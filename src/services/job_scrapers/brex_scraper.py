import logging
from typing import List
from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import random

class BrexScraper(BaseJobScraper):
    """Playwright-based scraper for Brex's custom careers page"""
    def __init__(self):
        super().__init__()
        self.name = "Brex"
        self.logger = logging.getLogger("scraper.Brex")

    def can_handle_url(self, url: str) -> bool:
        return "brex.com/careers" in url

    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible for debugging
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_selector('section#jobsBoard', timeout=15000)
                # Human-like interaction: scroll, mouse move, random delay
                await page.mouse.move(100, 100)
                await asyncio.sleep(random.uniform(0.5, 1.2))
                await page.mouse.move(200, 300)
                await asyncio.sleep(random.uniform(0.5, 1.2))
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(random.uniform(0.5, 1.2))
                await page.evaluate("window.scrollBy(0, -200)")
                await asyncio.sleep(random.uniform(0.5, 1.2))
                # Check for anti-bot or CAPTCHA
                captcha = await page.query_selector('iframe[src*="captcha"], [id*="captcha"], [class*="captcha"]')
                if captcha:
                    print("[BrexScraper] CAPTCHA or anti-bot detected!")
                else:
                    print("[BrexScraper] No obvious CAPTCHA detected.")
                # Find all department buttons
                dept_buttons = await page.query_selector_all('section#jobsBoard button[id$="-heading"]')
                for btn in dept_buttons:
                    try:
                        dept = (await btn.inner_text()).strip()
                        btn_id = await btn.get_attribute('id')
                        # Click to expand
                        await btn.click()
                        content_id = btn_id.replace('-heading', '_content')
                        # Wait for job links with data-testid="rebirth-link" to appear
                        try:
                            await page.wait_for_selector(f'#{content_id} a[data-testid="rebirth-link"]', timeout=7000)
                        except PlaywrightTimeoutError:
                            self.logger.debug(f"[BrexScraper] No job links appeared in {dept} after expand.")
                        # Print the HTML of the content div for debugging
                        content_div = await page.query_selector(f'#{content_id}')
                        if content_div:
                            html = await content_div.inner_html()
                            print(f"\n[DEBUG] HTML for {dept} content div after expand (first 2000 chars):\n" + html[:2000])
                            # Print all <a> tags' outerHTML in the content div
                            all_a = await content_div.query_selector_all('a')
                            print(f"[DEBUG] Found {len(all_a)} <a> tags in {dept} content div.")
                            for i, a in enumerate(all_a):
                                outer = await a.evaluate('(el) => el.outerHTML')
                                print(f"[DEBUG] <a> tag {i+1}: {outer[:300]}")
                        # Extract jobs using the more specific selector
                        job_links = await page.query_selector_all(f'#{content_id} a[data-testid="rebirth-link"]')
                        self.logger.debug(f"[BrexScraper] Found {len(job_links)} jobs in {dept}.")
                        for a in job_links:
                            try:
                                # Extract job title
                                try:
                                    title_elem = await a.query_selector("div[class*='1jca5mn']")
                                    title = (await title_elem.inner_text()).strip() if title_elem else (await a.inner_text()).strip()
                                except Exception:
                                    title = (await a.inner_text()).strip()
                                # Extract location
                                try:
                                    loc_elem = await a.query_selector("p[class*='vv28yo']")
                                    location = (await loc_elem.inner_text()).strip() if loc_elem else "N/A"
                                except Exception:
                                    location = "N/A"
                                job_url = await a.get_attribute('href')
                                if job_url and job_url.startswith('/'):
                                    job_url = 'https://www.brex.com' + job_url
                                if not title or not job_url:
                                    continue
                                job = JobPosition(
                                    title=title,
                                    company="Brex",
                                    location=location,
                                    url=job_url,
                                    job_board="Brex",
                                    description_snippet=f"{dept} at Brex. See job page for details.",
                                    posted_date=None,
                                    salary_range=None,
                                    job_type=None,
                                    remote_option=None
                                )
                                jobs.append(job)
                                self.logger.debug(f"[BrexScraper] Found job: {title} | {location} | {job_url}")
                            except Exception as e:
                                self.logger.debug(f"Error parsing Brex job link: {e}")
                                continue
                    except Exception as e:
                        self.logger.debug(f"Error handling Brex department button: {e}")
                        continue
                self.logger.info(f"[BrexScraper] Found {len(jobs)} jobs.")
            except Exception as e:
                self.logger.error(f"Error scraping Brex jobs: {e}")
            finally:
                await browser.close()
        return jobs 