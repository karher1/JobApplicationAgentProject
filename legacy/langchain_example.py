#!/usr/bin/env python3
"""
LangChain Framework Integration Example

This example demonstrates how to use LangChain's framework components
with the job application automation tools.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import logging

# Load environment variables
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

# Pydantic Models for LangChain
class JobApplicationRequest(BaseModel):
    """Model for job application requests"""
    url: str = Field(..., description="Job application URL")
    job_title: str = Field(..., description="Job title being applied for")
    company: str = Field(..., description="Company name")
    custom_data: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom form data")

class ApplicationResult(BaseModel):
    """Model for application results"""
    success: bool = Field(..., description="Whether application was successful")
    filled_fields: List[str] = Field(default_factory=list, description="Fields that were filled")
    failed_fields: List[str] = Field(default_factory=list, description="Fields that failed")
    message: str = Field(..., description="Result message")

# LangChain Prompts
FORM_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at analyzing job application forms and determining the best approach for filling them.
    
    Given a job application URL and context, provide recommendations for:
    1. What data should be used for each field type
    2. How to handle special requirements
    3. Any potential issues to watch out for
    
    Be specific and actionable in your recommendations."""),
    ("human", """Analyze this job application:
    
    URL: {url}
    Job Title: {job_title}
    Company: {company}
    
    Provide recommendations for filling out this application form.""")
])

DATA_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant that generates realistic job application data.
    
    Create professional, detailed responses that are appropriate for job applications.
    Each response should be 2-3 sentences and specific to the field context."""),
    ("human", """Generate data for the field: {field_name}
    Field type: {field_type}
    Job context: {job_context}
    
    Provide a detailed, professional response appropriate for this field.""")
])

# LangChain Chains
form_analysis_chain = LLMChain(
    llm=llm,
    prompt=FORM_ANALYSIS_PROMPT,
    output_parser=StrOutputParser()
)

data_generation_chain = LLMChain(
    llm=llm,
    prompt=DATA_GENERATION_PROMPT,
    output_parser=StrOutputParser()
)

# Custom LangChain Tools
class FormAnalysisTool(BaseTool):
    name = "analyze_job_form"
    description = "Analyze a job application form and provide recommendations"
    
    def _run(self, url: str, job_title: str, company: str) -> str:
        """Analyze a job application form"""
        try:
            result = form_analysis_chain.invoke({
                "url": url,
                "job_title": job_title,
                "company": company
            })
            return result
        except Exception as e:
            logger.error(f"Error analyzing form: {e}")
            return f"Error analyzing form: {str(e)}"

class DataGenerationTool(BaseTool):
    name = "generate_field_data"
    description = "Generate appropriate data for a specific form field"
    
    def _run(self, field_name: str, field_type: str, job_context: str) -> str:
        """Generate data for a specific field"""
        try:
            result = data_generation_chain.invoke({
                "field_name": field_name,
                "field_type": field_type,
                "job_context": job_context
            })
            return result
        except Exception as e:
            logger.error(f"Error generating data: {e}")
            return f"Error generating data: {str(e)}"

class JobApplicationTool(BaseTool):
    name = "apply_to_job"
    description = "Apply to a job using the existing automation tools"
    
    def _run(self, url: str, custom_data: Optional[Dict[str, str]] = None) -> ApplicationResult:
        """Apply to a job using the existing automation"""
        try:
            # Import the existing tools
            from job_application_automation import extract_job_application_form, fill_job_application_form
            
            # Step 1: Extract form fields
            logger.info(f"Extracting form fields from {url}")
            extraction_result = extract_job_application_form.invoke({"url": url})
            
            if not extraction_result.success:
                return ApplicationResult(
                    success=False,
                    message=f"Failed to extract form: {extraction_result.error_message}"
                )
            
            # Step 2: Prepare form data
            form_data = {}
            if extraction_result.suggested_data:
                form_data = extraction_result.suggested_data.model_dump()
            
            # Override with custom data if provided
            if custom_data:
                form_data.update(custom_data)
            
            # Step 3: Fill the form
            logger.info(f"Filling form with {len(form_data)} fields")
            fill_result = fill_job_application_form.invoke({
                "url": url,
                "form_data": form_data
            })
            
            return ApplicationResult(
                success=fill_result.success,
                filled_fields=fill_result.filled_fields,
                failed_fields=fill_result.failed_fields,
                message=f"Application {'successful' if fill_result.success else 'failed'}"
            )
            
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            return ApplicationResult(
                success=False,
                message=f"Error applying to job: {str(e)}"
            )

# Create LangChain Agent
tools = [FormAnalysisTool(), DataGenerationTool(), JobApplicationTool()]

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant that helps automate job applications using LangChain.
    
    Available tools:
    - analyze_job_form: Analyze a job application form and provide recommendations
    - generate_field_data: Generate appropriate data for specific form fields
    - apply_to_job: Apply to a job using automation tools
    
    Always use the tools to perform actions. Provide helpful guidance and recommendations."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Example usage functions
def analyze_job_application(url: str, job_title: str, company: str):
    """Analyze a job application using LangChain"""
    print(f"🔍 Analyzing job application for {job_title} at {company}")
    
    result = agent_executor.invoke({
        "input": f"Analyze the job application form at {url} for a {job_title} position at {company}. Provide recommendations for filling it out."
    })
    
    print("Analysis Result:")
    print(result["output"])
    return result

def generate_custom_data(field_name: str, field_type: str, job_context: str):
    """Generate custom data for a field using LangChain"""
    print(f"✍️ Generating data for {field_name} ({field_type})")
    
    result = agent_executor.invoke({
        "input": f"Generate appropriate data for a {field_type} field named '{field_name}' in the context of {job_context}."
    })
    
    print("Generated Data:")
    print(result["output"])
    return result

def apply_to_job_with_langchain(url: str, job_title: str, company: str, custom_data: Dict[str, str] = None):
    """Apply to a job using LangChain framework"""
    print(f"🚀 Applying to {job_title} position at {company}")
    
    # First analyze the form
    analysis_result = analyze_job_application(url, job_title, company)
    
    # Then apply with custom data
    apply_input = f"Apply to the job at {url} for {job_title} position at {company}"
    if custom_data:
        apply_input += f" with custom data: {custom_data}"
    
    result = agent_executor.invoke({
        "input": apply_input
    })
    
    print("Application Result:")
    print(result["output"])
    return result

def main():
    """Main function demonstrating LangChain integration"""
    print("🤖 LangChain Job Application Automation")
    print("=" * 50)
    
    # Example usage
    url = input("Enter job application URL: ").strip()
    job_title = input("Enter job title: ").strip()
    company = input("Enter company name: ").strip()
    
    if not url or not job_title or not company:
        print("Missing required information. Exiting.")
        return
    
    try:
        # Example 1: Analyze the form
        print("\n" + "="*30)
        print("STEP 1: Form Analysis")
        print("="*30)
        analyze_job_application(url, job_title, company)
        
        # Example 2: Generate custom data
        print("\n" + "="*30)
        print("STEP 2: Data Generation")
        print("="*30)
        generate_custom_data("cover_letter", "textarea", f"{job_title} position at {company}")
        
        # Example 3: Apply to the job
        print("\n" + "="*30)
        print("STEP 3: Job Application")
        print("="*30)
        custom_data = {
            "cover_letter": "I am excited to apply for this position and believe my skills make me an excellent candidate."
        }
        apply_to_job_with_langchain(url, job_title, company, custom_data)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 