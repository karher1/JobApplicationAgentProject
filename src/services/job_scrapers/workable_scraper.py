import logging
import time
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest
from urllib.parse import urlparse

class WorkableScraper(BaseJobScraper):
    """Scraper for Workable-hosted job boards (e.g., Hugging Face)"""
    def __init__(self):
        super().__init__()
        self.name = "Workable"
        self.logger = logging.getLogger("scraper.Workable")

    def can_handle_url(self, url: str) -> bool:
        return "workable.com" in url

    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        jobs = []
        driver = None
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(30)
            self.logger.info(f"Loading Workable jobs page: {url}")
            driver.get(url)
            wait = WebDriverWait(driver, 20)
            # Wait for job list items to load
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[role='listitem']")))
            time.sleep(3)  # Let jobs fully render
            job_items = driver.find_elements(By.CSS_SELECTOR, "li[role='listitem']")
            self.logger.info(f"Found {len(job_items)} job items.")
            for item in job_items:
                try:
                    # Find the job link
                    link = item.find_element(By.CSS_SELECTOR, "a[href]")
                    href = link.get_attribute("href")
                    # Title from aria-labelledby or h2/h3
                    aria_labelledby = link.get_attribute("aria-labelledby")
                    title = None
                    if aria_labelledby:
                        try:
                            title_elem = item.find_element(By.ID, aria_labelledby)
                            title = title_elem.text.strip()
                        except Exception:
                            title = None
                    if not title:
                        # Try to find h2/h3 inside the item
                        try:
                            title_elem = item.find_element(By.CSS_SELECTOR, "h2, h3")
                            title = title_elem.text.strip()
                        except Exception:
                            title = "Unknown"
                    # Location
                    try:
                        location_elem = item.find_element(By.CSS_SELECTOR, "div[class*='job-location']")
                        location = location_elem.text.strip()
                    except Exception:
                        location = "Remote"
                    # Department
                    try:
                        dept_elem = item.find_element(By.CSS_SELECTOR, "span[data-ui='job-department']")
                        department = dept_elem.text.strip()
                    except Exception:
                        department = None
                    # Filtering by job_titles if provided
                    if request.job_titles:
                        if not any(t.lower() in title.lower() for t in request.job_titles):
                            continue
                    # Filtering by locations if provided
                    if request.locations:
                        if not any(loc.lower() in location.lower() for loc in request.locations):
                            continue
                    # Company name from URL
                    parsed = urlparse(url)
                    company = parsed.path.strip('/').split('/')[0].capitalize() if parsed.path else "Workable"
                    jobs.append(JobPosition(
                        title=title,
                        company=company,
                        location=location,
                        url=href if href.startswith("http") else f"https://{parsed.netloc}{href}",
                        job_board="Workable",
                        description_snippet=f"Department: {department}" if department else None,
                        posted_date=None,
                        salary_range=None,
                        job_type=None,
                        remote_option="Remote" if "remote" in location.lower() else "On-site"
                    ))
                    if len(jobs) >= request.max_results:
                        break
                except Exception as e:
                    self.logger.debug(f"Error parsing job item: {e}")
                    continue
            self.logger.info(f"[WorkableScraper] Found {len(jobs)} jobs.")
        except Exception as e:
            self.logger.error(f"Error scraping Workable jobs: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return jobs 