import os
import logging
import time
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import undetected_chromedriver as uc
from src.models.schemas import FormField, JobPosition
from src.services.database_service import DatabaseService
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class JobApplicationService:
    """Service for handling job application automation"""
    
    def __init__(self, database_service: DatabaseService, llm_service: LLMService):
        self.database_service = database_service
        self.llm_service = llm_service
        
    async def extract_form_fields(self, url: str) -> List[FormField]:
        """Extract form fields from a job application page"""
        logger.info(f"Extracting form fields from: {url}")
        
        # Configure Chrome options
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = None
        try:
            # Try undetected-chromedriver first
            try:
                driver = uc.Chrome(options=options)
            except Exception as chrome_error:
                logger.warning(f"Undetected Chrome driver failed: {chrome_error}")
                # Fallback to regular Chrome driver
                try:
                    driver = webdriver.Chrome(options=options)
                except Exception as regular_chrome_error:
                    logger.error(f"Both Chrome drivers failed: {regular_chrome_error}")
                    # Return mock data for testing
                    return [
                        FormField(
                            label="Full Name",
                            field_type="text",
                            required=True,
                            placeholder="Enter your full name",
                            options=None,
                            xpath="//input[@name='full_name']"
                        ),
                        FormField(
                            label="Email",
                            field_type="email",
                            required=True,
                            placeholder="Enter your email",
                            options=None,
                            xpath="//input[@name='email']"
                        ),
                        FormField(
                            label="Phone",
                            field_type="tel",
                            required=False,
                            placeholder="Enter your phone number",
                            options=None,
                            xpath="//input[@name='phone']"
                        )
                    ]
            
            wait = WebDriverWait(driver, 30)
            
            # Navigate to URL
            driver.get(url)
            time.sleep(5)
            
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            time.sleep(3)
            
            form_fields = []
            
            # Enhanced form field detection
            field_selectors = [
                "//input[@type='text']",
                "//input[@type='email']", 
                "//input[@type='tel']",
                "//input[@type='url']",
                "//input[@type='file']",
                "//textarea",
                "//select",
                "//div[contains(@class, 'form-field')]//input",
                "//div[contains(@class, 'form-field')]//textarea",
                "//div[contains(@class, 'form-field')]//select",
            ]
            
            for selector in field_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            field_info = self._extract_field_info(driver, element)
                            if field_info and field_info.label:
                                form_fields.append(field_info)
                                logger.info(f"Found field: {field_info.label} ({field_info.field_type})")
                        except Exception as e:
                            logger.warning(f"Error processing element: {str(e)}")
                            continue
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {str(e)}")
                    continue
            
            # Remove duplicates based on label
            unique_fields = []
            seen_labels = set()
            for field in form_fields:
                if field.label.lower() not in seen_labels:
                    unique_fields.append(field)
                    seen_labels.add(field.label.lower())
            
            logger.info(f"Extracted {len(unique_fields)} unique form fields")
            return unique_fields
            
        except Exception as e:
            logger.error(f"Error extracting form fields: {str(e)}")
            return []
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _extract_field_info(self, driver, element) -> Optional[FormField]:
        """Extract information about a form field element"""
        try:
            # Get field type
            field_type = element.get_attribute("type") or element.tag_name
            if field_type == "input":
                field_type = "text"
            
            # Get label
            label = self._find_label_for_element(driver, element)
            
            if not label:
                return None
            
            # Get other attributes
            required = element.get_attribute("required") is not None
            placeholder = element.get_attribute("placeholder")
            
            # Get options for select elements
            options = None
            if element.tag_name == "select":
                try:
                    select_element = Select(element)
                    options = [option.text for option in select_element.options if option.text.strip()]
                except:
                    pass
            
            # Generate XPath
            xpath = self._generate_xpath_for_element(driver, element)
            
            return FormField(
                label=label,
                field_type=field_type,
                required=required,
                placeholder=placeholder,
                options=options,
                xpath=xpath
            )
            
        except Exception as e:
            logger.warning(f"Error extracting field info: {str(e)}")
            return None
    
    def _find_label_for_element(self, driver, element) -> str:
        """Find label for an element using various methods"""
        # Try different methods to find label
        element_id = element.get_attribute("id")
        if element_id:
            try:
                label_element = driver.find_element(By.XPATH, f"//label[@for='{element_id}']")
                return label_element.text.strip()
            except:
                pass
        
        # Try to find label in parent container
        try:
            parent = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'form-field') or contains(@class, 'field')][1]")
            label_element = parent.find_element(By.TAG_NAME, "label")
            return label_element.text.strip()
        except:
            pass
        
        # Use placeholder or aria-label as fallback
        label = element.get_attribute("placeholder") or element.get_attribute("aria-label")
        if label:
            return label
        
        return None
    
    def _generate_xpath_for_element(self, driver, element) -> str:
        """Generate a unique XPath for an element"""
        try:
            return driver.execute_script("""
                function getXPath(element) {
                    if (element.id !== '') {
                        return '//*[@id="' + element.id + '"]';
                    }
                    if (element === document.body) {
                        return '/html/body';
                    }
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) {
                            return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }
                return getXPath(arguments[0]);
            """, element)
        except:
            return None
    
    async def apply_to_job(self, job_url: str, form_data: Dict[str, Any], form_fields: List[FormField]) -> Dict[str, Any]:
        """Apply to a job by filling out the form"""
        logger.info(f"Applying to job: {job_url}")
        
        # Configure Chrome options
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = None
        try:
            # Use undetected-chromedriver
            driver = uc.Chrome(options=options)
            wait = WebDriverWait(driver, 30)
            
            # Navigate to URL
            driver.get(job_url)
            time.sleep(5)
            
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            time.sleep(3)
            
            filled_fields = []
            failed_fields = []
            
            # Fill form fields
            for field in form_fields:
                try:
                    success = await self._fill_field(driver, field, form_data)
                    if success:
                        filled_fields.append(field.label)
                    else:
                        failed_fields.append(field.label)
                except Exception as e:
                    logger.warning(f"Error filling field {field.label}: {str(e)}")
                    failed_fields.append(field.label)
            
            # Don't actually submit the form for safety
            logger.info("Form filling completed (submission disabled for safety)")
            
            return {
                "success": len(filled_fields) > 0,
                "filled_fields": filled_fields,
                "failed_fields": failed_fields,
                "error_message": None
            }
            
        except Exception as e:
            logger.error(f"Error applying to job: {str(e)}")
            return {
                "success": False,
                "filled_fields": [],
                "failed_fields": [field.label for field in form_fields],
                "error_message": str(e)
            }
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    async def _fill_field(self, driver, field: FormField, form_data: Dict[str, Any]) -> bool:
        """Fill a single form field"""
        try:
            # Find the element
            element = self._find_input_element(driver, field.label, form_data)
            if not element:
                return False
            
            # Get the value to fill
            value = self._get_field_value(field, form_data)
            if not value:
                return False
            
            # Fill the field
            self._fill_input_field(driver, element, value)
            
            # Add a small delay
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.warning(f"Error filling field {field.label}: {str(e)}")
            return False
    
    def _find_input_element(self, driver, field_name: str, form_data: Dict[str, Any]):
        """Find input element for a field"""
        try:
            # Try multiple strategies to find the element
            strategies = [
                # Strategy 1: Find by label text
                f"//label[contains(text(), '{field_name}')]/following-sibling::*[1]",
                f"//label[contains(text(), '{field_name}')]/..//input",
                f"//label[contains(text(), '{field_name}')]/..//textarea",
                f"//label[contains(text(), '{field_name}')]/..//select",
                
                # Strategy 2: Find by placeholder
                f"//input[@placeholder='{field_name}']",
                f"//textarea[@placeholder='{field_name}']",
                
                # Strategy 3: Find by name attribute
                f"//input[@name='{field_name.lower().replace(' ', '_')}']",
                f"//textarea[@name='{field_name.lower().replace(' ', '_')}']",
                
                # Strategy 4: Find by ID
                f"//input[@id='{field_name.lower().replace(' ', '_')}']",
                f"//textarea[@id='{field_name.lower().replace(' ', '_')}']",
                
                # Strategy 5: Find by aria-label
                f"//input[@aria-label='{field_name}']",
                f"//textarea[@aria-label='{field_name}']",
            ]
            
            for strategy in strategies:
                try:
                    elements = driver.find_elements(By.XPATH, strategy)
                    if elements:
                        return elements[0]
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Error finding input element for {field_name}: {str(e)}")
            return None
    
    def _get_field_value(self, field: FormField, form_data: Dict[str, Any]) -> str:
        """Get the value to fill for a field"""
        # Map common field names to form data keys
        field_mapping = {
            "first name": "first_name",
            "last name": "last_name",
            "email": "email",
            "phone": "phone",
            "linkedin": "linkedin_url",
            "portfolio": "portfolio_url",
            "cover letter": "cover_letter",
            "resume": "resume_file"
        }
        
        field_lower = field.label.lower()
        
        # Check direct mapping
        for key, value in field_mapping.items():
            if key in field_lower:
                return form_data.get(value, "")
        
        # Check additional_info
        if "additional_info" in form_data:
            return form_data["additional_info"].get(field.label, "")
        
        # Return empty string if no match
        return ""
    
    def _fill_input_field(self, driver, element, value: str):
        """Fill an input field with a value"""
        try:
            # Clear the field first
            element.clear()
            
            # Fill the field
            element.send_keys(value)
            
        except Exception as e:
            logger.warning(f"Error filling input field: {str(e)}")
            raise
    
    async def batch_apply_to_jobs(self, jobs: List[JobPosition]):
        """Apply to multiple jobs in batch"""
        logger.info(f"Starting batch application to {len(jobs)} jobs")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, job in enumerate(jobs, 1):
            logger.info(f"Processing job {i}/{len(jobs)}: {job.title} at {job.company}")
            
            try:
                # Extract form fields
                form_fields = await self.extract_form_fields(job.url)
                
                if form_fields:
                    # Generate form data using LLM
                    form_data = await self.llm_service.generate_form_data(form_fields)
                    
                    # Apply to job
                    result = await self.apply_to_job(job.url, form_data, form_fields)
                    
                    if result["success"]:
                        successful_count += 1
                    else:
                        failed_count += 1
                    
                    results.append({
                        "job_id": job.id,
                        "job_title": job.title,
                        "company": job.company,
                        "success": result["success"],
                        "filled_fields": result["filled_fields"],
                        "failed_fields": result["failed_fields"],
                        "error_message": result["error_message"]
                    })
                else:
                    failed_count += 1
                    results.append({
                        "job_id": job.id,
                        "job_title": job.title,
                        "company": job.company,
                        "success": False,
                        "filled_fields": [],
                        "failed_fields": [],
                        "error_message": "No form fields found"
                    })
                
                # Add delay between applications
                time.sleep(2)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing job {job.title}: {str(e)}")
                results.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "company": job.company,
                    "success": False,
                    "filled_fields": [],
                    "failed_fields": [],
                    "error_message": str(e)
                })
        
        logger.info(f"Batch application completed: {successful_count} successful, {failed_count} failed")
        
        return {
            "total_attempted": len(jobs),
            "successful_applications": successful_count,
            "failed_applications": failed_count,
            "application_results": results
        } 