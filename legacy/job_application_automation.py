from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt.chat_agent_executor import create_function_calling_executor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import json
import time
import logging
import re
import os
import platform
from enum import Enum
from dotenv import load_dotenv
import csv
from datetime import datetime
from urllib.parse import urlencode, urlparse, quote
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from serpapi import GoogleSearch

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models for structured data
class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "tel"
    URL = "url"
    TEXTAREA = "textarea"
    SELECT = "select"
    FILE = "file"
    CHECKBOX = "checkbox"
    RADIO = "radio"

class FormField(BaseModel):
    """Model for individual form fields"""
    label: str = Field(..., description="The label or name of the form field")
    field_type: FieldType = Field(..., description="The type of input field")
    required: bool = Field(default=False, description="Whether the field is required")
    placeholder: Optional[str] = Field(None, description="Placeholder text if available")
    options: Optional[List[str]] = Field(None, description="Options for select/radio fields")
    xpath: Optional[str] = Field(None, description="XPath selector for the field")
    
    @field_validator('label')
    @classmethod
    def validate_label(cls, v):
        if not v or not v.strip():
            raise ValueError('Label cannot be empty')
        return v.strip()

class JobApplicationData(BaseModel):
    """Model for job application form data"""
    first_name: Optional[str] = Field(None, description="Applicant's first name")
    last_name: Optional[str] = Field(None, description="Applicant's last name")
    email: Optional[str] = Field(None, description="Applicant's email address")
    phone: Optional[str] = Field(None, description="Applicant's phone number")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio or website URL")
    resume_file: Optional[str] = Field(None, description="Path to resume file")
    cover_letter: Optional[str] = Field(None, description="Cover letter text")
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Any additional fields")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class JobFormExtractionResult(BaseModel):
    """Model for the result of form extraction"""
    url: str = Field(..., description="The URL that was processed")
    form_fields: List[FormField] = Field(..., description="List of detected form fields")
    success: bool = Field(..., description="Whether extraction was successful")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    suggested_data: Optional[JobApplicationData] = Field(None, description="Suggested dummy data for the form")

class FormFillResult(BaseModel):
    """Model for the result of form filling"""
    success: bool = Field(..., description="Whether form filling was successful")
    filled_fields: List[str] = Field(default_factory=list, description="List of successfully filled fields")
    failed_fields: List[str] = Field(default_factory=list, description="List of fields that failed to fill")
    error_message: Optional[str] = Field(None, description="Error message if filling failed")

# New Models for Job Search
class JobPosition(BaseModel):
    """Model for individual job positions"""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    url: str = Field(..., description="Application URL")
    job_board: str = Field(..., description="Job board source (e.g., Ashby, Indeed, etc.)")
    posted_date: Optional[str] = Field(None, description="When the job was posted")
    salary_range: Optional[str] = Field(None, description="Salary information if available")
    job_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract, etc.")
    remote_option: Optional[str] = Field(None, description="Remote, Hybrid, On-site")
    description_snippet: Optional[str] = Field(None, description="Brief job description")
    
class JobSearchResult(BaseModel):
    """Model for job search results"""
    search_query: str = Field(..., description="The search query used")
    total_jobs_found: int = Field(..., description="Total number of jobs found")
    jobs: List[JobPosition] = Field(..., description="List of job positions")
    search_timestamp: str = Field(..., description="When the search was performed")
    success: bool = Field(..., description="Whether the search was successful")
    error_message: Optional[str] = Field(None, description="Error message if search failed")

class BatchApplicationResult(BaseModel):
    """Model for batch application results"""
    total_attempted: int = Field(..., description="Total applications attempted")
    successful_applications: int = Field(..., description="Number of successful applications")
    failed_applications: int = Field(..., description="Number of failed applications")
    application_results: List[Dict[str, Any]] = Field(..., description="Detailed results for each application")
    execution_time: float = Field(..., description="Total execution time in seconds")

# TOOL 1: Extract job application form data
@tool
def extract_job_application_form(url: str) -> JobFormExtractionResult:
    """
    Extract form fields from a job application page using Selenium and return structured data.
    
    Args:
        url: The job application URL (e.g., Ashby job posting)
        
    Returns:
        JobFormExtractionResult with detected form fields and suggested data
    """
    logger.info(f"Starting form extraction for URL: {url}")
    
    # Configure Chrome options with enhanced anti-detection
    options = Options()
    # Removed headless mode so you can see the browser
    
    # Enhanced anti-detection measures
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Performance and stability
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    
    # Window and display
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # More realistic user agent
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Additional anti-detection
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument('--disable-sync')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-component-update')
    options.add_argument('--disable-domain-reliability')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-ios-password-suggestions')
    
    try:
        # Use undetected-chromedriver for anti-bot
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 30)
        
        # Navigate to URL
        logger.info(f"Navigating to URL: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page load
        
        # Wait for page to be ready
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        time.sleep(3)  # Additional wait for dynamic content
        
        form_fields = []
        
        # Enhanced form field detection
        field_selectors = [
            # Input fields
            "//input[@type='text']",
            "//input[@type='email']", 
            "//input[@type='tel']",
            "//input[@type='url']",
            "//input[@type='file']",
            "//textarea",
            "//select",
            # Ashby specific
            "//div[contains(@class, 'form-field')]//input",
            "//div[contains(@class, 'form-field')]//textarea",
            "//div[contains(@class, 'form-field')]//select",
        ]
        
        for selector in field_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        # Extract field information
                        field_info = extract_field_info(driver, element)
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
        
        if not unique_fields:
            return JobFormExtractionResult(
                url=url,
                form_fields=[],
                success=False,
                error_message="No form fields detected on the page"
            )
        
        # Generate suggested data using LLM
        logger.info("Processing form elements with LLM...")
        suggested_data = generate_suggested_data(unique_fields)
        
        # Keep browser open for a moment so you can see the results
        logger.info("Extraction complete! Keeping browser open for 3 seconds...")
        time.sleep(3)  # Reduced from 10 to 3 seconds
        
        return JobFormExtractionResult(
            url=url,
            form_fields=unique_fields,
            success=True,
            suggested_data=suggested_data
        )
        
    except Exception as e:
        logger.error(f"Error during form extraction: {str(e)}")
        return JobFormExtractionResult(
            url=url,
            form_fields=[],
            success=False,
            error_message=str(e)
        )
    finally:
        try:
            logger.info("Closing browser...")
            driver.quit()
        except:
            pass

def extract_field_info(driver, element) -> Optional[FormField]:
    """Extract information about a form field element"""
    try:
        # Get field type
        field_type = element.get_attribute("type") or element.tag_name
        if field_type == "input":
            field_type = "text"  # default for input without type
        
        # Get label
        label = None
        
        # Try different methods to find label
        element_id = element.get_attribute("id")
        if element_id:
            try:
                label_element = driver.find_element(By.XPATH, f"//label[@for='{element_id}']")
                label = label_element.text.strip()
            except:
                pass
        
        if not label:
            # Try to find label in parent container
            try:
                parent = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'form-field') or contains(@class, 'field')][1]")
                label_element = parent.find_element(By.TAG_NAME, "label")
                label = label_element.text.strip()
            except:
                pass
        
        if not label:
            # Use placeholder or aria-label as fallback
            label = element.get_attribute("placeholder") or element.get_attribute("aria-label")
        
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
        xpath = generate_xpath_for_element(driver, element)
        
        return FormField(
            label=label,
            field_type=FieldType(field_type) if field_type in [e.value for e in FieldType] else FieldType.TEXT,
            required=required,
            placeholder=placeholder,
            options=options,
            xpath=xpath
        )
        
    except Exception as e:
        logger.warning(f"Error extracting field info: {str(e)}")
        return None

def generate_xpath_for_element(driver, element) -> str:
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

def generate_suggested_data(form_fields: List[FormField]) -> JobApplicationData:
    """Generate suggested dummy data based on detected form fields"""
    try:
        model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
        
        # Extract just the field labels for cleaner prompt
        field_labels = [field.label for field in form_fields]
        
        prompt = f"""
        Generate realistic dummy data for these job application form fields:
        
        {json.dumps(field_labels, indent=2)}
        
        Return ONLY a valid JSON object mapping each field label to appropriate dummy data:
        - For "Name": Use a full name like "Emily Johnson"
        - For email fields: Use professional email
        - For online profiles/LinkedIn: Use realistic URLs
        - For salary: Use realistic numbers with $ symbol
        - For essay/textarea questions: Provide thorough, professional responses with exactly 2 sentences. Make them detailed and compelling.
        - For yes/no questions: Answer "Yes" or "No"
        - For speed/numbers: Use realistic values
        
        For essay questions, provide detailed, thoughtful responses that demonstrate:
        - Professional experience and skills
        - Genuine enthusiasm and motivation
        - Specific examples and concrete details
        - Strong communication abilities
        
        Use the EXACT field labels as keys. Example:
        {{
            "Name": "Emily Johnson",
            "Email": "emily.johnson@email.com",
            "Share any online profiles (Linkedin, Github, Website, Portfolio, Twitter, etc.)": "https://linkedin.com/in/emilyjohnson, https://github.com/emilyjohnson",
            "Desired Annual Salary (or OTE if Sales)": "$85,000",
            "How good are you at what you do? And what does being great mean to you?": "I consistently exceed performance targets and have led three successful product launches that increased company revenue by 40%. Being great means not only delivering exceptional results but also mentoring teammates and continuously learning new skills to stay ahead of industry trends."
        }}
        
        Respond with ONLY the JSON object, no other text.
        """
        
        response = model.invoke([HumanMessage(content=prompt)])
        logger.info(f"LLM Raw response: {response.content}")
        
        # Clean the response - remove any markdown formatting
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            data_dict = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Trying to clean content: {content}")
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data_dict = json.loads(json_match.group())
            else:
                logger.error("Could not extract JSON from response")
                return create_fallback_data()
        
        # Create a comprehensive mapping of all data for form filling
        # This includes both the standard JobApplicationData fields and all additional form fields
        all_form_data = {}
        
        # Standard field mappings for JobApplicationData
        mapped_data = {}
        
        for key, value in data_dict.items():
            key_lower = key.lower()
            
            # Map to standard JobApplicationData fields
            if "name" in key_lower and "first" not in key_lower and "last" not in key_lower:
                # Split full name into first and last
                name_parts = str(value).split()
                if len(name_parts) >= 2:
                    mapped_data["first_name"] = name_parts[0]
                    mapped_data["last_name"] = " ".join(name_parts[1:])
                else:
                    mapped_data["first_name"] = str(value)
                
                # IMPORTANT: Store the FULL name for the "Name" field
                all_form_data["Name"] = str(value)  # Full name like "Emily Johnson"
                all_form_data["first_name"] = mapped_data.get("first_name", "")
                all_form_data["last_name"] = mapped_data.get("last_name", "")
            elif "email" in key_lower:
                mapped_data["email"] = value
                all_form_data["Email"] = value
                all_form_data["email"] = value
            elif "profiles" in key_lower or "linkedin" in key_lower:
                mapped_data["linkedin_url"] = value
                all_form_data[key] = value  # Use exact field name
                all_form_data["linkedin_url"] = value
            elif "portfolio" in key_lower or "website" in key_lower:
                mapped_data["portfolio_url"] = value
                all_form_data[key] = value
                all_form_data["portfolio_url"] = value
            elif "phone" in key_lower:
                mapped_data["phone"] = value
                all_form_data[key] = value
                all_form_data["phone"] = value
            elif "resume" in key_lower:
                mapped_data["resume_file"] = value
                # Skip resume fields in all_form_data since we don't want to fill them
                logger.info(f"Skipping resume field: {key}")
            elif "cover" in key_lower:
                mapped_data["cover_letter"] = value
                all_form_data[key] = value
                all_form_data["cover_letter"] = value
            else:
                # Add to additional_info for JobApplicationData
                if "additional_info" not in mapped_data:
                    mapped_data["additional_info"] = {}
                mapped_data["additional_info"][key] = value
                
                # Also add to all_form_data for direct field matching
                all_form_data[key] = value
        
        # Create JobApplicationData object
        job_data = JobApplicationData(**mapped_data)
        
        # Store the comprehensive form data in additional_info for access during form filling
        if not job_data.additional_info:
            job_data.additional_info = {}
        job_data.additional_info.update(all_form_data)
        
        return job_data
        
    except Exception as e:
        logger.error(f"Error generating suggested data: {str(e)}")
        return create_fallback_data()

def create_fallback_data() -> JobApplicationData:
    """Create fallback dummy data if LLM fails"""
    return JobApplicationData(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-123-4567",
        linkedin_url="https://linkedin.com/in/johndoe",
        additional_info={
            "Name": "John Doe",
            "Email": "john.doe@example.com",
            "Share any online profiles (Linkedin, Github, Website, Portfolio, Twitter, etc.)": "https://linkedin.com/in/johndoe",
            "What is your primary language": "English",
            "Desired Annual Salary (or OTE if Sales)": "$75,000",
            "Are you looking for full-time": "Yes",
            "What is your typing speed?": "70 WPM",
            "How good are you at what you do? And what does being great mean to you?": "I consistently deliver high-quality work and have successfully managed multiple projects simultaneously, earning recognition from both clients and management. Being great means not only meeting expectations but also proactively identifying opportunities for improvement and helping my team achieve collective success.",
            "We have an async culture here. How do you feel about it?": "I thrive in async environments as they allow me to work during my most productive hours and create thoughtful, well-structured communications. This approach has helped me maintain excellent work-life balance while delivering consistent results across different time zones.",
            "Travel is a big part of our company culture. Could you share some of your favorite travel experiences?": "I've had amazing experiences backpacking through Southeast Asia, where I learned to adapt quickly to new cultures and communicate effectively despite language barriers. These travels taught me resilience and cultural sensitivity, skills that prove invaluable when working with diverse teams."
        }
    )

# TOOL 2: Fill out job application form
@tool  
def fill_job_application_form(url: str, form_data: dict) -> FormFillResult:
    """
    Fill out a job application form using the provided data.
    
    Args:
        url: The job application URL
        form_data: Dictionary containing the form data to fill
        
    Returns:
        FormFillResult with success status and details
    """
    logger.info(f"Starting form filling for URL: {url}")
    
    # Configure Chrome options (visible browser window)
    options = Options()
    # Removed headless mode so you can see the browser
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    filled_fields = []
    failed_fields = []
    filled_elements = set()  # Track elements we've already filled to avoid duplicates
    
    try:
        # Use undetected-chromedriver for anti-bot
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 30)
        
        # Navigate to URL
        logger.info(f"Navigating to URL: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        logger.info("Starting to fill form fields...")
        
        # Prioritize certain fields and avoid conflicts
        priority_fields = []
        regular_fields = []
        
        for field_name, field_value in form_data.items():
            if not field_value:
                continue
            
            # Prioritize exact field names over generic mappings
            if field_name in ["Name", "Email", "Share any online profiles (Linkedin, Github, Website, Portfolio, Twitter, etc.)"]:
                priority_fields.append((field_name, field_value))
            elif field_name not in ["first_name", "last_name", "email", "linkedin_url", "resume_file", "Resume"]:
                # Skip generic mappings if we have exact field names, and skip resume fields
                regular_fields.append((field_name, field_value))
        
        # Process priority fields first
        all_fields_to_process = priority_fields + regular_fields
        
        for field_name, field_value in all_fields_to_process:
            try:
                logger.info(f"Looking for field: {field_name}")
                input_element = find_input_element(driver, field_name, field_value)
                if input_element:
                    # Check if we've already filled this element
                    element_id = input_element.get_attribute('id') or input_element.get_attribute('name') or str(hash(input_element))
                    
                    if element_id in filled_elements:
                        logger.info(f"Skipping {field_name} - element already filled")
                        continue
                    
                    fill_input_field(driver, input_element, field_value)
                    filled_fields.append(field_name)
                    filled_elements.add(element_id)
                    logger.info(f"✅ Successfully filled field: {field_name} with value: {field_value}")
                    # Small delay to see the field being filled
                    time.sleep(0.5)  # Reduced from 1 to 0.5 seconds
                else:
                    failed_fields.append(field_name)
                    logger.warning(f"❌ Could not find element for field: {field_name}")
                    
            except Exception as e:
                failed_fields.append(field_name)
                logger.error(f"❌ Error filling field {field_name}: {str(e)}")
        
        # Keep browser open longer so you can see the results
        logger.info("Form filling complete! Keeping browser open for 5 seconds to review...")
        time.sleep(5)  # Reduced from 15 to 5 seconds
        
        return FormFillResult(
            success=len(filled_fields) > 0,
            filled_fields=filled_fields,
            failed_fields=failed_fields
        )
        
    except Exception as e:
        logger.error(f"Error during form filling: {str(e)}")
        return FormFillResult(
            success=False,
            filled_fields=filled_fields,
            failed_fields=list(form_data.keys()),
            error_message=str(e)
        )
    finally:
        try:
            logger.info("Closing browser...")
            driver.quit()
        except:
            pass

def find_input_element(driver, field_name: str, field_value: str):
    """Find an input element based on field name"""
    field_name_lower = field_name.lower().replace("_", " ")
    
    # Clean field name for better matching - handle apostrophes and special characters
    field_name_clean = field_name_lower.replace("'", "").replace("'", "").replace(""", "").replace(""", "")
    field_name_clean = field_name_clean.replace("?", "").replace("!", "").replace(",", "").replace(".", "")
    
    # Special handling for common field mappings
    field_mappings = {
        "first_name": ["name", "first name", "full name"],
        "last_name": ["last name", "surname"],
        "linkedin_url": ["online profiles", "profiles", "linkedin", "social", "links"],
        "portfolio_url": ["portfolio", "website", "online profiles", "profiles"],
        "phone": ["phone", "telephone", "mobile", "contact"],
        "email": ["email", "e-mail", "email address"],
        "resume_file": ["resume", "cv", "curriculum"],
        "cover_letter": ["cover letter", "cover", "motivation"]
    }
    
    # Get possible field names to search for
    search_terms = [field_name_lower, field_name_clean]
    if field_name in field_mappings:
        search_terms.extend(field_mappings[field_name])
    
    # Add keyword-based search terms for problematic fields
    if "work ethic" in field_name_lower:
        search_terms.extend(["work ethic", "approach to work", "describe your work"])
    if "career plans" in field_name_lower:
        search_terms.extend(["career plans", "how long", "staying with", "next company"])
    if "motivates you" in field_name_lower or "wander" in field_name_lower:
        search_terms.extend(["motivates you", "part of our team", "joining wander", "thrilled"])
    
    # Try different strategies to find the element
    for search_term in search_terms:
        # Escape single quotes for XPath
        search_term_escaped = search_term.replace("'", "&apos;")
        
        strategies = [
            # By exact label text match
            f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]/..//input",
            f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]/..//textarea",
            # By label text with following sibling
            f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]/following-sibling::input",
            f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]/following-sibling::textarea",
            # By placeholder
            f"//input[@placeholder and contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]",
            f"//textarea[@placeholder and contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]",
            # By aria-label
            f"//input[@aria-label and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]",
            f"//textarea[@aria-label and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]",
            # By name attribute
            f"//input[@name and contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]",
            f"//textarea[@name and contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}')]"
        ]
        
        for strategy in strategies:
            try:
                elements = driver.find_elements(By.XPATH, strategy)
                if elements:
                    logger.info(f"Found element for '{field_name}' using search term '{search_term}' with strategy: {strategy}")
                    return elements[0]  # Return first match
            except Exception as e:
                continue
    
    # Try direct field name match (for cases where field_name is the exact label)
    direct_strategies = [
        f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_name_clean}')]/..//input",
        f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_name_clean}')]/..//textarea",
        f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_name_clean}')]/following-sibling::input",
        f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_name_clean}')]/following-sibling::textarea"
    ]
    
    for strategy in direct_strategies:
        try:
            elements = driver.find_elements(By.XPATH, strategy)
            if elements:
                logger.info(f"Found element for '{field_name}' using direct match with strategy: {strategy}")
                return elements[0]
        except Exception as e:
            continue
    
    # Final fallback: Try to find by specific IDs we know are problematic
    fallback_id_strategies = []
    if "work ethic" in field_name_lower:
        fallback_id_strategies.append("//textarea[@id='bf35a96f-931f-4d8a-b618-7e718f297677']")
    if "career plans" in field_name_lower:
        fallback_id_strategies.append("//textarea[@id='46a14898-77af-427f-9961-0ae9330565b8']")
    if "motivates you" in field_name_lower or "wander" in field_name_lower:
        fallback_id_strategies.append("//textarea[@id='8280aedc-c8cc-44b9-bd58-3dcab50e39de']")
    
    for strategy in fallback_id_strategies:
        try:
            elements = driver.find_elements(By.XPATH, strategy)
            if elements:
                logger.info(f"Found element for '{field_name}' using fallback ID strategy: {strategy}")
                return elements[0]
        except Exception as e:
            continue
    
    return None

def fill_input_field(driver, element, value: str):
    """Fill an input field with the given value"""
    try:
        # Clear existing content
        element.clear()
        
        # Handle different input types
        if element.tag_name.lower() == "select":
            select = Select(element)
            try:
                select.select_by_visible_text(value)
            except:
                select.select_by_value(value)
        else:
            # Regular input or textarea
            element.send_keys(str(value))
            
    except Exception as e:
        logger.error(f"Error filling input field: {str(e)}")
        raise

# TOOL 3: Search for QA/SDET jobs across multiple job boards
@tool
def search_qa_jobs(
    job_titles: List[str] = ["QA Engineer", "SDET", "Software Engineer in Test", "QA Automation Engineer"],
    locations: List[str] = ["United States", "Remote"],
    max_results_per_search: int = 50
) -> Dict[str, Any]:
    """
    Search for QA/SDET jobs across multiple job boards including Ashby.
    
    Args:
        job_titles: List of job titles to search for
        locations: List of locations to search in
        max_results_per_search: Maximum number of results per search query
        
    Returns:
        JobSearchResult with found job positions
    """
    logger.info(f"Starting job search for titles: {job_titles} in locations: {locations}")
    
    all_jobs = []
    search_timestamp = datetime.now().isoformat()
    
    # Configure Chrome options for job search
    options = Options()
    # options.add_argument('--headless')  # Disable headless mode for debugging
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Use undetected-chromedriver for anti-bot
        driver = uc.Chrome(options=options)
        
        # Focus only on Ashby job boards using SerpAPI
        job_boards = [
            {
                "name": "Ashby",
                "search_function": search_ashby_jobs_serpapi,
                "enabled": True
            }
        ]
        
        for job_title in job_titles:
            for location in locations:
                logger.info(f"Searching for '{job_title}' in '{location}'")
                
                for board in job_boards:
                    if board["enabled"]:
                        try:
                            logger.info(f"Searching on {board['name']}")
                            if board["search_function"] == search_ashby_jobs_serpapi:
                                # SerpAPI function doesn't need driver
                                jobs = board["search_function"](job_title, location, max_results_per_search // len(job_boards))
                            else:
                                # Browser-based functions need driver
                                jobs = board["search_function"](driver, job_title, location, max_results_per_search // len(job_boards))
                            all_jobs.extend(jobs)
                            time.sleep(2)  # Rate limiting
                        except Exception as e:
                            logger.error(f"Error searching {board['name']}: {str(e)}")
                            continue
        
        # Remove duplicates based on URL
        unique_jobs = []
        seen_urls = set()
        for job in all_jobs:
            if job.url not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job.url)
        
        logger.info(f"Found {len(unique_jobs)} unique jobs after deduplication")
        
        # Save results to CSV
        save_jobs_to_csv(unique_jobs)
        
        # Convert JobPosition objects to dictionaries
        jobs_dict = [job.dict() for job in unique_jobs]
        
        return {
            "search_query": f"Titles: {job_titles}, Locations: {locations}",
            "total_jobs_found": len(unique_jobs),
            "jobs": jobs_dict,
            "search_timestamp": search_timestamp,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error during job search: {str(e)}")
        return {
            "search_query": f"Titles: {job_titles}, Locations: {locations}",
            "total_jobs_found": 0,
            "jobs": [],
            "search_timestamp": search_timestamp,
            "success": False,
            "error_message": str(e)
        }
    finally:
        try:
            driver.quit()
        except:
            pass

def search_indeed_jobs(driver, job_title: str, location: str, max_results: int) -> List[JobPosition]:
    """Search for jobs on Indeed"""
    jobs = []
    try:
        # Construct Indeed search URL
        params = {
            'q': job_title,
            'l': location,
            'sort': 'date',
            'fromage': '7'  # Last 7 days
        }
        indeed_url = f"https://www.indeed.com/jobs?{urlencode(params)}"
        
        logger.info(f"Searching Indeed: {indeed_url}")
        driver.get(indeed_url)
        time.sleep(5)  # Give more time for page to load
        
        # Look for job cards with more generic selectors
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-jk]")
        
        if not job_cards:
            # Try alternative selector
            job_cards = driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon")
        
        logger.info(f"Found {len(job_cards)} job cards on Indeed")
        
        for i, job_card in enumerate(job_cards[:max_results]):
            try:
                # Try to get job title
                title_elements = job_card.find_elements(By.CSS_SELECTOR, "h2 a[data-jk]")
                if not title_elements:
                    title_elements = job_card.find_elements(By.CSS_SELECTOR, "h2 a")
                
                if title_elements:
                    title = title_elements[0].get_attribute('title') or title_elements[0].text
                    job_url = title_elements[0].get_attribute('href')
                    
                    # Try to get company name
                    company_elements = job_card.find_elements(By.CSS_SELECTOR, "[data-testid='company-name']")
                    if not company_elements:
                        company_elements = job_card.find_elements(By.CSS_SELECTOR, ".companyName")
                    
                    company = company_elements[0].text if company_elements else "Unknown Company"
                    
                    # Try to get location
                    location_elements = job_card.find_elements(By.CSS_SELECTOR, "[data-testid='job-location']")
                    if not location_elements:
                        location_elements = job_card.find_elements(By.CSS_SELECTOR, ".companyLocation")
                    
                    job_location = location_elements[0].text if location_elements else location
                    
                    # Try to get salary
                    salary = None
                    salary_elements = job_card.find_elements(By.CSS_SELECTOR, "[data-testid='salary-snippet']")
                    if salary_elements:
                        salary = salary_elements[0].text
                    
                    # Try to get snippet
                    snippet = None
                    snippet_elements = job_card.find_elements(By.CSS_SELECTOR, "[data-testid='job-snippet']")
                    if snippet_elements:
                        snippet = snippet_elements[0].text[:200] + "..." if len(snippet_elements[0].text) > 200 else snippet_elements[0].text
                    
                    if title and company and job_url:
                        jobs.append(JobPosition(
                            title=title,
                            company=company,
                            location=job_location,
                            url=job_url,
                            job_board="Indeed",
                            salary_range=salary,
                            description_snippet=snippet
                        ))
                        logger.info(f"Found job: {title} at {company}")
                    
            except Exception as e:
                logger.warning(f"Error parsing Indeed job {i}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error searching Indeed jobs: {str(e)}")
    
    logger.info(f"Indeed search completed: {len(jobs)} jobs found")
    return jobs

def search_ashby_jobs(driver, job_title: str, location: str, max_results: int) -> List[JobPosition]:
    """Search for jobs on Ashby job boards"""
    jobs = []
    try:
        logger.info(f"Searching Ashby for '{job_title}' in '{location}'")
        
        # Multiple search strategies for Ashby jobs
        search_strategies = [
            # Strategy 1: Direct Google search for Ashby job boards
            f'site:ashbyhq.com "{job_title}"',
            f'site:jobs.ashbyhq.com "{job_title}"',
            
            # Strategy 2: Search with location
            f'site:ashbyhq.com "{job_title}" "{location}"',
            f'site:jobs.ashbyhq.com "{job_title}" "{location}"',
            
            # Strategy 3: Search for QA/SDET specific terms
            f'site:ashbyhq.com "QA Engineer" OR "SDET" OR "Software Engineer in Test"',
            f'site:jobs.ashbyhq.com "QA Engineer" OR "SDET" OR "Software Engineer in Test"'
        ]
        
        seen_urls = set()
        
        for strategy in search_strategies:
            if len(jobs) >= max_results:
                break
                
            try:
                google_url = f"https://www.google.com/search?q={quote(strategy)}"
                logger.info(f"Trying search strategy: {strategy}")
                logger.info(f"Search URL: {google_url}")
                
                driver.get(google_url)
                time.sleep(3)
                
                # Get search results - try multiple selectors for Google search results
                search_results = []
                selectors_to_try = [
                    "div.g",  # Old selector
                    "div[data-sokoban-container]",  # Newer selector
                    "div[jscontroller]",  # Another common selector
                    "div[data-ved]",  # Results with data-ved attribute
                    "div[jsname]",  # Results with jsname attribute
                    "div[data-hveid]",  # Another Google result identifier
                    "div[data-ved] a[href]",  # Direct links in results
                    "div[jscontroller] a[href]",  # Links in jscontroller divs
                ]
                
                for selector in selectors_to_try:
                    results = driver.find_elements(By.CSS_SELECTOR, selector)
                    if results:
                        logger.info(f"Found {len(results)} results with selector: {selector}")
                        search_results = results
                        break
                
                # If still no results, try a broader approach
                if not search_results:
                    # Look for any links that might be search results
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    search_results = [link for link in all_links if link.get_attribute('href') and 'ashbyhq.com' in link.get_attribute('href')]
                    logger.info(f"Found {len(search_results)} Ashby links using broad search")
                
                for result in search_results:
                    if len(jobs) >= max_results:
                        break
                        
                    try:
                        # Handle different result structures
                        if result.tag_name == 'a':
                            # Result is already a link
                            url = result.get_attribute('href')
                        else:
                            # Result is a container, find the link inside
                            link_element = result.find_element(By.CSS_SELECTOR, "a")
                            url = link_element.get_attribute('href')
                        
                        # Check if it's an Ashby job URL
                        if url and ('ashbyhq.com' in url or 'jobs.ashbyhq.com' in url) and '/jobs/' in url:
                            if url in seen_urls:
                                continue
                                
                            seen_urls.add(url)
                            
                            # Get job title
                            try:
                                if result.tag_name == 'a':
                                    # If result is a link, use its text as title
                                    title = result.text.strip()
                                else:
                                    # Look for title in various possible elements
                                    title_selectors = ["h3", "h2", ".LC20lb", "[role='heading']", ".DKV0Md"]
                                    title = None
                                    for selector in title_selectors:
                                        try:
                                            title_element = result.find_element(By.CSS_SELECTOR, selector)
                                            title = title_element.text.strip()
                                            if title:
                                                break
                                        except:
                                            continue
                                    
                                    if not title:
                                        title = job_title  # Fallback
                            except:
                                title = job_title  # Fallback
                            
                            # Extract company name from URL
                            company = extract_company_from_ashby_url(url)
                            
                            # Try to get snippet for more info
                            try:
                                snippet_element = result.find_element(By.CSS_SELECTOR, ".VwiC3b")
                                description_snippet = snippet_element.text[:200] + "..." if len(snippet_element.text) > 200 else snippet_element.text
                            except:
                                description_snippet = None
                            
                            # Check if job title matches our search criteria
                            title_lower = title.lower()
                            job_title_lower = job_title.lower()
                            
                            if (job_title_lower in title_lower or 
                                any(term in title_lower for term in ["qa", "sdet", "test", "automation"]) or
                                "engineer" in title_lower):
                                
                                jobs.append(JobPosition(
                                    title=title,
                                    company=company,
                                    location=location,
                                    url=url,
                                    job_board="Ashby",
                                    description_snippet=description_snippet
                                ))
                                
                                logger.info(f"Found Ashby job: {title} at {company}")
                            
                    except Exception as e:
                        logger.warning(f"Error parsing Ashby job result: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Error with search strategy '{strategy}': {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error searching Ashby jobs: {str(e)}")
    
    logger.info(f"Ashby search completed: {len(jobs)} jobs found")
    return jobs

def search_google_jobs(driver, job_title: str, location: str, max_results: int) -> List[JobPosition]:
    """Search for jobs using Google Jobs"""
    jobs = []
    try:
        # Construct Google Jobs search
        query = f"{job_title} {location} jobs"
        google_jobs_url = f"https://www.google.com/search?q={quote(query)}&ibp=htl;jobs"
        
        driver.get(google_jobs_url)
        time.sleep(3)
        
        # Look for job cards in Google Jobs
        job_cards = driver.find_elements(By.CSS_SELECTOR, "[data-ved] .pE8vnd")
        
        for i, card in enumerate(job_cards[:max_results]):
            try:
                card.click()
                time.sleep(1)
                
                # Extract job details
                title = driver.find_element(By.CSS_SELECTOR, "[role='heading'][aria-level='2']").text
                company = driver.find_element(By.CSS_SELECTOR, ".nJlQNd").text
                job_location = driver.find_element(By.CSS_SELECTOR, ".sMzDkb").text
                
                # Get apply link
                apply_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Apply')]")
                job_url = apply_links[0].get_attribute('href') if apply_links else ""
                
                jobs.append(JobPosition(
                    title=title,
                    company=company,
                    location=job_location,
                    url=job_url,
                    job_board="Google Jobs"
                ))
                
            except Exception as e:
                logger.warning(f"Error parsing Google job {i}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error searching Google Jobs: {str(e)}")
    
    return jobs

def extract_company_from_ashby_url(url: str) -> str:
    """Extract company name from Ashby URL"""
    try:
        # URL format: https://jobs.ashbyhq.com/COMPANY/...
        parts = urlparse(url).path.split('/')
        if len(parts) > 1:
            return parts[1].replace('-', ' ').title()
    except:
        pass
    return "Unknown Company"

def save_jobs_to_csv(jobs: List[JobPosition], filename: str = None):
    """Save job results to CSV file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qa_jobs_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'company', 'location', 'url', 'job_board', 'posted_date', 'salary_range', 'job_type', 'remote_option', 'description_snippet']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'url': job.url,
                    'job_board': job.job_board,
                    'posted_date': job.posted_date,
                    'salary_range': job.salary_range,
                    'job_type': job.job_type,
                    'remote_option': job.remote_option,
                    'description_snippet': job.description_snippet
                })
        
        logger.info(f"Jobs saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving jobs to CSV: {str(e)}")

# TOOL 4: Apply to multiple jobs in batch
@tool
def batch_apply_to_jobs(job_urls: List[str], max_applications: int = 10) -> Dict[str, Any]:
    """
    Apply to multiple jobs in batch using the existing form filling functionality.
    
    Args:
        job_urls: List of job application URLs
        max_applications: Maximum number of applications to attempt
        
    Returns:
        BatchApplicationResult with detailed results
    """
    logger.info(f"Starting batch application to {len(job_urls)} jobs (max: {max_applications})")
    
    start_time = time.time()
    application_results = []
    successful_count = 0
    failed_count = 0
    
    # Limit the number of applications
    urls_to_process = job_urls[:max_applications]
    
    for i, url in enumerate(urls_to_process, 1):
        logger.info(f"Processing application {i}/{len(urls_to_process)}: {url}")
        
        try:
            # Extract form fields
            extraction_result = extract_job_application_form(url)
            
            if extraction_result.success and extraction_result.suggested_data:
                # Fill the form
                form_data = extraction_result.suggested_data.additional_info
                fill_result = fill_job_application_form(url, form_data)
                
                result = {
                    "url": url,
                    "success": fill_result.success,
                    "filled_fields": len(fill_result.filled_fields),
                    "failed_fields": len(fill_result.failed_fields),
                    "error_message": fill_result.error_message
                }
                
                if fill_result.success:
                    successful_count += 1
                    logger.info(f"✅ Successfully applied to {url}")
                else:
                    failed_count += 1
                    logger.warning(f"❌ Failed to apply to {url}")
                    
            else:
                result = {
                    "url": url,
                    "success": False,
                    "filled_fields": 0,
                    "failed_fields": 0,
                    "error_message": extraction_result.error_message or "Failed to extract form fields"
                }
                failed_count += 1
                
            application_results.append(result)
            
            # Rate limiting between applications
            if i < len(urls_to_process):
                logger.info("Waiting 30 seconds before next application...")
                time.sleep(30)
                
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            application_results.append({
                "url": url,
                "success": False,
                "filled_fields": 0,
                "failed_fields": 0,
                "error_message": str(e)
            })
            failed_count += 1
    
    execution_time = time.time() - start_time
    
    # Save results
    save_application_results(application_results)
    
    logger.info(f"Batch application complete: {successful_count} successful, {failed_count} failed")
    
    return {
        "total_attempted": len(urls_to_process),
        "successful_applications": successful_count,
        "failed_applications": failed_count,
        "application_results": application_results,
        "execution_time": execution_time
    }

def save_application_results(results: List[Dict[str, Any]], filename: str = None):
    """Save application results to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"application_results_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": results
            }, f, indent=2)
        
        logger.info(f"Application results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving application results: {str(e)}")

# TOOL 5: Smart job filtering based on criteria
@tool
def filter_jobs_by_criteria(
    jobs: List[Dict[str, Any]],
    required_keywords: List[str] = ["automation", "selenium", "testing"],
    excluded_keywords: List[str] = ["manual testing", "senior", "lead"],
    preferred_companies: List[str] = [],
    remote_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Filter jobs based on specific criteria for QA/SDET positions.
    
    Args:
        jobs: List of job positions as dictionaries
        required_keywords: Keywords that must be present in title or description
        excluded_keywords: Keywords that should not be present
        preferred_companies: List of preferred company names
        remote_only: Whether to include only remote positions
        
    Returns:
        Filtered list of job positions as dictionaries
    """
    filtered_jobs = []
    
    for job in jobs:
        # Combine title and description for keyword searching
        text_to_search = f"{job.get('title', '')} {job.get('description_snippet', '')}".lower()
        
        # Check required keywords
        has_required = any(keyword.lower() in text_to_search for keyword in required_keywords)
        
        # Check excluded keywords
        has_excluded = any(keyword.lower() in text_to_search for keyword in excluded_keywords)
        
        # Check company preference
        preferred_company = not preferred_companies or any(
            company.lower() in job.get('company', '').lower() for company in preferred_companies
        )
        
        # Check remote requirement
        is_remote_ok = not remote_only or (
            job.get('remote_option') and "remote" in job.get('remote_option', '').lower()
        ) or "remote" in job.get('location', '').lower()
        
        # Apply filters
        if has_required and not has_excluded and preferred_company and is_remote_ok:
            filtered_jobs.append(job)
    
    logger.info(f"Filtered {len(jobs)} jobs down to {len(filtered_jobs)} matching criteria")
    return filtered_jobs

def search_ashby_jobs_serpapi(job_title: str, location: str, max_results: int) -> List[JobPosition]:
    """Search for Ashby jobs using SerpAPI (Google Search API)"""
    jobs = []
    
    # Get API key from environment
    api_key = os.getenv('SERPAPI_KEY')
    if not api_key:
        logger.error("SERPAPI_KEY not found in environment variables")
        return jobs
    
    # Multiple search strategies for Ashby jobs
    search_strategies = [
        f'site:ashbyhq.com "{job_title}"',
        f'site:jobs.ashbyhq.com "{job_title}"',
        f'site:ashbyhq.com "{job_title}" "{location}"',
        f'site:jobs.ashbyhq.com "{job_title}" "{location}"',
        f'site:ashbyhq.com "QA Engineer" OR "SDET" OR "Software Engineer in Test"',
        f'site:jobs.ashbyhq.com "QA Engineer" OR "SDET" OR "Software Engineer in Test"'
    ]
    
    seen_urls = set()
    
    for strategy in search_strategies:
        if len(jobs) >= max_results:
            break
            
        try:
            logger.info(f"Trying search strategy: {strategy}")
            
            # Use SerpAPI for Google search
            search = GoogleSearch({
                "q": strategy,
                "api_key": api_key,
                "num": 10  # Number of results per request
            })
            
            results = search.get_dict()
            
            if "organic_results" in results:
                organic_results = results["organic_results"]
                logger.info(f"Found {len(organic_results)} organic results")
                
                for result in organic_results:
                    if len(jobs) >= max_results:
                        break
                        
                    try:
                        url = result.get("link", "")
                        
                        # Check if it's an Ashby job URL
                        if url and ('ashbyhq.com' in url or 'jobs.ashbyhq.com' in url) and '/jobs/' in url:
                            if url in seen_urls:
                                continue
                                
                            seen_urls.add(url)
                            
                            # Get job title
                            title = result.get("title", job_title)
                            
                            # Extract company name from URL
                            company = extract_company_from_ashby_url(url)
                            
                            # Get snippet for more info
                            description_snippet = result.get("snippet", None)
                            
                            # Check if job title matches our search criteria
                            title_lower = title.lower()
                            job_title_lower = job_title.lower()
                            
                            if (job_title_lower in title_lower or 
                                any(term in title_lower for term in ["qa", "sdet", "test", "automation"]) or
                                "engineer" in title_lower):
                                
                                jobs.append(JobPosition(
                                    title=title,
                                    company=company,
                                    location=location,
                                    url=url,
                                    job_board="Ashby",
                                    description_snippet=description_snippet
                                ))
                                
                                logger.info(f"Found Ashby job: {title} at {company}")
                            
                    except Exception as e:
                        logger.warning(f"Error parsing Ashby job result: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.warning(f"Error with search strategy '{strategy}': {str(e)}")
            continue
            
    logger.info(f"Ashby search completed: {len(jobs)} jobs found")
    return jobs

# Update the main execution to include new functionality
if __name__ == "__main__":
    # Set up tools and agent with new functionality
    tools = [
        extract_job_application_form, 
        fill_job_application_form,
        search_qa_jobs,
        batch_apply_to_jobs,
        filter_jobs_by_criteria
    ]
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_function_calling_executor(model, tools)
    
    print("🚀 Starting comprehensive job application automation...")
    print("Available operations:")
    print("1. Search for QA/SDET jobs")
    print("2. Apply to a single job")
    print("3. Batch apply to multiple jobs")
    print("4. Full automation (search + filter + apply)")
    
    # Example: Full automation workflow focused on Ashby job boards
    result = agent.invoke({
        "messages": [
            HumanMessage(content="""
            Please perform the following automated job application workflow:
            
            1. Search for QA Engineer, SDET, Software Engineer in Test, and QA Automation Engineer positions on Ashby job boards
            2. Filter the results to focus on automation and testing roles
            3. Apply to the top 5 most relevant positions
            
            Focus on remote positions and companies that use modern testing frameworks.
            Only search on Ashby job boards for better quality tech job applications.
            """)
        ]
    })
    
    print("\n📋 Agent Result:")
    print(result)
