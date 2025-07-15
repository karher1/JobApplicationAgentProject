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

class RobinhoodScraper(BaseJobScraper):
    """Scraper for Robinhood's custom careers site (https://careers.robinhood.com/)"""
    def __init__(self):
        super().__init__()
        self.name = "Robinhood"
        self.logger = logging.getLogger("scraper.Robinhood")

    def can_handle_url(self, url: str) -> bool:
        return "careers.robinhood.com" in url

    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        jobs = []
        driver = None
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(30)
            self.logger.info(f"Loading Robinhood careers page: {url}")
            driver.get(url)
            # Scroll to the section with categories
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)  # Wait for categories to load
            wait = WebDriverWait(driver, 20)
            # Find all category accordions
            category_buttons = driver.find_elements(By.CSS_SELECTOR, "div.accordion")
            self.logger.debug(f"Found {len(category_buttons)} category accordions.")
            for btn in category_buttons:
                try:
                    btn.click()
                    time.sleep(1)  # Wait for jobs to expand
                    # Find the next sibling panel
                    panel = btn.find_element(By.XPATH, "following-sibling::div[contains(@class, 'panel')]")
                    job_elements = panel.find_elements(By.CSS_SELECTOR, "p.job")
                    self.logger.debug(f"Found {len(job_elements)} p.job elements in category.")
                    for job_elem in job_elements:
                        try:
                            link_elem = job_elem.find_element(By.TAG_NAME, "a")
                            title = link_elem.text.strip()
                            job_url = link_elem.get_attribute("href")
                            location = job_elem.get_attribute("data-location") or "Unknown"
                            self.logger.debug(f"Job title: {title}, location: {location}, url: {job_url}")
                            job_position = JobPosition(
                                title=title,
                                company="Robinhood",
                                location=location,
                                url=job_url,
                                job_board="Robinhood",
                                description_snippet=None,
                                posted_date=None,
                                salary_range=None,
                                job_type=None,
                                remote_option="Remote" if "remote" in location.lower() else "On-site"
                            )
                            
                            # Filter jobs based on search criteria
                            if self.matches_search_criteria(job_position, request):
                                jobs.append(job_position)
                            else:
                                self.logger.debug(f"Filtered out job: {title}")
                        except Exception as e:
                            self.logger.debug(f"Error parsing job element: {e}")
                            continue
                except Exception as e:
                    self.logger.debug(f"Error expanding or extracting jobs: {e}")
                    continue
            self.logger.info(f"[RobinhoodScraper] Found {len(jobs)} jobs.")
        except Exception as e:
            self.logger.error(f"Error scraping Robinhood jobs: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return jobs 