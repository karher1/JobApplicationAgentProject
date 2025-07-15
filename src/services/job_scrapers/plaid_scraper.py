import time
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

class PlaidScraper(BaseJobScraper):
    """Scraper for Plaid's real careers page (https://plaid.com/careers/#search)"""
    def __init__(self):
        super().__init__()
        self.name = "PlaidScraper"

    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        jobs = []
        driver = None
        try:
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1280,720')
            driver = webdriver.Chrome(options=options)
            driver.get("https://plaid.com/careers/#search")
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/careers/openings/"]')))
            time.sleep(2)  # Let React render

            # Find all job cards (each card is a job)
            job_links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/careers/openings/"]')
            for link in job_links:
                try:
                    parent = link.find_element(By.XPATH, './ancestor::li[1]')
                    # The job title is the previous sibling div before the <a>
                    title = ""
                    location = ""
                    try:
                        # Get all direct children divs of the parent
                        divs = parent.find_elements(By.XPATH, './div')
                        # Usually: [location_div, title_div, ... , a]
                        if len(divs) >= 2:
                            location = divs[0].text.strip()
                            title = divs[1].text.strip()
                        else:
                            # Fallback: try previous siblings
                            title_elem = link.find_element(By.XPATH, 'preceding-sibling::div[1]')
                            title = title_elem.text.strip()
                            location_elem = title_elem.find_element(By.XPATH, 'preceding-sibling::div[1]')
                            location = location_elem.text.strip()
                    except Exception as e:
                        self.logger.debug(f"Error extracting title/location: {e}")
                    job_url = "https://plaid.com" + link.get_attribute('href')
                    # Filtering by job_titles if provided
                    if request.job_titles:
                        if not any(t.lower() in title.lower() for t in request.job_titles):
                            continue
                    jobs.append(JobPosition(
                        title=title,
                        company="Plaid",
                        location=location,
                        url=job_url,
                        job_board="Plaid",
                        description_snippet=None,
                        posted_date=None,
                        salary_range=None,
                        job_type=None,
                        remote_option="Remote" if "remote" in location.lower() else "On-site"
                    ))
                    if len(jobs) >= request.max_results:
                        break
                except Exception as e:
                    self.logger.debug(f"Error parsing job card: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error scraping Plaid jobs: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return jobs

    def can_handle_url(self, url: str) -> bool:
        return "plaid.com/careers" in url 