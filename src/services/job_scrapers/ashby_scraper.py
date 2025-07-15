import asyncio
import time
import logging
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service import Service

from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

class AshbyScraper(BaseJobScraper):
    """Scraper for Ashby job boards (ashbyhq.com)"""
    
    def __init__(self, debug: bool = False):
        super().__init__()
        self.name = "Ashby"
        self.debug = debug
        # Known Ashby companies that are more likely to have QA positions
        self.qa_focused_companies = [
            "linear", "vercel", "stripe", "figma", "discord", 
            "robinhood", "coinbase", "airtable", "retool", "amplitude", 
            "segment", "mixpanel", "brex", "plaid", "deel", 
            "gitlab", "hashicorp", "anthropic", "openai", "scale", 
            "databricks", "snowflake", "confluent", "mongodb", "elastic",
            "wander", "notion", "loom", "webflow", "superhuman",
            "census", "ramp", "mercury", "lattice", "clipboard-health",
            "rippling", "benchling", "faire", "flexport", "anduril",
            "cruise", "waymo", "nuro", "relativity", "palantir"
        ]
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL"""
        return "ashbyhq.com" in url or "jobs.ashbyhq.com" in url
    
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from Ashby job boards"""
        jobs = []
        
        # If it's a specific company URL, scrape it directly
        if self._is_company_url(url):
            company_jobs = await self._scrape_company_page(url, request)
            jobs.extend(company_jobs)
        else:
            # If it's a general URL, try multiple companies
            jobs = await self._scrape_multiple_companies(request)
        
        return jobs
    
    def _is_company_url(self, url: str) -> bool:
        """Check if URL is for a specific company"""
        return any(company in url for company in self.qa_focused_companies)
    
    async def _scrape_multiple_companies(self, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from multiple Ashby companies - optimized for speed"""
        jobs = []
        
        # Try only the most likely companies first (3-4 max for speed)
        priority_companies = ["linear", "stripe", "figma", "notion"]
        
        for company in priority_companies:
            try:
                company_url = f"https://jobs.ashbyhq.com/{company}"
                company_jobs = await self._scrape_company_page(company_url, request)
                jobs.extend(company_jobs)
                
                if len(jobs) >= request.max_results:
                    self.logger.info(f"Found enough jobs ({len(jobs)}), stopping search")
                    break
                
                # Reduced rate limiting for speed
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error scraping {company}: {e}")
                continue
        
        return jobs
    
    async def _scrape_company_page(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from a specific company's Ashby page"""
        jobs = []
        driver = None
        
        try:
            driver = self._setup_driver()
            self.logger.info(f"Scraping Ashby URL: {url}")
            
            driver.get(url)
            
            # Wait for page to load with faster timeout
            wait = WebDriverWait(driver, 10)  # Reduced from 30 to 10 seconds
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except TimeoutException:
                self.logger.warning(f"Timeout waiting for page to load: {url}")
                return jobs
            
            # Check for iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                self.logger.info(f"Found {len(iframes)} iframes, switching to first iframe")
                try:
                    driver.switch_to.frame(iframes[0])
                    # Wait for iframe content to load
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                except Exception as e:
                    self.logger.warning(f"Could not switch to iframe: {e}")
            
            # Scroll to load lazy-loaded content
            self._scroll_to_load_content(driver, wait)
            
            # Find job elements
            job_elements = self._find_job_elements(driver, wait)
            
            if not job_elements:
                self.logger.warning(f"No job elements found for {url}")
                return jobs
            
            # DEBUG: Print all raw job titles found before filtering
            if self.debug:
                raw_titles = []
                for element in job_elements:
                    try:
                        if hasattr(element, 'tag_name') and element.tag_name == "a":
                            raw_text = element.text.strip()
                            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                            if lines:
                                raw_titles.append(lines[0])
                        elif hasattr(element, 'tag_name') and element.tag_name == "div":
                            raw_text = element.text.strip()
                            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                            if lines:
                                raw_titles.append(lines[0])
                        else:
                            raw_text = element.text.strip()
                            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                            if lines:
                                raw_titles.append(lines[0])
                    except Exception as e:
                        continue
                print("\n[DEBUG] Raw job titles found on page:")
                for t in raw_titles:
                    print(f" - {t}")
                print()
            # Log what types of jobs we found for debugging
            job_titles_found = []
            
            # Extract job data
            for element in job_elements[:20]:  # Limit per company
                try:
                    job_data = self._extract_job_data(driver, element, url, wait)
                    if job_data:
                        job_titles_found.append(job_data.title)
                        if self.matches_search_criteria(job_data, request):
                            jobs.append(job_data)
                            self.logger.info(f"Found matching job: {job_data.title}")
                        
                except Exception as e:
                    self.logger.debug(f"Error extracting job data: {e}")
                    continue
            
            # Log what we found for debugging
            if job_titles_found:
                self.logger.info(f"Found {len(job_titles_found)} jobs at {url}: {job_titles_found[:5]}...")
            
            # If no QA/SDET jobs found, log a warning
            qa_keywords = ['qa', 'test', 'sdet', 'quality', 'automation']
            qa_jobs = [title for title in job_titles_found if any(keyword in title.lower() for keyword in qa_keywords)]
            if not qa_jobs and any(keyword in ' '.join(request.job_titles).lower() for keyword in qa_keywords):
                self.logger.warning(f"No QA/SDET jobs found at {url}. Consider adding fallback companies.")
            
            # Switch back to default content if we were in an iframe
            if iframes:
                try:
                    driver.switch_to.default_content()
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error scraping Ashby page {url}: {e}")
        
        finally:
            # Always quit the driver to prevent resource leaks
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.debug(f"Error quitting driver: {e}")
        
        return jobs
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with appropriate options - optimized for speed"""
        chromedriver_path = "/Users/karenherrera/.wdm/drivers/chromedriver/mac64/138.0.7204.92/chromedriver-mac-arm64/chromedriver"
        options = Options()
        
        # Optimize for speed - disable unnecessary features
        options.add_argument("--headless=new")  # Modern headless mode for Chrome 109+
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Speed up by not loading images
        options.add_argument("--window-size=1280,720")  # Smaller window for speed
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        options.add_experimental_option("detach", False)
        
        # Additional speed optimizations
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-web-security")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-first-run")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--enable-automation")
        options.add_argument("--password-store=basic")
        options.add_argument("--use-mock-keychain")
        
        service = Service(chromedriver_path)
        return webdriver.Chrome(service=service, options=options)
    
    def _scroll_to_load_content(self, driver: webdriver.Chrome, wait: WebDriverWait):
        """Scroll to load lazy-loaded content using WebDriverWait instead of time.sleep"""
        self.logger.info("Scrolling to load all jobs...")
        for scroll_attempt in range(3):
            try:
                # Scroll to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Wait for content to load instead of sleeping
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Scroll back to top
                driver.execute_script("window.scrollTo(0, 0);")
                # Brief wait for scroll to complete
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
            except Exception as e:
                self.logger.debug(f"Scroll attempt {scroll_attempt + 1} failed: {e}")
    
    def _find_job_elements(self, driver: webdriver.Chrome, wait: WebDriverWait) -> List:
        """Find job elements on the page using current Ashby DOM structure"""
        # Updated selectors based on current Ashby structure (2024)
        job_selectors = [
            "a[href*='jobs.ashbyhq.com']",           # Direct Ashby job links
            "a[href*='/linear/']",                   # Linear-specific job links
            "div[role='button']",                    # Clickable job containers
            "a[role='link']",                        # Link elements with role
            "[data-qa='job-link']",                  # Data attribute job links
            "a:has(h3)",                             # Links containing h3 headers
            "a:has(h4)",                             # Links containing h4 headers
            "div:has(a[href*='ashbyhq.com'])",       # Containers with job links
            "a[href*='/jobs/']",                     # Generic job links
            "a"                                      # Fallback: all links
        ]
        
        for selector in job_selectors:
            try:
                # Wait for elements to be present
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                self.logger.debug(f"Selector '{selector}' found {len(elements)} elements")
                
                if elements:
                    # Filter elements to ensure they're actual job postings
                    filtered_elements = []
                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            element_href = element.get_attribute('href') or ""
                            
                            # Skip empty elements
                            if not element_text and not element_href:
                                continue
                            
                            # Skip navigation and footer elements
                            skip_phrases = [
                                'home', 'about', 'contact', 'privacy', 'terms',
                                'login', 'sign up', 'company', 'culture', 'benefits',
                                'filter', 'search', 'sort', 'apply now', 'view all',
                                'powered by', 'opportunistic'
                            ]
                            
                            if any(skip in element_text.lower() for skip in skip_phrases):
                                continue
                            
                            # Must contain job-like content
                            job_indicators = [
                                'engineer', 'developer', 'manager', 'analyst', 'director',
                                'specialist', 'coordinator', 'lead', 'senior', 'junior',
                                'full time', 'part time', 'remote', 'onsite', 'hybrid',
                                'gtm', 'growth', 'marketing', 'sales', 'product'
                            ]
                            
                            # Check if element contains job-related terms OR has job URL
                            has_job_content = (
                                any(indicator in element_text.lower() for indicator in job_indicators) or
                                'ashbyhq.com' in element_href or
                                '/jobs/' in element_href
                            )
                            
                            if has_job_content and len(element_text) > 5:
                                filtered_elements.append(element)
                                
                        except Exception as e:
                            self.logger.debug(f"Error filtering element: {e}")
                            continue
                    
                    if filtered_elements:
                        self.logger.info(f"Found {len(filtered_elements)} job elements with selector: {selector}")
                        return filtered_elements
                        
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # Final fallback: get all text content and look for job patterns
        self.logger.warning("No job elements found with selectors, trying text-based approach")
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body_text = body.text
            
            # Look for job title patterns in the text
            job_patterns = [
                r'Account Executive.*',
                r'Software Engineer.*',
                r'Product Manager.*',
                r'Data Scientist.*',
                r'Marketing.*',
                r'Sales.*',
                r'Engineer.*',
                r'Manager.*',
                r'Director.*',
                r'Analyst.*'
            ]
            
            import re
            found_jobs = []
            for pattern in job_patterns:
                matches = re.findall(pattern, body_text, re.IGNORECASE)
                found_jobs.extend(matches)
            
            if found_jobs:
                self.logger.info(f"Found job titles in text: {found_jobs[:5]}")
                # Create mock elements for text-based matches
                mock_elements = []
                for job_title in found_jobs[:10]:  # Limit to 10
                    # This is a simplified approach - in a real implementation,
                    # you'd try to find the actual DOM elements for these titles
                    mock_elements.append(type('MockElement', (), {
                        'text': job_title,
                        'get_attribute': lambda x: None,
                        'tag_name': 'text'
                    })())
                return mock_elements
                
        except Exception as e:
            self.logger.debug(f"Text-based approach failed: {e}")
        
        return []
    
    def _debug_page_structure(self, driver: webdriver.Chrome):
        """Debug method to see what's actually on the page"""
        try:
            # Get all elements with class containing common job-related terms
            debug_selectors = [
                "[class*='job']",
                "[class*='posting']", 
                "[class*='container']",
                "[class*='ashby']",
                "a[href*='Linear']",
                "a[href*='jobs']"
            ]
            
            for selector in debug_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.debug(f"DEBUG: Found {len(elements)} elements with selector '{selector}'")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.text.strip()[:50]
                        href = elem.get_attribute('href')
                        classes = elem.get_attribute('class')
                        self.logger.debug(f"  [{i}] tag={elem.tag_name}, text='{text}', href='{href}', class='{classes}'")
                        
        except Exception as e:
            self.logger.debug(f"Debug page structure failed: {e}")
    
    def _extract_job_data(self, driver: webdriver.Chrome, element, url: str, wait: WebDriverWait) -> Optional[JobPosition]:
        """Extract job data from an element with improved logic for current Ashby structure"""
        try:
            job_url = None
            job_title = None
            
            # Handle text-based mock elements (from regex matching)
            if hasattr(element, 'tag_name') and element.tag_name == 'text':
                job_title = element.text.strip()
                job_url = url  # Use the main page URL as fallback
                company = self._extract_company_from_url(url)
                
                # Extract job description
                description_snippet = self._extract_job_description(driver, element, job_url)
                
                job_position = self.create_job_position(
                    title=job_title,
                    company=company,
                    location="Remote",
                    url=job_url,
                    description=description_snippet,
                    job_board="Ashby"
                )
                return job_position
            
            # Handle real DOM elements
            if element.tag_name == "a":
                # For <a> elements, get URL directly and extract title from content
                job_url = element.get_attribute("href")
                
                # Try to get job title from the link text
                raw_text = element.text.strip()
                
                # Clean up the text - take first meaningful line
                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                if lines:
                    job_title = lines[0]
                    
                    # If title is very short, try combining with second line
                    if len(job_title) < 10 and len(lines) > 1:
                        second_line = lines[1]
                        # Only combine if second line looks like part of job title
                        if not any(skip in second_line.lower() for skip in ['remote', 'full time', 'part time', '•']):
                            job_title = f"{job_title} {second_line}"
                
            elif element.tag_name == "div":
                # For div elements, look for job titles and URLs within
                raw_text = element.text.strip()
                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                
                if not lines:
                    return None
                
                # Look for the job title (usually the first substantial line)
                job_title = lines[0]
                
                # Try to find a link within the div
                try:
                    link_element = element.find_element(By.TAG_NAME, "a")
                    job_url = link_element.get_attribute("href")
                except:
                    # If no link found, construct URL from job title
                    job_url = self._construct_job_url_from_title(job_title, url)
                    
            else:
                # For other elements, use basic text extraction
                raw_text = element.text.strip()
                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                
                if not lines:
                    return None
                
                job_title = lines[0]
                job_url = self._find_job_url_in_element(element, url)
            
            # Clean the job title
            if job_title:
                job_title = self._clean_job_title(job_title)
            
            # Validate job title
            if not job_title or len(job_title) < 3:
                return None
            
            # Enhanced filtering for non-job content
            skip_terms = [
                "powered by", "privacy", "terms", "about", "contact", "login",
                "home", "careers", "jobs", "apply", "submit", "search", "filter",
                "opportunistic", "open positions", "filter open positions"
            ]
            
            if any(skip in job_title.lower() for skip in skip_terms):
                return None
            
            # Ensure we have a job URL
            if not job_url:
                job_url = self._construct_job_url_from_title(job_title, url)
            elif not job_url.startswith('http'):
                # Handle relative URLs
                if job_url.startswith('/'):
                    base_domain = '/'.join(url.split('/')[:3])
                    job_url = base_domain + job_url
                else:
                    job_url = url.rstrip('/') + '/' + job_url
            
            # Extract company from URL
            company = self._extract_company_from_url(url)
            
            # Extract location (try to find it in surrounding context)
            location = self._extract_location_from_element_context(element) or "Remote"
            
            # Extract job description
            description_snippet = self._extract_job_description(driver, element, job_url)
            
            # Create the job position
            job_position = self.create_job_position(
                title=job_title,
                company=company,
                location=location,
                url=job_url,
                description=description_snippet,
                job_board="Ashby"
            )
            
            self.logger.info(f"Successfully extracted job: {job_title} at {company}")
            return job_position
            
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {e}")
            return None
    
    def _extract_job_description(self, driver: webdriver.Chrome, element, job_url: str) -> str:
        """Extract job description snippet from job listing or job detail page"""
        try:
            # Method 1: Try to find description in the current element context
            description_text = self._extract_description_from_element(element)
            if description_text and len(description_text.strip()) > 10:
                self.logger.debug(f"Found description from element: {description_text[:50]}...")
                return description_text
            
            # Method 2: Create a meaningful description based on job title
            company = self._extract_company_from_url(job_url or "")
            
            # Get job title from element if possible
            job_title = ""
            try:
                if hasattr(element, 'text') and element.text:
                    lines = [line.strip() for line in element.text.split('\n') if line.strip()]
                    if lines:
                        job_title = lines[0]
            except:
                pass
            
            # Create a descriptive snippet based on job title and company
            if job_title:
                # Generate role-specific descriptions
                title_lower = job_title.lower()
                if 'data' in title_lower and 'engineer' in title_lower:
                    return f"Join {company} as a {job_title}. Work with large-scale data systems and analytics infrastructure. Apply your expertise in data engineering, pipeline development, and analytics."
                elif 'software engineer' in title_lower or 'software developer' in title_lower:
                    return f"Software engineering position at {company}. Build innovative products and scalable systems. Work with cutting-edge technology and collaborate with talented engineers."
                elif 'senior' in title_lower and 'engineer' in title_lower:
                    return f"Senior engineering role at {company}. Lead technical initiatives and mentor team members. Solve complex challenges and drive technical excellence."
                elif 'platform' in title_lower:
                    return f"Platform engineering role at {company}. Build and maintain core infrastructure systems. Focus on scalability, reliability, and developer experience."
                elif 'machine learning' in title_lower or 'ml' in title_lower or 'ai' in title_lower:
                    return f"Machine learning opportunity at {company}. Work on AI/ML systems and algorithms. Apply your expertise in model development and deployment."
                elif 'security' in title_lower:
                    return f"Security engineering position at {company}. Protect systems and data through innovative security solutions. Work on threat detection and prevention."
                elif 'devops' in title_lower or 'site reliability' in title_lower or 'sre' in title_lower:
                    return f"Infrastructure and reliability role at {company}. Ensure system scalability and operational excellence. Work with cloud platforms and automation."
                elif 'frontend' in title_lower or 'front-end' in title_lower or 'ui' in title_lower:
                    return f"Frontend engineering position at {company}. Build exceptional user interfaces and experiences. Work with modern frameworks and design systems."
                elif 'backend' in title_lower or 'back-end' in title_lower or 'api' in title_lower:
                    return f"Backend engineering role at {company}. Design and implement scalable server-side systems. Work on APIs, databases, and distributed systems."
                else:
                    return f"Engineering opportunity at {company} for {job_title}. Join a talented team working on innovative technology solutions."
            
            # Generic fallback
            return f"Exciting career opportunity at {company}. Join a dynamic team and work on cutting-edge technology projects. Click to view full details."
            
        except Exception as e:
            self.logger.debug(f"Error extracting job description: {e}")
            company = self._extract_company_from_url(job_url or "")
            return f"Career opportunity at {company}. Click to view full details."
    
    def _extract_description_from_element(self, element) -> Optional[str]:
        """Extract description text from the job listing element"""
        try:
            # Look for description text in the element or its children
            all_text = element.text.strip()
            if not all_text:
                return None
            
            # Split by lines and look for description-like content
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Skip the title line and look for description content
            for i, line in enumerate(lines[1:], 1):  # Skip first line (title)
                # Look for description indicators
                if (len(line) > 30 and 
                    not any(skip in line.lower() for skip in ['remote', 'full time', 'apply', '•', '$', 'salary']) and
                    any(word in line.lower() for word in ['we', 'you', 'the', 'responsible', 'will', 'experience', 'team', 'work', 'develop', 'build'])):
                    
                    # Found a description-like line, return it (truncated)
                    return line[:200] + "..." if len(line) > 200 else line
            
            # If no clear description found, return a meaningful snippet
            if len(lines) > 1:
                # Look for longer lines that might be descriptions
                longer_lines = [line for line in lines[1:] if len(line) > 20]
                if longer_lines:
                    desc = longer_lines[0]
                    return desc[:200] + "..." if len(desc) > 200 else desc
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extracting description from element: {e}")
            return None
    
    def _fetch_description_from_job_page(self, job_url: str) -> Optional[str]:
        """Fetch job description from individual job detail page using Selenium (since Ashby uses dynamic content)"""
        driver = None
        try:
            driver = self._setup_driver()
            driver.set_page_load_timeout(15)
            driver.get(job_url)

            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            wait = WebDriverWait(driver, 15)

            # 1. Try to extract from div.prose (main description block)
            try:
                prose_elem = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.prose'))
                )
                text = prose_elem.text.strip()
                if len(text) > 50:
                    self.logger.debug(f"[Ashby] Extracted from div.prose: {text[:80]}...")
                    sentences = text.split('.')
                    snippet = '. '.join(sentences[:3]).strip()
                    if len(snippet) > 400:
                        snippet = snippet[:400] + '...'
                    if not snippet.endswith('.'):
                        snippet += '.'
                    return snippet
            except Exception as e:
                self.logger.debug(f"[Ashby] Could not find div.prose: {e}")

            # 2. Try the main job description block as before
            try:
                desc_elem = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="job-description"]'))
                )
                text = desc_elem.text.strip()
                if len(text) > 50:
                    self.logger.debug(f"[Ashby] Extracted main job description block: {text[:80]}...")
                    sentences = text.split('.')
                    snippet = '. '.join(sentences[:3]).strip()
                    if len(snippet) > 400:
                        snippet = snippet[:400] + '...'
                    if not snippet.endswith('.'):
                        snippet += '.'
                    return snippet
            except Exception as e:
                self.logger.debug(f"[Ashby] Could not find main job description block: {e}")

            # 3. Fallback: Try other selectors as before
            description_selectors = [
                '.job-description', 
                '[data-testid="description"]',
                'div[class*="description"]',
                'div[class*="content"]',
                '.content',
                'article',
                'main',
                'div p',
                'p'
            ]
            for selector in description_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if len(text) > 50:
                            sentences = text.split('.')
                            snippet = '. '.join(sentences[:3]).strip()
                            if len(snippet) > 400:
                                snippet = snippet[:400] + '...'
                            if not snippet.endswith('.'):
                                snippet += '.'
                            self.logger.debug(f"[Ashby] Fallback selector {selector} found: {snippet[:80]}...")
                            return snippet
                except Exception as e:
                    continue
            # 4. Fallback: Any substantial text content
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                paragraphs = [p.strip() for p in body_text.split('\n') if len(p.strip()) > 50]
                for paragraph in paragraphs:
                    if any(word in paragraph.lower() for word in ['we', 'you', 'the', 'responsible', 'experience', 'team', 'will', 'role', 'position']):
                        snippet = paragraph[:400] + '...' if len(paragraph) > 400 else paragraph
                        self.logger.debug(f"[Ashby] Fallback body text: {snippet[:80]}...")
                        return snippet
            except Exception as e:
                pass
            return None
        except Exception as e:
            self.logger.debug(f"Error fetching description from job page {job_url}: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _clean_job_title(self, title: str) -> str:
        """Clean job title by removing metadata and formatting"""
        title = title.strip()
        
        # Remove common noisy phrases that indicate non-job content
        bad_phrases = [
            'powered by', 'opportunistic', 'join us', 'we\'re hiring', 'explore openings',
            'vulnerability disclosure', 'privacy policy', 'terms of service', 'cookie policy',
            'about us', 'contact us', 'legal', 'copyright', 'all rights reserved'
        ]
        
        for bad in bad_phrases:
            if bad.lower() in title.lower():
                return ''  # Return empty string to indicate invalid title
        
        # Strip company, location metadata
        if '\n' in title:
            title = title.split('\n')[0]
        if '•' in title:
            title = title.split('•')[0]
        
        # Remove any trailing weird characters
        title = title.strip("•-:").strip()
        
        # Normalize whitespace
        title = ' '.join(title.split())
        
        # Final validation - must be a reasonable job title
        if not title or len(title) < 5 or len(title) > 100:
            return ''
        
        # Check if it looks like a real job title (starts with letter, reasonable length)
        import re
        if not re.match(r'^[A-Za-z].{3,100}$', title):
            return ''
        
        return title
    
    def _find_job_url_for_title_element(self, title_element, base_url: str) -> Optional[str]:
        """Find job URL for an h1 title element by looking at parent containers"""
        try:
            # Method 1: Look for parent link
            try:
                parent_link = title_element.find_element(By.XPATH, "./ancestor::a")
                href = parent_link.get_attribute("href")
                if href:
                    return href
            except:
                pass
            
            # Method 2: Look for nearby links in the same container
            try:
                container = title_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'container')]")
                links = container.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and ('/jobs/' in href or 'ashbyhq.com' in href):
                        return href
            except:
                pass
            
            # Method 3: Look for data attributes on the title or parent
            for element in [title_element, title_element.find_element(By.XPATH, "..")]:
                try:
                    for attr in ["data-href", "data-url", "data-job-url"]:
                        href = element.get_attribute(attr)
                        if href:
                            return href
                except:
                    continue
            
        except Exception as e:
            self.logger.debug(f"Error finding URL for title element: {e}")
        
        return None
    
    def _construct_job_url_from_title(self, job_title: str, base_url: str) -> str:
        """Construct a job URL from the job title"""
        # Create a URL-friendly slug from the job title
        slug = job_title.lower()
        slug = slug.replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c in '-_')
        slug = slug[:50]  # Limit length
        
        return f"{base_url}/jobs/{slug}"
    
    def _extract_location_from_element_context(self, element) -> Optional[str]:
        """Extract location from element context (nearby elements, parent containers)"""
        try:
            # Method 1: Look in the same container
            container = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'container')]")
            container_text = container.text.lower()
            
            # Look for location keywords
            location_keywords = ['remote', 'san francisco', 'new york', 'london', 'berlin', 'toronto']
            for keyword in location_keywords:
                if keyword in container_text:
                    return keyword.title()
                    
            # Method 2: Look for specific location elements
            location_elements = container.find_elements(By.CSS_SELECTOR, "[class*='location'], [class*='Location']")
            if location_elements:
                return location_elements[0].text.strip()
                
        except Exception as e:
            self.logger.debug(f"Error extracting location from context: {e}")
        
        return None
    
    def _find_job_url_in_element(self, element, base_url: str) -> Optional[str]:
        """Find job URL within an element using improved DOM traversal"""
        try:
            # Method 1: Try to find <a> tag inside the div
            try:
                link_elem = element.find_element(By.TAG_NAME, "a")
                job_url = link_elem.get_attribute("href")
                if job_url:
                    self.logger.debug(f"Found URL inside element: {job_url}")
                    return job_url
            except NoSuchElementException:
                pass
            
            # Method 2: Walk up the DOM to find parent <a> tag
            try:
                parent_link = element.find_element(By.XPATH, "./ancestor::a")
                job_url = parent_link.get_attribute("href")
                if job_url:
                    self.logger.debug(f"Found URL in ancestor: {job_url}")
                    return job_url
            except NoSuchElementException:
                pass
            
            # Method 3: Look for data-href or onclick attributes
            for attr in ["data-href", "href"]:
                href = element.get_attribute(attr)
                if href and ('/jobs/' in href or 'ashbyhq.com' in href):
                    self.logger.debug(f"Found URL in {attr}: {href}")
                    return href
            
            # Method 4: Check for onclick with router navigation
            onclick = element.get_attribute("onclick")
            if onclick and 'job' in onclick.lower():
                # Extract URL from onclick if possible
                import re
                url_match = re.search(r'["\']([^"\']*jobs?[^"\']*)["\']', onclick)
                if url_match:
                    self.logger.debug(f"Found URL in onclick: {url_match.group(1)}")
                    return url_match.group(1)
            
            # Method 5: Try to get data attributes that might contain job IDs
            job_id = element.get_attribute("data-job-id") or element.get_attribute("data-id")
            if job_id:
                constructed_url = f"{base_url}/jobs/{job_id}"
                self.logger.debug(f"Constructed URL from job ID: {constructed_url}")
                return constructed_url
            
            # Method 6: Debug - log the HTML to see what we're working with
            self.logger.debug(f"Job element HTML:\n{element.get_attribute('outerHTML')[:500]}...")
            
            # Last resort: construct URL from job title
            title_text = element.text.strip().split('\n')[0]
            if title_text and len(title_text) > 5:
                job_slug = title_text.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')[:50]
                constructed_url = f"{base_url}/jobs/{job_slug}"
                self.logger.debug(f"Constructed URL from title: {constructed_url}")
                return constructed_url
                
        except Exception as e:
            self.logger.debug(f"Error finding job URL: {e}")
        
        return None
    
    def _extract_company_from_url(self, url: str) -> str:
        """Extract company name from URL"""
        try:
            # Extract from jobs.ashbyhq.com/company-name
            parts = url.split('/')
            if len(parts) > 3:
                company = parts[3].replace('-', ' ').title()
                return company
        except:
            pass
        return "Unknown Company" 