import logging
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

class FigmaScraper(BaseJobScraper):
    """Scraper for Figma's custom careers page (not Ashby)"""
    def __init__(self):
        super().__init__()
        self.name = "Figma"
        self.logger = logging.getLogger("scraper.Figma")

    def can_handle_url(self, url: str) -> bool:
        return "figma.com/careers" in url

    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        jobs = []
        driver = None
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(20)
            driver.get(url)
            wait = WebDriverWait(driver, 15)
            # Wait for job-openings section
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section#job-openings')))
            except TimeoutException:
                self.logger.warning("Timeout waiting for Figma job openings to load.")
                return jobs
            section = driver.find_element(By.CSS_SELECTOR, 'section#job-openings')
            dept_divs = section.find_elements(By.CSS_SELECTOR, 'div.css-2qv4k')
            for dept_div in dept_divs:
                try:
                    dept = dept_div.find_element(By.CSS_SELECTOR, 'h2').text.strip()
                except Exception:
                    dept = "Unknown"
                # Find all job links in this department
                try:
                    job_links = dept_div.find_elements(By.CSS_SELECTOR, 'ul.css-kgs24z li a')
                except Exception:
                    job_links = []
                for a in job_links:
                    try:
                        title = a.text.strip()
                        job_url = a.get_attribute('href')
                        if not title or not job_url:
                            continue
                        job = JobPosition(
                            title=title,
                            company="Figma",
                            location="N/A",
                            url=job_url,
                            job_board="Figma",
                            description_snippet=f"{dept} at Figma. See job page for details.",
                            posted_date=None,
                            salary_range=None,
                            job_type=None,
                            remote_option=None
                        )
                        jobs.append(job)
                    except Exception as e:
                        self.logger.debug(f"Error parsing Figma job link: {e}")
                        continue
            self.logger.info(f"[FigmaScraper] Found {len(jobs)} jobs.")
        except Exception as e:
            self.logger.error(f"Error scraping Figma jobs: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return jobs 