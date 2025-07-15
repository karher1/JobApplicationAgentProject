#!/usr/bin/env python3
"""
Final script to extract job listings from Coinbase careers page
Handles Cloudflare protection and various page structures
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright
import time

async def extract_coinbase_jobs():
    """Extract job listings from Coinbase careers page with Cloudflare handling."""
    
    async with async_playwright() as p:
        # Use a more realistic browser setup
        browser = await p.chromium.launch(
            headless=False,  # Run in visible mode to handle Cloudflare
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Add extra headers to look more like a real browser
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        try:
            print("Navigating to Coinbase careers page...")
            await page.goto("https://www.coinbase.com/careers", wait_until='networkidle', timeout=60000)
            
            # Wait for potential Cloudflare challenge
            print("Waiting for page to load (handling potential Cloudflare challenge)...")
            await page.wait_for_timeout(10000)  # Wait 10 seconds
            
            # Check if we're on a Cloudflare challenge page
            if "Just a moment" in await page.content() or "Enable JavaScript" in await page.content():
                print("Detected Cloudflare challenge. Waiting for it to resolve...")
                await page.wait_for_timeout(15000)  # Wait 15 more seconds
                
                # Try to wait for the challenge to complete
                try:
                    await page.wait_for_url("**/careers**", timeout=30000)
                    print("Cloudflare challenge resolved!")
                except:
                    print("Cloudflare challenge may still be active, continuing...")
            
            # Try multiple URLs to find job listings
            urls_to_try = [
                "https://www.coinbase.com/careers",
                "https://www.coinbase.com/careers/positions",
                "https://www.coinbase.com/careers/jobs"
            ]
            
            jobs_found = []
            
            for url in urls_to_try:
                print(f"Trying URL: {url}")
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(5000)
                    
                    content = await page.content()
                    
                    # Method 1: Look for job links in the page
                    job_links = await page.query_selector_all('a[href*="careers"], a[href*="jobs"], a[href*="position"]')
                    print(f"Found {len(job_links)} potential job links")
                    
                    # Method 2: Look for job data in script tags
                    scripts = await page.query_selector_all('script')
                    print(f"Found {len(scripts)} script tags to analyze")
                    
                    for script in scripts:
                        try:
                            script_content = await script.inner_text()
                            if script_content and ('job' in script_content.lower() or 'position' in script_content.lower()):
                                # Look for JSON data
                                job_data = extract_jobs_from_script(script_content)
                                if job_data:
                                    jobs_found.extend(job_data)
                                    print(f"Found {len(job_data)} jobs in script tag")
                        except:
                            continue
                    
                    # Method 3: Look for job listings in the DOM
                    job_elements = await page.query_selector_all('[data-testid*="job"], [class*="job"], [class*="position"], [class*="career"]')
                    print(f"Found {len(job_elements)} job elements in DOM")
                    
                    for element in job_elements:
                        try:
                            job_info = await extract_job_from_element(element)
                            if job_info:
                                jobs_found.append(job_info)
                        except:
                            continue
                    
                    # Method 4: Look for external job board redirects (like Greenhouse)
                    greenhouse_links = await page.query_selector_all('a[href*="greenhouse"], a[href*="lever"], a[href*="workday"]')
                    if greenhouse_links:
                        print(f"Found {len(greenhouse_links)} external job board links")
                        for link in greenhouse_links:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            if href and text:
                                jobs_found.append({
                                    'title': text.strip(),
                                    'url': href,
                                    'company': 'Coinbase',
                                    'location': 'Various',
                                    'source': 'external_board'
                                })
                    
                    if jobs_found:
                        print(f"Found jobs at {url}, stopping search")
                        break
                        
                except Exception as e:
                    print(f"Error with URL {url}: {str(e)}")
                    continue
            
            # If no jobs found through normal methods, try to find the actual job board
            if not jobs_found:
                print("No jobs found through normal methods. Looking for job board redirects...")
                
                # Look for any links that might lead to job listings
                all_links = await page.query_selector_all('a[href]')
                for link in all_links:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and any(keyword in href.lower() for keyword in ['job', 'career', 'position', 'greenhouse', 'lever']):
                        print(f"Found potential job link: {href} - {text}")
                        jobs_found.append({
                            'title': text.strip() if text else 'View Jobs',
                            'url': href,
                            'company': 'Coinbase',
                            'location': 'Various',
                            'source': 'link_redirect'
                        })
            
            print(f"Total jobs found: {len(jobs_found)}")
            
            # Save results
            with open("coinbase_jobs_final.json", "w") as f:
                json.dump(jobs_found, f, indent=2)
            
            # Display results
            for i, job in enumerate(jobs_found[:10]):  # Show first 10
                print(f"\n{i+1}. {job.get('title', 'N/A')}")
                print(f"   Company: {job.get('company', 'N/A')}")
                print(f"   Location: {job.get('location', 'N/A')}")
                print(f"   URL: {job.get('url', 'N/A')}")
                print(f"   Source: {job.get('source', 'N/A')}")
            
            return jobs_found
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return []
        finally:
            await browser.close()

def extract_jobs_from_script(script_content):
    """Extract job data from script content."""
    jobs = []
    
    # Look for various JSON patterns
    patterns = [
        r'"jobs":\s*(\[.*?\])',
        r'"positions":\s*(\[.*?\])',
        r'"careers":\s*(\[.*?\])',
        r'"departments":\s*(\[.*?\])',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, script_content, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            job = parse_job_object(item)
                            if job:
                                jobs.append(job)
            except:
                continue
    
    return jobs

def parse_job_object(job_data):
    """Parse a job object from JSON data."""
    if not isinstance(job_data, dict):
        return None
    
    # Look for title
    title = job_data.get('title') or job_data.get('name') or job_data.get('position')
    if not title:
        return None
    
    # Look for URL
    url = job_data.get('url') or job_data.get('absolute_url') or job_data.get('link')
    if url and url.startswith('\\'):
        url = url.replace('\\u002F', '/')
    
    # Look for location
    location = job_data.get('location')
    if isinstance(location, dict):
        location = location.get('name') or location.get('city')
    
    return {
        'title': title,
        'url': url,
        'company': 'Coinbase',
        'location': location or 'Various',
        'source': 'script_json'
    }

async def extract_job_from_element(element):
    """Extract job information from a DOM element."""
    try:
        # Try to get job title
        title_element = await element.query_selector('h1, h2, h3, h4, .title, [class*="title"]')
        title = await title_element.inner_text() if title_element else None
        
        # Try to get job URL
        link_element = await element.query_selector('a[href]')
        url = await link_element.get_attribute('href') if link_element else None
        
        # Try to get location
        location_element = await element.query_selector('[class*="location"], [class*="city"]')
        location = await location_element.inner_text() if location_element else None
        
        if title:
            return {
                'title': title.strip(),
                'url': url,
                'company': 'Coinbase',
                'location': location.strip() if location else 'Various',
                'source': 'dom_element'
            }
    except:
        pass
    
    return None

if __name__ == "__main__":
    asyncio.run(extract_coinbase_jobs()) 