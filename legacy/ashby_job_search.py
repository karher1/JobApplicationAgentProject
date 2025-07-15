#!/usr/bin/env python3
"""
Ashby Job Search Agent

Specialized agent for searching QA engineer positions on Ashby job boards.
Focuses on QA Engineer, Senior QA Engineer, QA Automation Engineer positions.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AshbyJobSearchAgent:
    """Specialized agent for searching Ashby job boards"""
    
    def __init__(self):
        self.base_url = "https://jobs.ashbyhq.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        
        # QA-focused job titles
        self.qa_job_titles = [
            "QA Engineer",
            "Senior QA Engineer", 
            "QA Automation Engineer",
            "Software Engineer in Test",
            "SDET",
            "Test Engineer",
            "Quality Assurance Engineer",
            "Automation Engineer",
            "Test Automation Engineer"
        ]
        
        # Keywords to look for in job descriptions
        self.qa_keywords = [
            "testing", "automation", "selenium", "cypress", "pytest", "junit",
            "test cases", "quality assurance", "qa", "sdet", "test automation",
            "manual testing", "api testing", "ui testing", "regression testing"
        ]
        
        # Companies known to use Ashby (we'll discover more)
        self.known_ashby_companies = [
            "notion",
            "linear", 
            "vercel",
            "stripe",
            "figma",
            "discord",
            "robinhood",
            "coinbase",
            "airtable",
            "calendly",
            "lattice",
            "retool",
            "amplitude",
            "segment",
            "mixpanel"
        ]
    
    def search_qa_jobs(self, job_titles: List[str] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for QA jobs across Ashby job boards"""
        if job_titles is None:
            job_titles = self.qa_job_titles
        
        logger.info(f"Starting Ashby job search for titles: {job_titles}")
        
        all_jobs = []
        
        # Search known companies
        for company in self.known_ashby_companies:
            try:
                company_jobs = self._search_company_jobs(company, job_titles, max_results)
                all_jobs.extend(company_jobs)
                logger.info(f"Found {len(company_jobs)} jobs at {company}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching {company}: {e}")
                continue
        
        # Remove duplicates based on URL
        unique_jobs = []
        seen_urls = set()
        for job in all_jobs:
            if job['url'] not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job['url'])
        
        logger.info(f"Total unique QA jobs found: {len(unique_jobs)}")
        return unique_jobs[:max_results]
    
    def _search_company_jobs(self, company: str, job_titles: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Search for jobs at a specific company"""
        company_url = f"{self.base_url}/{company}"
        
        try:
            # Use Selenium for dynamic content
            jobs = self._scrape_company_with_selenium(company_url, job_titles, max_results)
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping {company}: {e}")
            return []
    
    def _scrape_company_with_selenium(self, company_url: str, job_titles: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Scrape company jobs using Selenium for dynamic content"""
        jobs = []
        
        # Configure Chrome options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 30)
            
            # Navigate to company page
            driver.get(company_url)
            time.sleep(3)
            
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Look for job listings
            job_elements = self._find_job_elements(driver)
            
            for element in job_elements:
                try:
                    job_data = self._extract_job_data(driver, element, company_url)
                    
                    if job_data and self._is_qa_job(job_data, job_titles):
                        jobs.append(job_data)
                        
                        if len(jobs) >= max_results:
                            break
                            
                except Exception as e:
                    logger.warning(f"Error extracting job data: {e}")
                    continue
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Error with Selenium scraping: {e}")
            if 'driver' in locals():
                driver.quit()
        
        return jobs
    
    def _find_job_elements(self, driver) -> List:
        """Find job listing elements on the page"""
        job_elements = []
        
        # Common selectors for Ashby job listings
        selectors = [
            "a[href*='/jobs/']",
            "[data-testid*='job']",
            ".job-listing",
            ".job-card",
            "[class*='job']",
            "a[href*='careers']"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    job_elements.extend(elements)
                    logger.debug(f"Found {len(elements)} job elements with selector: {selector}")
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # Remove duplicates
        unique_elements = []
        seen_urls = set()
        for element in job_elements:
            try:
                url = element.get_attribute('href')
                if url and url not in seen_urls:
                    unique_elements.append(element)
                    seen_urls.add(url)
            except:
                continue
        
        return unique_elements
    
    def _extract_job_data(self, driver, element, company_url: str) -> Optional[Dict[str, Any]]:
        """Extract job data from an element"""
        try:
            # Get job URL
            job_url = element.get_attribute('href')
            if not job_url:
                return None
            
            # Make URL absolute if needed
            if job_url.startswith('/'):
                job_url = urljoin(company_url, job_url)
            
            # Extract company name from URL
            company = self._extract_company_from_url(job_url)
            
            # Get job title
            job_title = element.text.strip()
            if not job_title:
                # Try to find title in child elements
                title_elements = element.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, [class*='title']")
                if title_elements:
                    job_title = title_elements[0].text.strip()
            
            # Get additional details if available
            location = self._extract_location(element)
            job_type = self._extract_job_type(element)
            remote_option = self._extract_remote_option(element)
            
            return {
                'title': job_title,
                'company': company,
                'location': location or 'Remote',
                'url': job_url,
                'job_board': 'Ashby',
                'job_type': job_type,
                'remote_option': remote_option,
                'posted_date': None,  # Ashby doesn't always show this
                'salary_range': None,  # Ashby doesn't always show this
                'description_snippet': None  # Will be filled later if needed
            }
            
        except Exception as e:
            logger.warning(f"Error extracting job data: {e}")
            return None
    
    def _is_qa_job(self, job_data: Dict[str, Any], job_titles: List[str]) -> bool:
        """Check if a job is a QA position"""
        title = job_data.get('title', '').lower()
        
        # Check if title matches QA job titles
        for qa_title in job_titles:
            if qa_title.lower() in title:
                return True
        
        # Check for QA keywords in title
        for keyword in self.qa_keywords:
            if keyword.lower() in title:
                return True
        
        return False
    
    def _extract_company_from_url(self, url: str) -> str:
        """Extract company name from Ashby URL"""
        try:
            # URL pattern: https://jobs.ashbyhq.com/company-name/jobs/job-id
            path_parts = urlparse(url).path.split('/')
            if len(path_parts) > 1:
                company = path_parts[1]
                return company.replace('-', ' ').title()
        except:
            pass
        return "Unknown Company"
    
    def _extract_location(self, element) -> Optional[str]:
        """Extract location from job element"""
        try:
            # Look for location indicators
            location_selectors = [
                "[class*='location']",
                "[class*='place']",
                "[data-testid*='location']",
                "span:contains('Remote')",
                "span:contains('San Francisco')",
                "span:contains('New York')"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if location_elem:
                        return location_elem.text.strip()
                except:
                    continue
            
            # Check element text for location keywords
            element_text = element.text.lower()
            location_keywords = ['remote', 'san francisco', 'new york', 'austin', 'seattle', 'boston']
            
            for keyword in location_keywords:
                if keyword in element_text:
                    return keyword.title()
                    
        except Exception as e:
            logger.debug(f"Error extracting location: {e}")
        
        return None
    
    def _extract_job_type(self, element) -> Optional[str]:
        """Extract job type from element"""
        try:
            element_text = element.text.lower()
            
            if 'full-time' in element_text:
                return 'Full-time'
            elif 'part-time' in element_text:
                return 'Part-time'
            elif 'contract' in element_text:
                return 'Contract'
            elif 'internship' in element_text:
                return 'Internship'
                
        except Exception as e:
            logger.debug(f"Error extracting job type: {e}")
        
        return None
    
    def _extract_remote_option(self, element) -> Optional[str]:
        """Extract remote option from element"""
        try:
            element_text = element.text.lower()
            
            if 'remote' in element_text:
                return 'Remote'
            elif 'hybrid' in element_text:
                return 'Hybrid'
            elif 'on-site' in element_text or 'onsite' in element_text:
                return 'On-site'
                
        except Exception as e:
            logger.debug(f"Error extracting remote option: {e}")
        except:
            pass
        return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific job"""
        try:
            # Use Selenium to get full job details
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 30)
            
            driver.get(job_url)
            time.sleep(3)
            
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Extract job details
            details = {
                'url': job_url,
                'title': self._get_job_title(driver),
                'company': self._get_company_name(driver),
                'location': self._get_job_location(driver),
                'description': self._get_job_description(driver),
                'requirements': self._get_job_requirements(driver),
                'benefits': self._get_job_benefits(driver),
                'salary': self._get_job_salary(driver),
                'job_type': self._get_job_type(driver),
                'remote_option': self._get_remote_option(driver)
            }
            
            driver.quit()
            return details
            
        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            if 'driver' in locals():
                driver.quit()
            return None
    
    def _get_job_title(self, driver) -> str:
        """Extract job title from job page"""
        try:
            selectors = ["h1", "[class*='title']", "[data-testid*='title']"]
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        return element.text.strip()
                except:
                    continue
        except:
            pass
        return "Unknown Title"
    
    def _get_company_name(self, driver) -> str:
        """Extract company name from job page"""
        try:
            selectors = ["[class*='company']", "[data-testid*='company']", ".company-name"]
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        return element.text.strip()
                except:
                    continue
        except:
            pass
        return "Unknown Company"
    
    def _get_job_location(self, driver) -> str:
        """Extract job location from job page"""
        try:
            selectors = ["[class*='location']", "[data-testid*='location']", ".location"]
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        return element.text.strip()
                except:
                    continue
        except:
            pass
        return "Remote"
    
    def _get_job_description(self, driver) -> str:
        """Extract job description from job page"""
        try:
            selectors = ["[class*='description']", "[data-testid*='description']", ".job-description", "main"]
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        return element.text.strip()
                except:
                    continue
        except:
            pass
        return ""
    
    def _get_job_requirements(self, driver) -> List[str]:
        """Extract job requirements from job page"""
        try:
            requirements = []
            selectors = ["[class*='requirement']", "[class*='qualification']", "ul li"]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Filter out short text
                            requirements.append(text)
                except:
                    continue
            
            return requirements[:10]  # Limit to first 10 requirements
            
        except Exception as e:
            logger.debug(f"Error extracting requirements: {e}")
            return []
    
    def _get_job_benefits(self, driver) -> List[str]:
        """Extract job benefits from job page"""
        try:
            benefits = []
            selectors = ["[class*='benefit']", "[class*='perk']", ".benefits li"]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 5:
                            benefits.append(text)
                except:
                    continue
            
            return benefits[:10]  # Limit to first 10 benefits
            
        except Exception as e:
            logger.debug(f"Error extracting benefits: {e}")
            return []
    
    def _get_job_salary(self, driver) -> str:
        """Extract job salary from job page"""
        try:
            selectors = ["[class*='salary']", "[class*='compensation']", ".salary"]
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        return element.text.strip()
                except:
                    continue
        except:
            pass
        return ""
    
    def _get_job_type(self, driver) -> str:
        """Extract job type from job page"""
        try:
            element_text = driver.page_source.lower()
            
            if 'full-time' in element_text:
                return 'Full-time'
            elif 'part-time' in element_text:
                return 'Part-time'
            elif 'contract' in element_text:
                return 'Contract'
            elif 'internship' in element_text:
                return 'Internship'
                
        except Exception as e:
            logger.debug(f"Error extracting job type: {e}")
        
        return "Full-time"
    
    def _get_remote_option(self, driver) -> str:
        """Extract remote option from job page"""
        try:
            element_text = driver.page_source.lower()
            
            if 'remote' in element_text:
                return 'Remote'
            elif 'hybrid' in element_text:
                return 'Hybrid'
            elif 'on-site' in element_text or 'onsite' in element_text:
                return 'On-site'
                
        except Exception as e:
            logger.debug(f"Error extracting remote option: {e}")
        
        return "Remote"

# Example usage
if __name__ == "__main__":
    agent = AshbyJobSearchAgent()
    
    # Search for QA jobs
    jobs = agent.search_qa_jobs(max_results=20)
    
    print(f"Found {len(jobs)} QA jobs on Ashby:")
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job['title']} at {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   URL: {job['url']}")
        print() 