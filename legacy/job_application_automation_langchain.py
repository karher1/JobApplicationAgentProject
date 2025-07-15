from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain.schema import BaseOutputParser
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
from enum import Enum
from dotenv import load_dotenv
import csv
from datetime import datetime
from urllib.parse import urlencode, urlparse
import requests
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LangChain components
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

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

# LangChain Prompts
FORM_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at analyzing job application forms and extracting structured data. 
    Given a list of form fields, generate appropriate dummy data for testing purposes.
    
    Rules:
    1. Generate realistic but fictional data
    2. For text fields, provide detailed, two-sentence responses
    3. For required fields, always provide data
    4. For optional fields, provide data if it makes sense
    5. Use professional but not overly formal language
    6. Make responses specific to the field context"""),
    ("human", """Analyze these form fields and generate appropriate dummy data:
    
    {form_fields}
    
    Generate the data in JSON format with the following structure:
    {{
        "first_name": "string",
        "last_name": "string", 
        "email": "string",
        "phone": "string",
        "linkedin_url": "string",
        "portfolio_url": "string",
        "cover_letter": "string",
        "additional_info": {{}}
    }}
    
    For any additional fields found, include them in additional_info with appropriate values.""")
])

DATA_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant that generates realistic job application data. 
    Create detailed, professional responses that are appropriate for job applications."""),
    ("human", """Generate data for the field: {field_name}
    Field type: {field_type}
    Required: {required}
    Placeholder: {placeholder}
    
    Provide a detailed, two-sentence response that would be appropriate for this field in a job application.""")
])

# LangChain Chains
form_extraction_chain = LLMChain(
    llm=llm,
    prompt=FORM_EXTRACTION_PROMPT,
    output_parser=JsonOutputParser()
)

data_generation_chain = LLMChain(
    llm=llm,
    prompt=DATA_GENERATION_PROMPT,
    output_parser=StrOutputParser()
)

# Custom LangChain Tools
class FormExtractionTool(BaseTool):
    name = "extract_job_application_form"
    description = "Extract form fields from a job application page using Selenium and return structured data"
    
    def _run(self, url: str) -> JobFormExtractionResult:
        """Extract form fields from a job application page"""
        logger.info(f"Starting form extraction for URL: {url}")
        
        # Configure Chrome options
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        try:
            # Initialize WebDriver
            logger.info("Initializing Chrome WebDriver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 30)
            
            # Navigate to URL
            logger.info(f"Navigating to URL: {url}")
            driver.get(url)
            time.sleep(5)
            
            # Wait for page to be ready
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
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
                            if field_info:
                                form_fields.append(field_info)
                        except Exception as e:
                            logger.warning(f"Error extracting field info: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {e}")
                    continue
            
            driver.quit()
            
            if form_fields:
                # Use LangChain to generate suggested data
                suggested_data = self._generate_suggested_data_with_langchain(form_fields)
                
                return JobFormExtractionResult(
                    url=url,
                    form_fields=form_fields,
                    success=True,
                    suggested_data=suggested_data
                )
            else:
                return JobFormExtractionResult(
                    url=url,
                    form_fields=[],
                    success=False,
                    error_message="No form fields found"
                )
                
        except Exception as e:
            logger.error(f"Error during form extraction: {e}")
            return JobFormExtractionResult(
                url=url,
                form_fields=[],
                success=False,
                error_message=str(e)
            )
    
    def _extract_field_info(self, driver, element) -> Optional[FormField]:
        """Extract detailed information about a form field"""
        try:
            # Get basic attributes
            field_type = element.get_attribute('type') or 'text'
            placeholder = element.get_attribute('placeholder')
            required = element.get_attribute('required') is not None
            
            # Determine field type
            if element.tag_name == 'textarea':
                field_type = 'textarea'
            elif element.tag_name == 'select':
                field_type = 'select'
            elif field_type == 'file':
                field_type = 'file'
            
            # Get label text
            label = self._find_label_for_element(driver, element)
            
            # Get options for select fields
            options = None
            if field_type == 'select':
                options = [option.text for option in element.find_elements(By.TAG_NAME, 'option') if option.text.strip()]
            
            # Generate XPath
            xpath = self._generate_xpath_for_element(driver, element)
            
            return FormField(
                label=label,
                field_type=FieldType(field_type),
                required=required,
                placeholder=placeholder,
                options=options,
                xpath=xpath
            )
            
        except Exception as e:
            logger.warning(f"Error extracting field info: {e}")
            return None
    
    def _find_label_for_element(self, driver, element) -> str:
        """Find the label text for a form element"""
        try:
            # Try to find label by for attribute
            element_id = element.get_attribute('id')
            if element_id:
                label = driver.find_element(By.XPATH, f"//label[@for='{element_id}']")
                if label:
                    return label.text.strip()
            
            # Try to find label by parent or sibling
            parent = element.find_element(By.XPATH, "./..")
            label = parent.find_element(By.TAG_NAME, "label")
            if label:
                return label.text.strip()
            
            # Try to find nearby text
            nearby_text = element.find_element(By.XPATH, "./preceding-sibling::*[1]")
            if nearby_text and nearby_text.text.strip():
                return nearby_text.text.strip()
            
            # Fallback to placeholder or name
            placeholder = element.get_attribute('placeholder')
            if placeholder:
                return placeholder
            
            name = element.get_attribute('name')
            if name:
                return name.replace('_', ' ').title()
            
            return "Unknown Field"
            
        except Exception:
            # Final fallback
            placeholder = element.get_attribute('placeholder')
            if placeholder:
                return placeholder
            return "Unknown Field"
    
    def _generate_xpath_for_element(self, driver, element) -> str:
        """Generate a unique XPath for an element"""
        try:
            return driver.execute_script("""
                function getXPath(element) {
                    if (element.id !== '') {
                        return 'id("' + element.id + '")';
                    }
                    if (element === document.body) {
                        return element.tagName;
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
        except Exception:
            return ""
    
    def _generate_suggested_data_with_langchain(self, form_fields: List[FormField]) -> JobApplicationData:
        """Use LangChain to generate suggested data for form fields"""
        try:
            # Convert form fields to string representation
            fields_str = "\n".join([
                f"- {field.label} ({field.field_type.value}) {'[REQUIRED]' if field.required else '[OPTIONAL]'}"
                for field in form_fields
            ])
            
            # Use LangChain chain to generate data
            result = form_extraction_chain.invoke({"form_fields": fields_str})
            
            # Parse the result and create JobApplicationData
            if isinstance(result, dict):
                return JobApplicationData(**result)
            else:
                # Fallback to default data
                return self._create_fallback_data()
                
        except Exception as e:
            logger.error(f"Error generating data with LangChain: {e}")
            return self._create_fallback_data()
    
    def _create_fallback_data(self) -> JobApplicationData:
        """Create fallback data when LangChain generation fails"""
        return JobApplicationData(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="(555) 123-4567",
            linkedin_url="https://linkedin.com/in/johndoe",
            portfolio_url="https://johndoe.dev",
            cover_letter="I am excited to apply for this position and believe my skills and experience make me an excellent candidate for this role. I am passionate about technology and always eager to learn new skills and take on challenging projects.",
            additional_info={}
        )

class FormFillingTool(BaseTool):
    name = "fill_job_application_form"
    description = "Fill out a job application form with provided data using Selenium"
    
    def _run(self, url: str, form_data: dict) -> FormFillResult:
        """Fill out a job application form with the provided data"""
        logger.info(f"Starting form filling for URL: {url}")
        
        # Configure Chrome options
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        try:
            # Initialize WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 30)
            
            # Navigate to URL
            driver.get(url)
            time.sleep(5)
            
            # Wait for page to be ready
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            time.sleep(3)
            
            filled_fields = []
            failed_fields = []
            
            # Fill each field
            for field_name, field_value in form_data.items():
                if field_value is None or field_value == "":
                    continue
                    
                try:
                    success = self._fill_field(driver, field_name, str(field_value))
                    if success:
                        filled_fields.append(field_name)
                        logger.info(f"Successfully filled {field_name}")
                    else:
                        failed_fields.append(field_name)
                        logger.warning(f"Failed to fill {field_name}")
                except Exception as e:
                    failed_fields.append(field_name)
                    logger.error(f"Error filling {field_name}: {e}")
            
            driver.quit()
            
            success = len(filled_fields) > 0
            return FormFillResult(
                success=success,
                filled_fields=filled_fields,
                failed_fields=failed_fields
            )
            
        except Exception as e:
            logger.error(f"Error during form filling: {e}")
            return FormFillResult(
                success=False,
                failed_fields=list(form_data.keys()),
                error_message=str(e)
            )
    
    def _fill_field(self, driver, field_name: str, field_value: str) -> bool:
        """Fill a specific field on the form"""
        try:
            # Try multiple strategies to find the field
            element = self._find_input_element(driver, field_name, field_value)
            if element:
                self._fill_input_field(driver, element, field_value)
                return True
            return False
        except Exception as e:
            logger.error(f"Error filling field {field_name}: {e}")
            return False
    
    def _find_input_element(self, driver, field_name: str, field_value: str):
        """Find the input element for a given field name"""
        # Strategy 1: Direct name/id match
        selectors = [
            f"//input[@name='{field_name}']",
            f"//input[@id='{field_name}']",
            f"//textarea[@name='{field_name}']",
            f"//textarea[@id='{field_name}']",
            f"//select[@name='{field_name}']",
            f"//select[@id='{field_name}']"
        ]
        
        for selector in selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                if element.is_displayed() and element.is_enabled():
                    return element
            except NoSuchElementException:
                continue
        
        # Strategy 2: Label-based search
        label_selectors = [
            f"//label[contains(text(), '{field_name}')]//following-sibling::input",
            f"//label[contains(text(), '{field_name}')]//following-sibling::textarea",
            f"//label[contains(text(), '{field_name}')]//following-sibling::select",
            f"//label[contains(text(), '{field_name}')]/input",
            f"//label[contains(text(), '{field_name}')]/textarea",
            f"//label[contains(text(), '{field_name}')]/select"
        ]
        
        for selector in label_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                if element.is_displayed() and element.is_enabled():
                    return element
            except NoSuchElementException:
                continue
        
        # Strategy 3: Placeholder-based search
        placeholder_selectors = [
            f"//input[@placeholder='{field_name}']",
            f"//textarea[@placeholder='{field_name}']"
        ]
        
        for selector in placeholder_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                if element.is_displayed() and element.is_enabled():
                    return element
            except NoSuchElementException:
                continue
        
        # Strategy 4: Generic field type matching
        field_mappings = {
            'first_name': ['//input[@type="text"][1]', '//input[contains(@placeholder, "first")]'],
            'last_name': ['//input[@type="text"][2]', '//input[contains(@placeholder, "last")]'],
            'email': ['//input[@type="email"]', '//input[contains(@placeholder, "email")]'],
            'phone': ['//input[@type="tel"]', '//input[contains(@placeholder, "phone")]'],
            'linkedin_url': ['//input[@type="url"]', '//input[contains(@placeholder, "linkedin")]'],
            'portfolio_url': ['//input[@type="url"]', '//input[contains(@placeholder, "portfolio")]'],
            'cover_letter': ['//textarea[1]', '//textarea[contains(@placeholder, "cover")]']
        }
        
        if field_name in field_mappings:
            for selector in field_mappings[field_name]:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        return element
                except NoSuchElementException:
                    continue
        
        return None
    
    def _fill_input_field(self, driver, element, value: str):
        """Fill an input field with the given value"""
        try:
            # Clear the field first
            element.clear()
            time.sleep(0.5)
            
            # Fill the field
            element.send_keys(value)
            time.sleep(0.5)
            
            # Trigger change event
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error filling input field: {e}")
            raise

# Create LangChain Agent
tools = [FormExtractionTool(), FormFillingTool()]

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant that helps automate job applications. 
    You can extract form fields from job application pages and fill them with appropriate data.
    
    Available tools:
    - extract_job_application_form: Extract form fields from a job application URL
    - fill_job_application_form: Fill out a job application form with provided data
    
    Always use the tools to perform actions. Never make up information."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Main execution function
def main():
    """Main function to demonstrate the LangChain-based job application automation"""
    print("🤖 LangChain Job Application Automation")
    print("=" * 50)
    
    # Example usage
    url = input("Enter job application URL: ").strip()
    
    if not url:
        print("No URL provided. Exiting.")
        return
    
    try:
        # Step 1: Extract form fields
        print("\n📋 Step 1: Extracting form fields...")
        extraction_result = agent_executor.invoke({
            "input": f"Extract form fields from this job application URL: {url}"
        })
        
        print(f"Extraction result: {extraction_result}")
        
        # Step 2: Fill the form (if extraction was successful)
        if "extract_job_application_form" in str(extraction_result):
            print("\n✍️ Step 2: Filling the form...")
            fill_result = agent_executor.invoke({
                "input": f"Fill the job application form at {url} with appropriate test data"
            })
            
            print(f"Fill result: {fill_result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 