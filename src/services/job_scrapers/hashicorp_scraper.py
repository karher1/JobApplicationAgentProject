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

class HashiCorpScraper(BaseJobScraper):
    """Scraper for HashiCorp's custom careers page (not Ashby)"""
    def __init__(self):
        super().__init__()
        self.name = "HashiCorp"
        self.logger = logging.getLogger("scraper.HashiCorp")

    def can_handle_url(self, url: str) -> bool:
        return "hashicorp.com/careers" in url

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
            self.logger.info(f"Loading HashiCorp careers page: {url}")
            driver.get(url)
            wait = WebDriverWait(driver, 20)
            # Wait for job list to load
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-object-id]")))
            time.sleep(8)  # Let jobs fully render (increased wait)
            job_items = driver.find_elements(By.CSS_SELECTOR, "li[data-object-id]")
            for item in job_items:
                try:
                    link = item.find_element(By.CSS_SELECTOR, "a[class^='style_link']")
                    aria_label = link.get_attribute("aria-label") or ""
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    parts = [p.strip() for p in aria_label.split(",")]
                    title = parts[0] if parts else "Unknown"
                    location = ", ".join(parts[1:]).strip() if len(parts) > 1 else "Remote"
                    if request.job_titles:
                        if not any(t.lower() in title.lower() for t in request.job_titles):
                            continue
                    if request.locations:
                        if not any(loc.lower() in location.lower() for loc in request.locations):
                            continue
                    job_url = href if href.startswith("http") else f"https://www.hashicorp.com{href}"
                    jobs.append(JobPosition(
                        title=title,
                        company="HashiCorp",
                        location=location,
                        url=job_url,
                        job_board="HashiCorp",
                        description_snippet=f"See job page for details.",
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
            self.logger.info(f"[HashiCorpScraper] Found {len(jobs)} jobs.")
        except Exception as e:
            self.logger.error(f"Error scraping HashiCorp jobs: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return jobs 