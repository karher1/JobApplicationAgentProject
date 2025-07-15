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

class StripeScraper(BaseJobScraper):
    """Scraper for Stripe's real jobs page (https://stripe.com/jobs/search)"""
    def __init__(self):
        super().__init__()
        self.name = "StripeScraper"

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
            driver.get("https://stripe.com/jobs/search")
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)  # Let React render

            # If a job title is provided, enter it in the search box
            if request.job_titles and len(request.job_titles) > 0:
                search_term = request.job_titles[0]
                try:
                    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="jobsQueryInput"]')))
                    search_input.clear()
                    search_input.send_keys(search_term)
                    print(f"[StripeScraper DEBUG] Entered search term: {search_term}")
                    time.sleep(2)  # Wait for results to update
                except Exception as e:
                    print(f"[StripeScraper DEBUG] Could not use search box: {e}")
            else:
                print("[StripeScraper DEBUG] No job_titles provided, scraping all jobs on first page.")

            # Find all job rows (each row is a job)
            job_rows = driver.find_elements(By.CSS_SELECTOR, 'tr.TableRow')
            print(f"[StripeScraper DEBUG] Found {len(job_rows)} tr.TableRow elements.")
            if len(job_rows) == 0:
                print("[StripeScraper DEBUG] No job rows found. Dumping page source snippet:")
                print(driver.page_source[:2000])
            # Debug: print the text content of the first 5 rows
            for i, row in enumerate(job_rows[:5]):
                try:
                    print(f"[StripeScraper DEBUG] TableRow {i} text: {row.text}")
                except Exception as e:
                    print(f"[StripeScraper DEBUG] Error printing TableRow {i}: {e}")

            for row in job_rows:
                try:
                    # Try the more flexible selector first
                    try:
                        title_elem = row.find_element(By.CSS_SELECTOR, 'td.JobsListings__tableCell--title a')
                        print("[StripeScraper DEBUG] Used selector: td.JobsListings__tableCell--title a")
                    except Exception:
                        # Fallback: just the first <a> in the row
                        title_elem = row.find_element(By.TAG_NAME, 'a')
                        print("[StripeScraper DEBUG] Used fallback selector: first <a> in row")
                    title = title_elem.text.strip()
                    job_url = title_elem.get_attribute('href')
                    dept_elem = row.find_element(By.CSS_SELECTOR, 'td.JobsListings__tableCell--departments')
                    department = dept_elem.text.strip()
                    loc_elem = row.find_element(By.CSS_SELECTOR, 'td.JobsListings__tableCell--country')
                    location = loc_elem.text.strip()
                    # Filtering by job_titles if provided
                    if request.job_titles:
                        if not any(t.lower() in title.lower() for t in request.job_titles):
                            continue
                    jobs.append(JobPosition(
                        title=title,
                        company="Stripe",
                        location=location,
                        url=job_url,
                        job_board="Stripe",
                        description_snippet=f"Department: {department}",
                        posted_date=None,
                        salary_range=None,
                        job_type=None,
                        remote_option="Remote" if "remote" in location.lower() else "On-site"
                    ))
                    if len(jobs) >= request.max_results:
                        break
                except Exception as e:
                    print(f"[StripeScraper DEBUG] Error parsing job row: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error scraping Stripe jobs: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return jobs

    def can_handle_url(self, url: str) -> bool:
        return "stripe.com/jobs/search" in url 