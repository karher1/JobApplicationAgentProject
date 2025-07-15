#!/usr/bin/env python3
"""
Script to extract job listings from Coinbase careers page focusing on the job listings section
"""

import asyncio
from playwright.async_api import async_playwright

async def extract_coinbase_jobs():
    """Extract job listings from the middle section of Coinbase careers page."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see what's happening
        page = await browser.new_page()
        
        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        })
        
        print("Navigating to Coinbase careers page...")
        await page.goto("https://www.coinbase.com/careers/positions")
        await page.wait_for_timeout(5000)  # Wait for page to load
        
        # Look for the main job listings section (skip header/navigation)
        print("\n=== Looking for job listings section ===")
        
        # Try to find the main content area with job listings
        main_content_selectors = [
            'main',
            '[role="main"]',
            'div[class*="main"]',
            'div[class*="content"]',
            'div[class*="positions"]',
            'div[class*="jobs"]',
        ]
        
        main_content = None
        for selector in main_content_selectors:
            element = await page.query_selector(selector)
            if element:
                text = await element.inner_text()
                if len(text) > 1000:  # Main content should be substantial
                    main_content = element
                    print(f"Found main content with selector: {selector}")
                    break
        
        if not main_content:
            print("Could not find main content area, using entire page")
            main_content = page
        
        # Look for department sections/dropdowns within the main content
        print("\n=== Looking for department sections ===")
        
        # Look for elements that might contain department names and job lists
        department_selectors = [
            'div[class*="department"]',
            'div[class*="section"]',
            'div[class*="category"]',
            'div[class*="group"]',
            'div[class*="accordion"]',
            'div[class*="collaps"]',
            'div[class*="dropdown"]',
            'div[class*="cds-flex-f1tjav3"]',  # From the HTML structure you showed
        ]
        
        departments_found = []
        
        for selector in department_selectors:
            elements = await main_content.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                
                for i, element in enumerate(elements):
                    try:
                        text = await element.inner_text()
                        
                        # Look for department-like text (contains job-related keywords)
                        if any(keyword in text.lower() for keyword in ['engineering', 'product', 'design', 'marketing', 'sales', 'operations', 'finance', 'legal', 'hr', 'data', 'security', 'compliance']):
                            # Check if this element contains job links
                            job_links = await element.query_selector_all('a[href*="/careers/positions/"]')
                            if job_links:
                                print(f"  Department element {i}: {len(job_links)} job links")
                                print(f"    Text preview: {text[:200]}...")
                                departments_found.append((element, text[:100], len(job_links)))
                            
                    except Exception as e:
                        continue
        
        # If we found department sections, extract jobs from them
        if departments_found:
            print(f"\n=== Found {len(departments_found)} department sections ===")
            
            all_jobs = []
            for dept_element, dept_text, job_count in departments_found:
                print(f"\nProcessing department: {dept_text}")
                
                # Try to expand the department if it's collapsed
                try:
                    # Look for clickable elements within this department
                    clickable = await dept_element.query_selector('[aria-expanded="false"]')
                    if clickable:
                        print("  Expanding department...")
                        await clickable.click()
                        await page.wait_for_timeout(1000)
                except:
                    pass
                
                # Extract job links from this department
                job_links = await dept_element.query_selector_all('a[href*="/careers/positions/"]')
                print(f"  Found {len(job_links)} job links in this department")
                
                for i, job_link in enumerate(job_links):
                    try:
                        href = await job_link.get_attribute('href')
                        
                        # Get job title - it might be in the link text or a nearby element
                        job_title = await job_link.inner_text()
                        if not job_title.strip():
                            # Try to find title in parent or sibling elements
                            parent = await job_link.query_selector('xpath=..')
                            if parent:
                                # Look for title in spans or other text elements
                                title_elements = await parent.query_selector_all('span, p, div')
                                for title_elem in title_elements:
                                    title_text = await title_elem.inner_text()
                                    if title_text.strip() and len(title_text) > 5 and len(title_text) < 100:
                                        job_title = title_text.strip()
                                        break
                        
                        # Get location - look for location indicators
                        location = "Unknown"
                        try:
                            # Look for location in the same container as the job link
                            container = await job_link.query_selector('xpath=../..')
                            if container:
                                container_text = await container.inner_text()
                                # Look for common location patterns
                                location_keywords = ['remote', 'san francisco', 'new york', 'london', 'singapore', 'tokyo', 'chicago', 'austin', 'seattle', 'los angeles']
                                for keyword in location_keywords:
                                    if keyword in container_text.lower():
                                        location = keyword.title()
                                        break
                        except:
                            pass
                        
                        full_url = f"https://www.coinbase.com{href}" if href.startswith('/') else href
                        
                        job_data = {
                            'title': job_title,
                            'url': full_url,
                            'location': location,
                            'department': dept_text.split('\n')[0][:50]  # First line of department text
                        }
                        
                        all_jobs.append(job_data)
                        print(f"    Job {i+1}: {job_title} - {location}")
                        
                    except Exception as e:
                        print(f"    Error processing job link {i}: {e}")
                        continue
            
            print(f"\n=== Total jobs extracted: {len(all_jobs)} ===")
            
            # Show sample of extracted jobs
            print("\n=== Sample jobs ===")
            for i, job in enumerate(all_jobs[:10]):
                print(f"{i+1}. {job['title']}")
                print(f"   Department: {job['department']}")
                print(f"   Location: {job['location']}")
                print(f"   URL: {job['url']}")
                print()
        
        else:
            print("\n=== No department sections found, trying alternative approach ===")
            
            # Look for all job links on the page and try to extract their context
            all_job_links = await page.query_selector_all('a[href*="/careers/positions/"]')
            print(f"Found {len(all_job_links)} total job links")
            
            jobs = []
            for i, job_link in enumerate(all_job_links[:20]):  # Limit to first 20 for analysis
                try:
                    href = await job_link.get_attribute('href')
                    
                    # Try to get job information from surrounding context
                    # Look at parent containers for job title and location
                    current_element = job_link
                    job_title = ""
                    location = ""
                    
                    # Try multiple parent levels to find job info
                    for level in range(5):
                        try:
                            parent = await current_element.query_selector('xpath=..')
                            if parent:
                                parent_text = await parent.inner_text()
                                
                                # Look for job title patterns
                                lines = parent_text.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line and len(line) > 5 and len(line) < 100:
                                        # Check if this looks like a job title
                                        if any(keyword in line.lower() for keyword in ['engineer', 'manager', 'analyst', 'director', 'specialist', 'lead', 'senior', 'junior', 'developer', 'designer']):
                                            if not job_title:
                                                job_title = line
                                        
                                        # Check if this looks like a location
                                        if any(keyword in line.lower() for keyword in ['remote', 'san francisco', 'new york', 'london', 'singapore']):
                                            if not location:
                                                location = line
                                
                                current_element = parent
                            else:
                                break
                        except:
                            break
                    
                    if job_title:
                        full_url = f"https://www.coinbase.com{href}" if href.startswith('/') else href
                        jobs.append({
                            'title': job_title,
                            'url': full_url,
                            'location': location or "Unknown",
                            'department': "Unknown"
                        })
                        print(f"Job {i+1}: {job_title} - {location}")
                
                except Exception as e:
                    print(f"Error processing job {i}: {e}")
                    continue
            
            print(f"\nExtracted {len(jobs)} jobs using alternative approach")
        
        # Save the page content for further analysis
        print("\n=== Saving page content ===")
        html_content = await page.content()
        with open("coinbase_jobs_analysis.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Saved page content to coinbase_jobs_analysis.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_coinbase_jobs()) 