#!/usr/bin/env python3

import asyncio
import re
from playwright.async_api import async_playwright

async def debug_coinbase():
    """Debug the Coinbase page structure"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        })
        
        print("Navigating to Coinbase careers page...")
        await page.goto("https://www.coinbase.com/careers", wait_until='networkidle', timeout=30000)
        
        # Get page content
        content = await page.content()
        print(f"Page content length: {len(content)}")
        
        # Save the content for analysis
        with open("coinbase_current_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved page content to coinbase_current_page.html")
        
        # Look for various patterns that might contain job data
        patterns_to_check = [
            r'"departments":\s*\[',
            r'"jobs":\s*\[',
            r'"absolute_url":\s*"[^"]*coinbase\.com[^"]*careers',
            r'"title":\s*"[^"]*Engineer[^"]*"',
            r'"title":\s*"[^"]*Manager[^"]*"',
            r'careers.*positions',
            r'Greenhouse',
            r'job.*listing',
        ]
        
        print("\nSearching for job-related patterns:")
        for pattern in patterns_to_check:
            matches = re.findall(pattern, content, re.IGNORECASE)
            print(f"Pattern '{pattern}': {len(matches)} matches")
            if matches:
                print(f"  First match: {matches[0][:100]}...")
        
        # Look for script tags that might contain job data
        scripts = await page.query_selector_all("script")
        print(f"\nFound {len(scripts)} script tags")
        
        job_containing_scripts = 0
        for i, script in enumerate(scripts):
            try:
                script_content = await script.inner_text()
                if script_content and ('job' in script_content.lower() or 'career' in script_content.lower()):
                    job_containing_scripts += 1
                    if 'absolute_url' in script_content and 'title' in script_content:
                        print(f"Script {i} contains job data!")
                        # Save this script for analysis
                        with open(f"coinbase_script_{i}.txt", "w", encoding="utf-8") as f:
                            f.write(script_content)
                        print(f"Saved script {i} to coinbase_script_{i}.txt")
                        
                        # Look for the departments pattern in this script
                        dept_match = re.search(r'"departments":\s*(\[.*?\])', script_content, re.DOTALL)
                        if dept_match:
                            print(f"Found departments pattern in script {i}!")
                        else:
                            print(f"No departments pattern found in script {i}")
                            
            except Exception as e:
                print(f"Error processing script {i}: {e}")
        
        print(f"Scripts containing job-related content: {job_containing_scripts}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_coinbase()) 