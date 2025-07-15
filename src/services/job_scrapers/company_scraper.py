import asyncio
import aiohttp
import logging
import os
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

from .base_scraper import BaseJobScraper
from .ashby_scraper import AshbyScraper
from .greenhouse_scraper import GreenhouseScraper
from .lever_scraper import LeverScraper
from .stripe_scraper import StripeScraper
from .plaid_scraper import PlaidScraper
from .figma_scraper import FigmaScraper
from .hashicorp_scraper import HashiCorpScraper
from .workable_scraper import WorkableScraper
from .robinhood_scraper import RobinhoodScraper
from .coinbase_scraper import CoinbaseScraper
from .github_scraper import GitHubScraper
from src.models.schemas import JobPosition, JobSearchRequest
from src.services.cache_service import CacheService

logger = logging.getLogger(__name__)
# Add file handler for CompanyScraper logs
log_file = os.path.join(os.path.dirname(__file__), '../../company_scraper.log')
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in logger.handlers):
    logger.addHandler(file_handler)

class CompanyScraper(BaseJobScraper):
    """Scraper for popular tech companies with known job board URLs - uses real scrapers with caching"""
    
    def __init__(self):
        super().__init__()
        self.name = "CompanyScraper"
        self.session = None
        self.cache_service = CacheService(cache_duration_hours=6)  # 6 hour cache
        
        # Initialize real scrapers
        self.ashby_scraper = AshbyScraper()
        self.greenhouse_scraper = GreenhouseScraper()
        self.lever_scraper = LeverScraper()
        self.stripe_scraper = StripeScraper()
        self.plaid_scraper = PlaidScraper()
        self.figma_scraper = FigmaScraper()
        self.hashicorp_scraper = HashiCorpScraper()
        self.workable_scraper = WorkableScraper()
        self.robinhood_scraper = RobinhoodScraper()
        self.coinbase_scraper = CoinbaseScraper()
        self.github_scraper = GitHubScraper()
        
        # Company URLs mapped to their job boards and scrapers
        self.company_scrapers = {
            # Ashby-hosted companies
            "linear": {"url": "https://jobs.ashbyhq.com/linear", "scraper": "ashby"},
            "vercel": {"url": "https://jobs.ashbyhq.com/vercel", "scraper": "ashby"},
            "retool": {"url": "https://jobs.ashbyhq.com/retool", "scraper": "ashby"},
            # "brex": {"url": "https://www.brex.com/careers#jobsBoard", "scraper": "brex"},  # Disabled: dynamic content not reliably scrapable
            "figma": {"url": "https://www.figma.com/careers/#job-openings", "scraper": "figma"},
            "notion": {"url": "https://jobs.ashbyhq.com/notion", "scraper": "ashby"},
            "airtable": {"url": "https://jobs.ashbyhq.com/airtable", "scraper": "ashby"},
            "loom": {"url": "https://jobs.ashbyhq.com/loom", "scraper": "ashby"},
            "superhuman": {"url": "https://jobs.ashbyhq.com/superhuman", "scraper": "ashby"},
            "ramp": {"url": "https://jobs.ashbyhq.com/ramp", "scraper": "ashby"},
            "stripe": {"url": "https://stripe.com/jobs/search", "scraper": "stripe"},
            "plaid": {"url": "https://plaid.com/careers/#search", "scraper": "plaid"},
            #"brex": {"url": "https://jobs.ashbyhq.com/brex", "scraper": "ashby"},
            "hashicorp": {"url": "https://www.hashicorp.com/careers/open-positions", "scraper": "hashicorp"},
            "openai": {"url": "https://jobs.ashbyhq.com/openai", "scraper": "ashby"},
            
            # Greenhouse-hosted companies
            "anthropic": {"url": "https://boards.greenhouse.io/anthropic", "scraper": "greenhouse"},
            "scale-ai": {"url": "https://boards.greenhouse.io/scaleai", "scraper": "greenhouse"},
            "hugging-face": {"url": "https://apply.workable.com/huggingface/#jobs", "scraper": "workable"},
            
            # Custom scrapers
            "robinhood": {"url": "https://careers.robinhood.com/", "scraper": "robinhood"},
            "coinbase": {"url": "https://www.coinbase.com/careers/positions", "scraper": "coinbase"},
            "github": {"url": "https://www.github.careers/careers-home/jobs", "scraper": "github"},
            
            # Lever-hosted companies
            "mistral-ai": {"url": "https://jobs.lever.co/mistral", "scraper": "lever"},
            
            # RemoteOK fallback for others
            "google": {"url": "remoteok", "scraper": "remoteok"},
            "amazon": {"url": "remoteok", "scraper": "remoteok"},
            "apple": {"url": "remoteok", "scraper": "remoteok"},
            "meta": {"url": "remoteok", "scraper": "remoteok"},
            "microsoft": {"url": "remoteok", "scraper": "remoteok"},
            "netflix": {"url": "remoteok", "scraper": "remoteok"},
            "tesla": {"url": "remoteok", "scraper": "remoteok"},
            "nvidia": {"url": "remoteok", "scraper": "remoteok"},
            
            # Additional companies from schemas - using RemoteOK as fallback
            "stability-ai": {"url": "remoteok", "scraper": "remoteok"},
            "cohere": {"url": "remoteok", "scraper": "remoteok"},
            "inflection-ai": {"url": "remoteok", "scraper": "remoteok"},
            "xai": {"url": "remoteok", "scraper": "remoteok"},
            "adept": {"url": "remoteok", "scraper": "remoteok"},
            "perplexity-ai": {"url": "remoteok", "scraper": "remoteok"},
            "runway": {"url": "remoteok", "scraper": "remoteok"},
            "pinecone": {"url": "remoteok", "scraper": "remoteok"},
            "weaviate": {"url": "remoteok", "scraper": "remoteok"},
            "langchain": {"url": "remoteok", "scraper": "remoteok"},
            "weights-biases": {"url": "remoteok", "scraper": "remoteok"},
            "labelbox": {"url": "remoteok", "scraper": "remoteok"},
            "truera": {"url": "remoteok", "scraper": "remoteok"},
            "databricks": {"url": "remoteok", "scraper": "remoteok"},
            "datarobot": {"url": "remoteok", "scraper": "remoteok"},
            "c3-ai": {"url": "remoteok", "scraper": "remoteok"},
            "abacus-ai": {"url": "remoteok", "scraper": "remoteok"},
            "sambanova": {"url": "remoteok", "scraper": "remoteok"},
            "cloudflare": {"url": "remoteok", "scraper": "remoteok"},
            "digitalocean": {"url": "remoteok", "scraper": "remoteok"},
            "fastly": {"url": "remoteok", "scraper": "remoteok"},
            "gitlab": {"url": "remoteok", "scraper": "remoteok"},
            "circleci": {"url": "remoteok", "scraper": "remoteok"},
            "netlify": {"url": "remoteok", "scraper": "remoteok"},
            "render": {"url": "remoteok", "scraper": "remoteok"},
            "replit": {"url": "remoteok", "scraper": "remoteok"},
            "atlassian": {"url": "remoteok", "scraper": "remoteok"},
            "slack": {"url": "remoteok", "scraper": "remoteok"},
            "clickup": {"url": "remoteok", "scraper": "remoteok"},
            "snap": {"url": "remoteok", "scraper": "remoteok"},
            "bytedance": {"url": "remoteok", "scraper": "remoteok"},
            "spotify": {"url": "remoteok", "scraper": "remoteok"},
            "pinterest": {"url": "remoteok", "scraper": "remoteok"},
            "square": {"url": "remoteok", "scraper": "remoteok"},
            "affirm": {"url": "remoteok", "scraper": "remoteok"},
            "chime": {"url": "remoteok", "scraper": "remoteok"},
            "snowflake": {"url": "remoteok", "scraper": "remoteok"},
            "confluent": {"url": "remoteok", "scraper": "remoteok"},
            "segment": {"url": "remoteok", "scraper": "remoteok"},
            "mixpanel": {"url": "remoteok", "scraper": "remoteok"},
            "amplitude": {"url": "remoteok", "scraper": "remoteok"},
            "looker": {"url": "remoteok", "scraper": "remoteok"},
            "tableau": {"url": "remoteok", "scraper": "remoteok"},
            "okta": {"url": "remoteok", "scraper": "remoteok"},
            "auth0": {"url": "remoteok", "scraper": "remoteok"},
            "crowdstrike": {"url": "remoteok", "scraper": "remoteok"},
            "sentinelone": {"url": "remoteok", "scraper": "remoteok"},
            "snyk": {"url": "remoteok", "scraper": "remoteok"},
            "salesforce": {"url": "remoteok", "scraper": "remoteok"},
            "workday": {"url": "remoteok", "scraper": "remoteok"},
            "servicenow": {"url": "remoteok", "scraper": "remoteok"},
            "zendesk": {"url": "remoteok", "scraper": "remoteok"},
            "box": {"url": "remoteok", "scraper": "remoteok"},
            "dropbox": {"url": "remoteok", "scraper": "remoteok"},
            "zoom": {"url": "remoteok", "scraper": "remoteok"},
        }
        
        # Company name mappings for RemoteOK
        self.company_name_mappings = {
            "google": ["Google", "Alphabet"],
            "amazon": ["Amazon", "AWS"],
            "apple": ["Apple"],
            "meta": ["Meta", "Facebook", "Instagram", "WhatsApp"],
            "microsoft": ["Microsoft", "LinkedIn", "GitHub"],
            "netflix": ["Netflix"],
            "tesla": ["Tesla"],
            "nvidia": ["NVIDIA", "Nvidia"],
            "stability-ai": ["Stability AI", "Stability"],
            "cohere": ["Cohere"],
            "mistral-ai": ["Mistral AI", "Mistral"],
            "inflection-ai": ["Inflection AI", "Inflection"],
            "xai": ["xAI"],
            "adept": ["Adept"],
            "perplexity-ai": ["Perplexity AI", "Perplexity"],
            "runway": ["Runway"],
            "pinecone": ["Pinecone"],
            "weaviate": ["Weaviate"],
            "langchain": ["LangChain"],
            "weights-biases": ["Weights & Biases", "Weights and Biases"],
            "labelbox": ["Labelbox"],
            "truera": ["Truera"],
            "databricks": ["Databricks"],
            "datarobot": ["DataRobot"],
            "c3-ai": ["C3.ai", "C3 AI"],
            "abacus-ai": ["Abacus.AI", "Abacus AI"],
            "sambanova": ["SambaNova"],
            "cloudflare": ["Cloudflare"],
            "digitalocean": ["DigitalOcean"],
            "fastly": ["Fastly"],
            "gitlab": ["GitLab"],
            "circleci": ["CircleCI"],
            "netlify": ["Netlify"],
            "render": ["Render"],
            "replit": ["Replit"],
            "atlassian": ["Atlassian"],
            "slack": ["Slack"],
            "clickup": ["ClickUp"],
            "snap": ["Snap", "Snapchat"],
            "bytedance": ["ByteDance"],
            "spotify": ["Spotify"],
            "pinterest": ["Pinterest"],
            "square": ["Square"],
            "affirm": ["Affirm"],
            "chime": ["Chime"],
            "snowflake": ["Snowflake"],
            "confluent": ["Confluent"],
            "segment": ["Segment"],
            "mixpanel": ["Mixpanel"],
            "amplitude": ["Amplitude"],
            "looker": ["Looker"],
            "tableau": ["Tableau"],
            "okta": ["Okta"],
            "auth0": ["Auth0"],
            "crowdstrike": ["CrowdStrike"],
            "sentinelone": ["SentinelOne"],
            "snyk": ["Snyk"],
            "salesforce": ["Salesforce"],
            "workday": ["Workday"],
            "servicenow": ["ServiceNow"],
            "zendesk": ["Zendesk"],
            "box": ["Box"],
            "dropbox": ["Dropbox"],
            "zoom": ["Zoom"],
        }
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from specific companies"""
        return await self.scrape_jobs_from_companies([], request)
    
    async def scrape_jobs_from_companies(self, companies: List[str], request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from specific companies using real scrapers with caching"""
        jobs = []
        
        # If no companies specified, use a diverse set of default companies
        if not companies:
            default_companies = [
                "stripe", "figma", "linear", "notion", "github", 
                "plaid", "hashicorp", "vercel", "ramp", "retool"
            ]
            companies = default_companies
        
        # Limit to 8 companies for performance and diversity
        limited_companies = companies[:8]
        
        for company in limited_companies:
            try:
                company_key = company.lower().replace(" ", "-").replace("(", "").replace(")", "")
                
                # Check cache first for individual company
                cached_jobs = await self.cache_service.get_cached_company_jobs(company_key, request)
                if cached_jobs:
                    jobs.extend(cached_jobs)
                    self.logger.info(f"Cache hit: Found {len(cached_jobs)} cached jobs for {company}")
                    continue
                
                # If not in cache, scrape real jobs
                company_jobs = await self._scrape_company_real(company_key, request)
                if company_jobs:
                    # Cache the results
                    await self.cache_service.cache_company_jobs(company_key, request, company_jobs)
                    jobs.extend(company_jobs)
                    self.logger.info(f"Found {len(company_jobs)} real jobs from {company}")
                else:
                    self.logger.warning(f"No real jobs found for {company}")
                
                if len(jobs) >= request.max_results:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error scraping {company}: {e}")
                continue
        
        return jobs[:request.max_results]
    
    async def _scrape_company_real(self, company_key: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape real jobs from company job boards"""
        jobs = []
        
        if company_key not in self.company_scrapers:
            self.logger.warning(f"Company {company_key} not supported")
            return jobs
        
        company_info = self.company_scrapers[company_key]
        scraper_type = company_info["scraper"]
        url = company_info["url"]
        self.logger.info(f"[CompanyScraper] Requested company: {company_key}, scraper_type: {scraper_type}, url: {url}")
        
        try:
            if scraper_type == "ashby":
                jobs = await self.ashby_scraper.scrape_jobs(url, request)
            elif scraper_type == "greenhouse":
                jobs = await self.greenhouse_scraper.scrape_jobs(url, request)
            elif scraper_type == "lever":
                jobs = await self.lever_scraper.scrape_jobs(url, request)
            elif scraper_type == "stripe":
                logger.info(f"[CompanyScraper] Using StripeScraper for company '{company_key}' and url '{url}'")
                jobs = await self.stripe_scraper.scrape_jobs(url, request)
                logger.info(f"[CompanyScraper] StripeScraper returned {len(jobs)} jobs before filtering.")
            elif scraper_type == "plaid":
                jobs = await self.plaid_scraper.scrape_jobs(url, request)
            elif scraper_type == "figma":
                jobs = await self.figma_scraper.scrape_jobs(url, request)
            elif scraper_type == "hashicorp":
                jobs = await self.hashicorp_scraper.scrape_jobs(url, request)
            elif scraper_type == "workable":
                jobs = await self.workable_scraper.scrape_jobs(url, request)
            elif scraper_type == "robinhood":
                jobs = await self.robinhood_scraper.scrape_jobs(url, request)
            elif scraper_type == "coinbase":
                jobs = await self.coinbase_scraper.scrape_jobs(url, request)
            elif scraper_type == "github":
                jobs = await self.github_scraper.scrape_jobs(url, request)
            elif scraper_type == "remoteok":
                jobs = await self._scrape_remoteok_for_company(company_key, request)
            else:
                logger.info(f"[CompanyScraper] Using scraper '{scraper_type}' for company '{company_key}' and url '{url}'")
                
        except Exception as e:
            self.logger.error(f"Error scraping {company_key} with {scraper_type}: {e}")
        
        return jobs
    
    async def _scrape_remoteok_for_company(self, company_key: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape RemoteOK for specific companies with fallback to general job matching"""
        jobs = []
        
        try:
            session = await self._get_session()
            
            async with session.get("https://remoteok.io/api") as response:
                if response.status == 200:
                    data = await response.json()
                    job_data = data[1:] if len(data) > 1 else []
                    
                    # Get company name variations
                    company_names = self.company_name_mappings.get(company_key, [company_key.title()])
                    
                    # First, try to find jobs from the specific company
                    company_specific_jobs = []
                    general_matching_jobs = []
                    
                    for job in job_data:
                        try:
                            company = job.get('company', '')
                            title = job.get('position', '')
                            
                            # Check if job title matches our criteria
                            if self._matches_job_criteria(title, request.job_titles):
                                job_position = JobPosition(
                                    title=title,
                                    company=company,
                                    location=job.get('location', 'Remote'),
                                    url=f"https://remoteok.io/remote-jobs/{job.get('id', '')}",
                                    job_board="RemoteOK",
                                    description_snippet=job.get('description', '')[:200] + "..." if job.get('description') else f"Remote {title} position at {company}",
                                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                                    salary_range=f"${job.get('salary_min', 0)}-${job.get('salary_max', 0)}" if job.get('salary_min') else None,
                                    job_type="Full-time",
                                    remote_option="Remote"
                                )
                                
                                # Check if this job is from one of our target companies
                                if any(name.lower() in company.lower() for name in company_names):
                                    company_specific_jobs.append(job_position)
                                else:
                                    general_matching_jobs.append(job_position)
                                
                                # Stop if we have enough jobs
                                if len(company_specific_jobs) + len(general_matching_jobs) >= request.max_results * 2:
                                    break
                                        
                        except Exception as e:
                            logger.debug(f"Error parsing RemoteOK job: {e}")
                            continue
                    
                    # Prioritize company-specific jobs, then add general matching jobs
                    jobs.extend(company_specific_jobs)
                    
                    # If no company-specific jobs found, add general matching jobs as fallback
                    if not company_specific_jobs:
                        jobs.extend(general_matching_jobs[:request.max_results])
                        if jobs:
                            self.logger.info(f"No {company_key} jobs found on RemoteOK, returning {len(jobs)} general remote jobs matching criteria")
                    
                    jobs = jobs[:request.max_results]
                            
        except Exception as e:
            logger.error(f"Error scraping RemoteOK for {company_key}: {e}")
        
        return jobs
    
    def _matches_job_criteria(self, title: str, target_titles: List[str]) -> bool:
        """Check if job title matches any target titles"""
        title_lower = title.lower()
        return any(target.lower() in title_lower for target in target_titles)
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL"""
        return any(company in url.lower() for company in self.company_scrapers.keys())
    
    def get_supported_companies(self) -> List[str]:
        """Get list of supported companies"""
        return list(self.company_scrapers.keys())
    
    async def close(self):
        """Close the scraper session"""
        if self.session:
            await self.session.close() 