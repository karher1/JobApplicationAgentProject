import os
import logging
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
from datetime import datetime, date

from src.models.user_profile import (
    WorkExperience, WorkExperienceCreate,
    Education, EducationCreate,
    Skill, UserSkillCreate,
    Resume
)

logger = logging.getLogger(__name__)

class ResumeParsingService:
    """Service for parsing resumes and extracting structured information"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.doc', '.docx', '.txt']
        
    async def parse_resume(self, resume: Resume) -> Dict[str, Any]:
        """Parse a resume file and extract structured information"""
        try:
            # Get file extension
            file_path = Path(resume.file_path)
            file_extension = file_path.suffix.lower()
            
            if file_extension not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Extract text from file
            text_content = await self._extract_text_from_file(file_path, file_extension)
            
            logger.info(f"Extracted text length: {len(text_content) if text_content else 0}")
            if text_content:
                logger.info(f"First 200 chars: {text_content[:200]}")
            
            if not text_content:
                raise ValueError("No text content could be extracted from the resume")
            
            # Parse the extracted text
            parsed_data = await self._parse_text_content(text_content)
            
            return {
                "success": True,
                "extracted_data": parsed_data,
                "text_content": text_content
            }
            
        except Exception as e:
            logger.error(f"Error parsing resume {resume.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_data": None
            }
    
    async def _extract_text_from_file(self, file_path: Path, file_extension: str) -> str:
        """Extract text content from different file formats"""
        try:
            if file_extension == '.txt':
                # Read plain text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_extension == '.pdf':
                # Extract text from PDF
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                        return text
                except ImportError:
                    logger.warning("pdfplumber not available, falling back to simple text extraction")
                    return ""
            
            elif file_extension in ['.doc', '.docx']:
                # Extract text from Word documents
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text
                except ImportError:
                    logger.warning("python-docx not available, falling back to simple text extraction")
                    return ""
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    async def _parse_text_content(self, text_content: str) -> Dict[str, Any]:
        """Parse text content and extract structured information"""
        try:
            # Clean and normalize text
            text = self._clean_text(text_content)
            logger.info(f"Text after cleaning (first 300 chars): {text[:300]}")
            
            # Extract different sections
            skills = self._extract_skills(text)
            work_experience = self._extract_work_experience(text)
            education = self._extract_education(text)
            contact_info = self._extract_contact_info(text)
            
            logger.info(f"Extracted: {len(skills)} skills, {len(work_experience)} work experiences, {len(education)} education entries")
            
            return {
                "skills": skills,
                "work_experience": work_experience,
                "education": education,
                "contact_info": contact_info
            }
            
        except Exception as e:
            logger.error(f"Error parsing text content: {e}")
            return {
                "skills": [],
                "work_experience": [],
                "education": [],
                "contact_info": {}
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove non-printable characters but preserve newlines
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t ')
        # Remove extra spaces (but preserve single newlines)
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove multiple consecutive newlines but keep single ones
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        # Common skill patterns and keywords
        skill_patterns = [
            # Programming languages
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|R|MATLAB)\b',
            # Web technologies
            r'\b(?:HTML|CSS|React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|Laravel|Rails)\b',
            # Databases
            r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Oracle|SQLite|Cassandra|DynamoDB)\b',
            # Cloud platforms
            r'\b(?:AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Jenkins|GitLab)\b',
            # Tools and frameworks
            r'\b(?:Git|Linux|Unix|Agile|Scrum|Jira|Confluence|Slack|Figma|Photoshop)\b'
        ]
        
        skills = set()
        
        # Look for skills section more precisely
        skills_section_match = re.search(r'(?i)(technical\s+skills?|skills?|core\s+competencies?|technologies?)[:\s]*\n(.*?)(?=\n[A-Z\s]+[:\n]|$)', text, re.DOTALL)
        if skills_section_match:
            skills_text = skills_section_match.group(2)
            logger.info(f"Found skills section: {skills_text[:200]}...")
            # Extract skills from bullet points or comma-separated lists
            for line in skills_text.split('\n'):
                line = line.strip()
                if line:
                    # Handle bullet points with colons (e.g., "• Programming Languages: Java, Python")
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            skill_items = re.split(r'[,;•·\-\|]', parts[1])
                            for item in skill_items:
                                skill = item.strip()
                                # Clean up parenthetical information
                                skill = re.sub(r'\([^)]*\)', '', skill).strip()
                                if len(skill) > 1 and len(skill) < 50:  # Reasonable skill name length
                                    skills.add(skill)
                    else:
                        # Handle simple lists
                        skill_items = re.split(r'[,;•·\-\|]', line)
                        for item in skill_items:
                            skill = item.strip()
                            # Clean up parenthetical information
                            skill = re.sub(r'\([^)]*\)', '', skill).strip()
                            if len(skill) > 1 and len(skill) < 50:  # Reasonable skill name length
                                skills.add(skill)
        
        # Extract skills using patterns
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        # Filter and clean skills
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip()
            if len(skill) > 1 and not skill.isdigit():
                cleaned_skills.append(skill)
        
        return list(set(cleaned_skills))[:20]  # Limit to 20 skills
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience from resume text"""
        experiences = []
        
        # Look for experience section
        exp_section_match = re.search(r'(?i)(professional\s+experience|work\s+experience|employment|experience)[:\s]*\n(.*?)(?=\n(?:education|skills|projects|certifications)|$)', text, re.DOTALL)
        logger.info(f"Work experience regex search result: {exp_section_match is not None}")
        
        if exp_section_match:
            exp_text = exp_section_match.group(2)
            
            # Split by job entries (look for "Company:" patterns)
            job_entries = re.split(r'(?=Company:)', exp_text)
            
            logger.info(f"Found {len(job_entries)} job entries")
            for i, entry in enumerate(job_entries):
                logger.info(f"Entry {i+1} length: {len(entry.strip())}")
                if len(entry.strip()) > 50:  # Filter out short entries
                    experience = self._parse_work_experience_entry(entry)
                    if experience:
                        logger.info(f"Successfully parsed experience: {experience['company_name']} - {experience['job_title']}")
                        experiences.append(experience)
                    else:
                        logger.info(f"Failed to parse entry: {entry[:100]}...")
        
        return experiences[:5]  # Limit to 5 most recent experiences
    
    def _parse_work_experience_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single work experience entry"""
        try:
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if len(lines) < 2:
                return None
            
            company_name = ""
            job_title = ""
            
            # Look for Company: and Title: patterns
            for line in lines:
                if line.startswith('Company:'):
                    # Extract company name and dates from the same line
                    company_match = re.search(r'Company:\s*(.+?)(?:\s+([A-Z][a-z]+ \d{4}.*)|$)', line)
                    if company_match:
                        company_name = company_match.group(1).strip()
                elif line.startswith('Title:'):
                    job_title = line.replace('Title:', '').strip()
            
            # If no structured format, try first line approach
            if not company_name and not job_title:
                first_line = lines[0]
                company_match = re.search(r'^([^,\-]+?)(?:\s*[-,]\s*(.+))?$', first_line)
                if company_match:
                    company_name = company_match.group(1).strip()
                    job_title = company_match.group(2).strip() if company_match.group(2) else ""
                    
                    # If job title is empty, try the second line
                    if not job_title and len(lines) > 1:
                        job_title = lines[1]
            
            # Extract dates using improved parsing - prioritize month-year over year-only
            date_pattern = r'(\w+\s+\d{4}|\d{1,2}/\d{2,4}|\d{4})'
            dates = re.findall(date_pattern, entry)
            
            start_date = None
            end_date = None
            is_current = False
            
            if dates:
                # Use the improved date parsing method
                start_date = self._parse_date_string(dates[0])
                if start_date is None:
                    # If parsing fails, keep the original string for now
                    start_date = dates[0]
                    
                if len(dates) > 1:
                    end_date = self._parse_date_string(dates[-1], is_end_date=True)
                    if end_date is None:
                        # If parsing fails, keep the original string for now
                        end_date = dates[-1]
                elif 'present' in entry.lower() or 'current' in entry.lower():
                    is_current = True
            
            # Extract description (everything after dates/title)
            description_lines = []
            for line in lines[2:]:
                if not re.search(date_pattern, line):
                    description_lines.append(line)
            
            description = '\n'.join(description_lines) if description_lines else ""
            
            # Convert date objects back to strings for JSON serialization
            from datetime import date
            start_date_str = start_date.isoformat() if isinstance(start_date, date) else start_date
            end_date_str = end_date.isoformat() if isinstance(end_date, date) else end_date
            
            return {
                "company_name": company_name,
                "job_title": job_title,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "is_current": is_current,
                "description": description,
                "achievements": [],
                "technologies_used": []
            }
            
        except Exception as e:
            logger.error(f"Error parsing work experience entry: {e}")
            return None
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education from resume text"""
        education_entries = []
        
        # Look for education section (might be at the end of document)
        edu_section_match = re.search(r'(?i)(education|academic\s+background|qualifications?)[:\s]*\n(.*?)$', text, re.DOTALL)
        
        if edu_section_match:
            edu_text = edu_section_match.group(2)
            
            # Split by institution entries
            edu_entries = re.split(r'\n(?=[A-Z][^\n]*(?:\b(?:University|College|School|Institute|Academy|Seminary)\b|,|\n))', edu_text)
            
            for entry in edu_entries:
                if len(entry.strip()) > 20:  # Filter out short entries
                    education = self._parse_education_entry(entry)
                    if education:
                        education_entries.append(education)
        
        return education_entries[:3]  # Limit to 3 education entries
    
    def _parse_education_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single education entry"""
        try:
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if not lines:
                return None
            
            # First line usually contains institution
            institution_name = lines[0]
            
            # Look for degree information
            degree = ""
            field_of_study = ""
            gpa = None
            
            for line in lines:
                # Check for degree patterns
                degree_match = re.search(r'\b(?:Bachelor|Master|PhD|B\.?[AS]\.?|M\.?[AS]\.?|B\.?Sc\.?|M\.?Sc\.?|MBA|PhD|Doctorate|Associate)\b.*', line, re.IGNORECASE)
                if degree_match and not degree:
                    degree = degree_match.group(0)
                
                # Check for GPA
                gpa_match = re.search(r'GPA:?\s*(\d+\.?\d*)', line, re.IGNORECASE)
                if gpa_match:
                    try:
                        gpa = float(gpa_match.group(1))
                    except ValueError:
                        pass
            
            # Extract dates using improved parsing - prioritize month-year over year-only
            date_pattern = r'(\w+\s+\d{4}|\d{1,2}/\d{2,4}|\d{4})'
            dates = re.findall(date_pattern, entry)
            
            start_date = None
            end_date = None
            is_current = False
            
            if dates:
                # Use the improved date parsing method
                start_date = self._parse_date_string(dates[0])
                if len(dates) > 1:
                    end_date = self._parse_date_string(dates[-1], is_end_date=True)
                elif 'present' in entry.lower() or 'current' in entry.lower():
                    is_current = True
            
            # Convert date objects back to strings for JSON serialization
            from datetime import date
            start_date_str = start_date.isoformat() if isinstance(start_date, date) else start_date
            end_date_str = end_date.isoformat() if isinstance(end_date, date) else end_date
            
            return {
                "institution_name": institution_name,
                "degree": degree,
                "field_of_study": field_of_study,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "is_current": is_current,
                "gpa": gpa,
                "description": ""
            }
            
        except Exception as e:
            logger.error(f"Error parsing education entry: {e}")
            return None
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text"""
        contact_info = {}
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact_info['email'] = email_match.group(0)
        
        # Extract phone number
        phone_match = re.search(r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', text)
        if phone_match:
            contact_info['phone'] = phone_match.group(0)
        
        # Extract LinkedIn
        linkedin_match = re.search(r'(?:linkedin\.com/in/|linkedin:)\s*([A-Za-z0-9\-]+)', text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin_url'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract GitHub
        github_match = re.search(r'(?:github\.com/|github:)\s*([A-Za-z0-9\-]+)', text, re.IGNORECASE)
        if github_match:
            contact_info['github_url'] = f"https://github.com/{github_match.group(1)}"
        
        return contact_info
    
    def _parse_date_string(self, date_str: str, is_end_date: bool = False) -> date:
        """Parse various date string formats into date objects"""
        if not date_str:
            return None
        
        from datetime import date
        import re
        
        # Clean up the date string
        date_str = date_str.strip()
        
        try:
            # Handle "Month Year" format (e.g., "March 2024", "July 2022")
            month_year_match = re.match(r'(\w+)\s+(\d{4})', date_str)
            if month_year_match:
                month_name, year = month_year_match.groups()
                year = int(year)
                
                # Map month names to numbers
                month_map = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
                    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
                    'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }
                
                month = month_map.get(month_name.lower())
                if month:
                    # For end dates, use last day of month; for start dates, use first day
                    if is_end_date:
                        # Get last day of month
                        if month == 12:
                            last_day = 31
                        elif month in [4, 6, 9, 11]:
                            last_day = 30
                        elif month == 2:
                            # Simple leap year check
                            last_day = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
                        else:
                            last_day = 31
                        return date(year, month, last_day)
                    else:
                        return date(year, month, 1)
            
            # Handle year-only format (e.g., "2024")
            if len(date_str) == 4 and date_str.isdigit():
                year = int(date_str)
                if is_end_date:
                    return date(year, 12, 31)
                else:
                    return date(year, 1, 1)
            
            # Handle MM/DD/YYYY or MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:  # MM/DD/YYYY
                    month, day, year = map(int, parts)
                    return date(year, month, day)
                elif len(parts) == 2:  # MM/YYYY
                    month, year = map(int, parts)
                    if is_end_date:
                        # Get last day of month
                        if month in [4, 6, 9, 11]:
                            day = 30
                        elif month == 2:
                            day = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
                        else:
                            day = 31
                        return date(year, month, day)
                    else:
                        return date(year, month, 1)
            
            # If all else fails, try to extract year and use that
            year_match = re.search(r'(\d{4})', date_str)
            if year_match:
                year = int(year_match.group(1))
                if is_end_date:
                    return date(year, 12, 31)
                else:
                    return date(year, 1, 1)
        
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse date string '{date_str}': {e}")
        
        # Return None for unparseable dates (don't use fallback)
        return None
    
    async def populate_user_profile_from_resume(self, user_id: int, parsed_data: Dict[str, Any], user_profile_service) -> Dict[str, Any]:
        """Populate user profile with parsed resume data"""
        try:
            results = {
                "skills_added": 0,
                "work_experience_added": 0,
                "education_added": 0,
                "contact_info_updated": False,
                "errors": []
            }
            
            # Add skills
            if parsed_data.get("skills"):
                for skill_name in parsed_data["skills"]:
                    try:
                        from src.models.user_profile import SkillAddRequest
                        skill_request = SkillAddRequest(
                            skill_name=skill_name,
                            proficiency_level="intermediate",
                            years_of_experience=None,
                            is_highlighted=False
                        )
                        await user_profile_service.add_skill_to_user(user_id, skill_request)
                        results["skills_added"] += 1
                    except Exception as e:
                        results["errors"].append(f"Error adding skill '{skill_name}': {str(e)}")
            
            # Add work experience
            if parsed_data.get("work_experience"):
                # Get existing work experiences to check for duplicates
                try:
                    existing_experiences = await user_profile_service.get_user_work_experience(user_id)
                    existing_set = set()
                    for exp in existing_experiences:
                        # Create a key for duplicate detection (company + job_title + start_date)
                        key = (exp.company_name.lower().strip(), exp.job_title.lower().strip(), str(exp.start_date))
                        existing_set.add(key)
                except Exception as e:
                    logger.warning(f"Could not get existing work experiences for duplicate check: {e}")
                    existing_set = set()
                
                for exp_data in parsed_data["work_experience"]:
                    try:
                        from datetime import date
                        
                        # Use the already-parsed dates from extraction (they're already in ISO format)
                        from datetime import date, datetime
                        
                        start_date_str = exp_data.get("start_date")
                        if start_date_str:
                            try:
                                # Parse ISO format date string (YYYY-MM-DD) to date object
                                start_date = datetime.fromisoformat(start_date_str).date()
                            except (ValueError, TypeError):
                                logger.warning(f"Could not parse start_date '{start_date_str}' for work experience: {exp_data.get('company_name', 'Unknown')} - {exp_data.get('job_title', 'Unknown')}. Using fallback date.")
                                # Use a reasonable fallback date (current year - 1)
                                current_year = date.today().year
                                start_date = date(current_year - 1, 1, 1)
                        else:
                            start_date = None
                        
                        # Handle end_date similarly but it's optional
                        end_date_str = exp_data.get("end_date")
                        if end_date_str:
                            try:
                                end_date = datetime.fromisoformat(end_date_str).date()
                            except (ValueError, TypeError):
                                logger.warning(f"Could not parse end_date '{end_date_str}'")
                                end_date = None
                        else:
                            end_date = None
                        
                        # Check for duplicate before adding
                        company_name = exp_data.get("company_name", "").strip()
                        job_title = exp_data.get("job_title", "").strip()
                        duplicate_key = (company_name.lower(), job_title.lower(), str(start_date))
                        
                        if duplicate_key in existing_set:
                            logger.info(f"Skipping duplicate work experience: {company_name} - {job_title}")
                            continue
                        
                        work_exp = WorkExperienceCreate(
                            user_id=user_id,
                            company_name=company_name,
                            job_title=job_title,
                            start_date=start_date,
                            end_date=end_date,
                            is_current=exp_data.get("is_current", False),
                            description=exp_data.get("description", ""),
                            achievements=exp_data.get("achievements", [])
                            # Note: technologies_used column is missing from database, skipping for now
                        )
                        await user_profile_service.add_work_experience(work_exp)
                        results["work_experience_added"] += 1
                        
                        # Add to existing_set to prevent duplicates within the same parsing session
                        existing_set.add(duplicate_key)
                        
                    except Exception as e:
                        results["errors"].append(f"Error adding work experience: {str(e)}")
            
            # Add education
            if parsed_data.get("education"):
                for edu_data in parsed_data["education"]:
                    try:
                        # Ensure required fields have values
                        institution_name = edu_data.get("institution_name", "").strip()
                        degree = edu_data.get("degree", "").strip()
                        
                        if not institution_name:
                            institution_name = "Unknown Institution"
                        if not degree:
                            degree = "Unknown Degree"
                        
                        education = EducationCreate(
                            user_id=user_id,
                            institution_name=institution_name,
                            degree=degree,
                            field_of_study=edu_data.get("field_of_study"),
                            start_date=edu_data.get("start_date"),
                            end_date=edu_data.get("end_date"),
                            is_current=edu_data.get("is_current", False),
                            gpa=edu_data.get("gpa"),
                            description=edu_data.get("description", "")
                        )
                        await user_profile_service.add_education(education)
                        results["education_added"] += 1
                    except Exception as e:
                        results["errors"].append(f"Error adding education: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error populating user profile from resume: {e}")
            return {
                "skills_added": 0,
                "work_experience_added": 0,
                "education_added": 0,
                "contact_info_updated": False,
                "errors": [str(e)]
            }