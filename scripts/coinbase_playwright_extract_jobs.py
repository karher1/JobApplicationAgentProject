from playwright.sync_api import sync_playwright
import json
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.coinbase.com/careers/positions")
    page.wait_for_timeout(5000)  # Wait for jobs to load (adjust as needed)

    # Extract all script tags and look for embedded JSON with job data
    scripts = page.query_selector_all("script")
    jobs_found = False
    for script in scripts:
        content = script.inner_text()
        # Look for a script tag containing job data
        if 'jobs' in content and 'absolute_url' in content and 'title' in content:
            # Try to extract the JSON object from the script content
            try:
                # Use regex to extract the largest JSON object in the script
                matches = re.findall(r'\{.*\}', content, re.DOTALL)
                for match in matches:
                    if 'jobs' in match and 'absolute_url' in match and 'title' in match:
                        try:
                            data = json.loads(match)
                            # Now extract jobs from the JSON structure
                            jobs = []
                            # The structure may be a list of departments, each with a 'jobs' list
                            if isinstance(data, dict) and 'departments' in data:
                                for dept in data['departments']:
                                    department = dept.get('name', '')
                                    for job in dept.get('jobs', []):
                                        jobs.append({
                                            'title': job.get('title'),
                                            'location': job.get('location', {}).get('name', ''),
                                            'url': job.get('absolute_url'),
                                            'department': department
                                        })
                            # If it's a flat list
                            elif isinstance(data, list):
                                for job in data:
                                    jobs.append({
                                        'title': job.get('title'),
                                        'location': job.get('location', {}).get('name', ''),
                                        'url': job.get('absolute_url'),
                                        'department': job.get('department', '')
                                    })
                            print(json.dumps(jobs, indent=2))
                            jobs_found = True
                            break
                        except Exception as e:
                            continue
                if jobs_found:
                    break
            except Exception as e:
                print("Error parsing JSON:", e)
    if not jobs_found:
        print("No job data found in script tags.")
    browser.close() 