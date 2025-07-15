#!/usr/bin/env python3
"""
Script to analyze Coinbase careers page dropdown structure and extract job listings
"""

import asyncio
from playwright.async_api import async_playwright

async def analyze_coinbase_dropdowns():
    """Analyze the dropdown structure on Coinbase careers page."""
    
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
        
        # Look for dropdown elements
        print("\n=== Analyzing dropdown structure ===")
        
        # Check for common dropdown patterns
        dropdown_selectors = [
            '[class*="dropdown"]',
            '[class*="collaps"]',
            '[class*="accordion"]',
            '[class*="expand"]',
            '[role="button"]',
            '[aria-expanded]',
            'div[class*="cds-flex-f1tjav3"]',  # From the HTML you showed
            'div[class*="cds-column-c1kchipr"]',
        ]
        
        for selector in dropdown_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                
                # Check first few elements
                for i, element in enumerate(elements[:3]):
                    try:
                        text = await element.inner_text()
                        classes = await element.get_attribute('class')
                        print(f"  Element {i}: classes='{classes}', text='{text[:100]}...'")
                    except:
                        pass
        
        # Look for job links specifically
        print("\n=== Looking for job links ===")
        job_link_selectors = [
            'a[href*="/careers/positions/"]',
            'a[href*="/positions/"]',
            '[class*="link"]',
            'a[class*="cds-link"]',
        ]
        
        for selector in job_link_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} job links with selector: {selector}")
                
                for i, element in enumerate(elements[:5]):
                    try:
                        href = await element.get_attribute('href')
                        text = await element.inner_text()
                        print(f"  Job {i}: {text} -> {href}")
                    except:
                        pass
        
        # Try to find and click on dropdown toggles
        print("\n=== Trying to expand dropdowns ===")
        
        # Look for elements that might be dropdown toggles
        toggle_selectors = [
            '[aria-expanded="false"]',
            '[class*="collapsed"]',
            'button[class*="dropdown"]',
            'div[role="button"]',
        ]
        
        for selector in toggle_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} potential dropdown toggles: {selector}")
                
                # Try clicking the first few
                for i, element in enumerate(elements[:3]):
                    try:
                        text = await element.inner_text()
                        print(f"  Clicking toggle {i}: {text[:50]}...")
                        await element.click()
                        await page.wait_for_timeout(1000)  # Wait for dropdown to expand
                        
                        # Check if new job links appeared
                        new_links = await page.query_selector_all('a[href*="/careers/positions/"]')
                        print(f"    After clicking: found {len(new_links)} job links")
                        
                    except Exception as e:
                        print(f"    Error clicking element {i}: {e}")
        
        # Final check for all job links
        print("\n=== Final job link count ===")
        all_job_links = await page.query_selector_all('a[href*="/careers/positions/"]')
        print(f"Total job links found: {len(all_job_links)}")
        
        # Extract details from first 10 job links
        print("\n=== Sample job details ===")
        for i, link in enumerate(all_job_links[:10]):
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                
                # Try to find location info near the link
                parent = await link.query_selector('xpath=..')
                if parent:
                    parent_text = await parent.inner_text()
                    print(f"Job {i+1}: {text}")
                    print(f"  URL: {href}")
                    print(f"  Context: {parent_text[:200]}...")
                    print()
            except Exception as e:
                print(f"Error processing job link {i}: {e}")
        
        # Save page content for analysis
        print("\n=== Saving page content ===")
        html_content = await page.content()
        with open("coinbase_dropdown_analysis.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Saved page content to coinbase_dropdown_analysis.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_coinbase_dropdowns()) 