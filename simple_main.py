from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
from pathlib import Path
import logging
import json
import re
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Analysis API",
    description="Simple resume analysis service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    job_description: Optional[str] = None

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file using pdfplumber"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file using python-docx"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text).strip()
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return ""

async def ai_analyze_resume(resume_text: str, job_description: Optional[str] = None) -> dict:
    """AI-powered resume analysis using OpenAI"""
    
    # Initialize OpenAI client
    # For demo purposes, we'll use a mock response if no API key is available
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        use_ai = bool(os.getenv("OPENAI_API_KEY"))
    except:
        use_ai = False
    
    if not use_ai:
        logger.info("No OpenAI API key found, using enhanced rule-based analysis")
        return enhanced_rule_based_analysis(resume_text, job_description)
    
    # Create the AI prompt
    job_context = f"\n\nJOB DESCRIPTION:\n{job_description}" if job_description else "\n\nNOTE: No specific job description provided - analyze for general ATS compatibility."
    
    prompt = f"""You are an expert ATS (Applicant Tracking System) resume analyst. Analyze this resume for ATS compatibility and provide specific, actionable recommendations.

RESUME:
{resume_text[:3000]}  # Limit to avoid token limits
{job_context}

Please analyze the resume and provide a detailed assessment in the following JSON format:

{{
    "overall_score": <number 0-100>,
    "ats_compatibility": {{
        "score": <number 0-100>,
        "issues": [<list of specific ATS formatting issues>],
        "recommendations": [<list of specific ATS improvements>]
    }},
    "content_strength": {{
        "score": <number 0-100>,
        "strengths": [<list of content strengths>],
        "weaknesses": [<list of content weaknesses>],
        "feedback": [<list of improvement suggestions>]
    }},
    "keyword_optimization": {{
        "keyword_match_score": <number 0-100>,
        "missing_keywords": [<skills/keywords missing from resume but important for role>],
        "present_keywords": [<relevant skills/keywords found in resume>],
        "recommendations": [<specific keyword optimization advice>]
    }},
    "improvement_suggestions": [
        {{
            "category": "<Keywords|Content|Formatting>",
            "priority": "<high|medium|low>", 
            "suggestion": "<specific actionable suggestion>",
            "example": "<concrete example of improvement>"
        }}
    ]
}}

ANALYSIS GUIDELINES:
1. Focus on ATS compatibility (simple formatting, keyword density, structure)
2. If job description provided, prioritize skills/keywords mentioned there
3. CRITICALLY IMPORTANT: Penalize scores significantly if resume skills don't match job requirements
4. For role mismatches (e.g., software engineer resume vs QA role), scores should be much lower
5. Look for quantified achievements, action verbs, and relevant experience
6. Identify missing technical skills that would strengthen the resume
7. Suggest specific, actionable improvements with examples
8. Include role compatibility warnings for significant mismatches
9. Be constructive but realistic about role fit

SCORING RULES:
- If resume has <50% skill match with job: Overall score should be <60
- If resume has <30% skill match with job: Overall score should be <45
- ATS score can be decent even with role mismatch (formatting is separate from skills)
- Always explain in suggestions if there's a significant role mismatch

Return ONLY the JSON response, no additional text."""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for consistent analysis
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            # Remove any markdown formatting if present
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].strip()
            
            result = json.loads(ai_response)
            
            # Validate required fields and ensure they're in correct format
            if not all(key in result for key in ["overall_score", "ats_compatibility", "content_strength", "keyword_optimization", "improvement_suggestions"]):
                raise ValueError("Missing required fields in AI response")
            
            logger.info("AI analysis completed successfully")
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"AI Response: {ai_response[:500]}...")
            # Fallback to rule-based analysis
            return enhanced_rule_based_analysis(resume_text, job_description)
            
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        # Fallback to rule-based analysis
        return enhanced_rule_based_analysis(resume_text, job_description)


def enhanced_rule_based_analysis(resume_text: str, job_description: Optional[str] = None) -> dict:
    """Enhanced rule-based analysis as fallback when AI is not available"""
    
    # Convert to lowercase for analysis
    resume_lower = resume_text.lower()
    
    # Expanded technical skills database
    all_tech_skills = [
        # Programming Languages
        "python", "javascript", "java", "c++", "c#", "ruby", "php", "swift", "kotlin", "go", "rust", "typescript",
        # Frontend
        "react", "angular", "vue", "svelte", "next.js", "nuxt.js", "html", "css", "sass", "scss", "tailwind", "bootstrap",
        # Backend/Frameworks
        "node.js", "express", "django", "flask", "spring", "laravel", "rails", "asp.net", "fastapi",
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "sqlite", "oracle", "cassandra",
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "github actions", "gitlab ci",
        # Tools & Others
        "git", "github", "gitlab", "jira", "confluence", "slack", "figma", "postman",
        # Methodologies
        "agile", "scrum", "kanban", "devops", "ci/cd", "tdd", "microservices",
        # Data & AI
        "machine learning", "ai", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "data analysis"
    ]
    
    # Find skills present in resume
    present_keywords = []
    for skill in all_tech_skills:
        if skill in resume_lower or skill.replace(" ", "") in resume_lower:
            present_keywords.append(skill.title())
    
    # Analyze job description if provided
    job_keywords = []
    if job_description:
        job_lower = job_description.lower()
        for skill in all_tech_skills:
            if skill in job_lower or skill.replace(" ", "") in job_lower:
                job_keywords.append(skill.title())
    
    # Find missing keywords (in job but not in resume)
    missing_keywords = [kw for kw in job_keywords if kw.lower() not in [pk.lower() for pk in present_keywords]]
    
    # Calculate role compatibility score
    role_compatibility = 100  # Start with perfect score
    if job_keywords:  # Only calculate if we have job requirements
        # Penalty for missing critical skills
        missing_critical_skills = len(missing_keywords)
        if missing_critical_skills > 0:
            # Heavy penalty for missing job-required skills
            role_compatibility -= min(50, missing_critical_skills * 10)
        
        # Bonus for having job-required skills
        matching_skills = len([kw for kw in job_keywords if kw.lower() in [pk.lower() for pk in present_keywords]])
        if len(job_keywords) > 0:
            match_percentage = (matching_skills / len(job_keywords)) * 100
            if match_percentage < 30:  # Less than 30% match is very poor
                role_compatibility -= 40
            elif match_percentage < 50:  # Less than 50% match is poor
                role_compatibility -= 25
            elif match_percentage < 70:  # Less than 70% match is average
                role_compatibility -= 10
    
    # If no job description, suggest trending skills but don't penalize role compatibility
    if not job_description:
        trending_skills = ["Docker", "Kubernetes", "AWS", "CI/CD", "TypeScript", "React"]
        missing_keywords = [skill for skill in trending_skills if skill.lower() not in [pk.lower() for pk in present_keywords]]
        role_compatibility = 85  # Neutral score when no job description provided
    
    # Enhanced content analysis
    word_count = len(resume_text.split())
    has_metrics = bool(re.search(r'\d+%|\d+x|\$\d+|\d+\+|increased|improved|reduced|achieved|boosted|enhanced', resume_lower))
    has_action_verbs = bool(re.search(r'led|managed|developed|created|implemented|designed|built|architected|optimized|delivered|launched', resume_lower))
    has_bullet_points = '•' in resume_text or resume_text.count('\n-') > 3 or resume_text.count('*') > 3
    has_contact_info = bool(re.search(r'@|phone|email|linkedin|github', resume_lower))
    
    # Improved scoring algorithm with role compatibility
    base_keyword_score = min(85, len(present_keywords) * 6 + 20)
    if len(present_keywords) > 10: base_keyword_score += 5  # Bonus for many relevant skills
    
    # Apply role compatibility to keyword score
    keyword_score = int(base_keyword_score * (role_compatibility / 100))
    
    content_score = 40
    if has_metrics: content_score += 25
    if has_action_verbs: content_score += 20
    if word_count > 150: content_score += 10
    if word_count > 300: content_score += 5
    if has_contact_info: content_score += 5
    
    # ATS score - this should be less affected by role mismatch (formatting is formatting)
    base_ats_score = 50
    if has_bullet_points: base_ats_score += 20
    if len(present_keywords) > 8: base_ats_score += 15
    if len(present_keywords) > 5: base_ats_score += 10
    if not re.search(r'[^\w\s\-\(\)\[\]\{\}\.\,\:\;]', resume_text): base_ats_score += 10  # Clean formatting
    if has_contact_info: base_ats_score += 5
    
    # Apply moderate role compatibility penalty to ATS score (less severe than keywords)
    ats_score = int(base_ats_score * (max(70, role_compatibility) / 100))  # At least 70% of base score
    
    # Overall score calculation with role compatibility as major factor
    overall_score = int((keyword_score * 0.5 + content_score * 0.25 + ats_score * 0.25))
    
    # Additional penalty for very poor role matches
    if job_keywords and role_compatibility < 50:
        overall_score = int(overall_score * 0.7)  # 30% additional penalty for severe mismatch
    
    overall_score = min(90, overall_score)  # Cap at 90 for rule-based
    
    # Generate intelligent suggestions
    suggestions = []
    
    # Add role compatibility warning if significant mismatch
    if job_keywords and role_compatibility < 60:
        match_percentage = (len([kw for kw in job_keywords if kw.lower() in [pk.lower() for pk in present_keywords]]) / len(job_keywords)) * 100 if job_keywords else 0
        suggestions.append({
            "category": "Role Match",
            "priority": "high",
            "suggestion": f"Resume shows {match_percentage:.0f}% skill match with job requirements - consider targeting more relevant positions",
            "example": "Focus on roles that better match your technical background, or acquire missing skills through training/projects"
        })
    
    if missing_keywords:
        top_missing = missing_keywords[:3]
        priority = "high" if len(missing_keywords) > 3 else "medium"
        suggestions.append({
            "category": "Keywords",
            "priority": priority,
            "suggestion": f"Add these job-required skills: {', '.join(top_missing)}",
            "example": f"Include '{top_missing[0]}' in your technical skills or experience section"
        })
    
    if not has_metrics:
        suggestions.append({
            "category": "Content",
            "priority": "high",
            "suggestion": "Add quantified achievements with specific metrics",
            "example": "Change 'improved system performance' to 'improved system performance by 40%, reducing load times from 3s to 1.8s'"
        })
    
    if not has_action_verbs:
        suggestions.append({
            "category": "Content",
            "priority": "medium",
            "suggestion": "Use stronger action verbs to start bullet points",
            "example": "Replace 'Responsible for team management' with 'Led cross-functional team of 8 developers'"
        })
    
    if not has_bullet_points:
        suggestions.append({
            "category": "Formatting",
            "priority": "medium",
            "suggestion": "Use bullet points for better ATS scanning and readability",
            "example": "Format key achievements as: • Developed RESTful APIs • Led agile development process"
        })
    
    if word_count < 150:
        suggestions.append({
            "category": "Content",
            "priority": "medium",
            "suggestion": "Expand content with more detailed experience descriptions",
            "example": "Add specific technologies used, team size, project outcomes, and impact metrics"
        })
    
    # Enhanced strengths and weaknesses
    strengths = []
    weaknesses = []
    
    if len(present_keywords) > 8:
        strengths.append("Excellent technical skill coverage")
    elif len(present_keywords) > 5:
        strengths.append("Good technical skill set")
    
    if has_action_verbs:
        strengths.append("Uses strong action-oriented language")
    if has_metrics:
        strengths.append("Includes quantified achievements")
    if word_count > 200:
        strengths.append("Comprehensive experience detail")
    if has_bullet_points:
        strengths.append("Well-formatted for ATS systems")
    
    if not has_metrics:
        weaknesses.append("Missing quantified achievements and metrics")
    if not has_action_verbs:
        weaknesses.append("Could use stronger action verbs")
    if len(present_keywords) < 5:
        weaknesses.append("Limited technical keyword presence")
    if word_count < 150:
        weaknesses.append("Content could be more detailed")
    if not has_bullet_points:
        weaknesses.append("Formatting could be more ATS-friendly")
    
    return {
        "overall_score": overall_score,
        "ats_compatibility": {
            "score": ats_score,
            "issues": ["Missing bullet point formatting"] if not has_bullet_points else [],
            "recommendations": ["Use bullet points and clean formatting for better ATS parsing"] if not has_bullet_points else ["Good ATS-friendly formatting detected"]
        },
        "content_strength": {
            "score": content_score,
            "strengths": strengths or ["Professional presentation"],
            "weaknesses": weaknesses or ["Generally well-structured content"],
            "feedback": [suggestion["suggestion"] for suggestion in suggestions[:2]]
        },
        "keyword_optimization": {
            "keyword_match_score": keyword_score,
            "missing_keywords": missing_keywords[:6],  # Show up to 6
            "present_keywords": present_keywords[:12],  # Show top 12
            "recommendations": [f"Consider adding {', '.join(missing_keywords[:3])} to strengthen keyword match"] if missing_keywords else ["Strong keyword coverage for this role"]
        },
        "improvement_suggestions": suggestions[:5]  # Limit to top 5 suggestions
    }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Resume Analysis API", "status": "running"}

@app.post("/api/resume-analysis/analyze")
async def analyze_resume_text(request: ResumeAnalysisRequest):
    """Analyze resume text and provide optimization recommendations"""
    try:
        if not request.resume_text.strip():
            raise HTTPException(status_code=400, detail="Resume text cannot be empty")
        
        # AI-powered resume analysis
        analysis = await ai_analyze_resume(request.resume_text, request.job_description)
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume-analysis/analyze-file")
async def analyze_resume_file(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    """Analyze uploaded resume file"""
    try:
        # Check file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.pdf', '.docx', '.txt']:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PDF, DOCX, or TXT files."
            )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Extract text based on file type
            text_content = ""
            if file_extension == '.pdf':
                text_content = extract_text_from_pdf(temp_file_path)
            elif file_extension == '.docx':
                text_content = extract_text_from_docx(temp_file_path)
            elif file_extension == '.txt':
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            if not text_content.strip():
                raise HTTPException(
                    status_code=400, 
                    detail="Could not extract text from file. Please ensure the file contains readable text."
                )
            
            # AI-powered analysis of extracted text
            analysis = await ai_analyze_resume(text_content, job_description)
            
            return {
                "success": True,
                "filename": file.filename,
                "text_length": len(text_content),
                "analysis": analysis
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def ai_optimize_resume(resume_text: str, job_description: str) -> dict:
    """AI-powered resume optimization for specific job descriptions"""
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        use_ai = bool(os.getenv("OPENAI_API_KEY"))
    except:
        use_ai = False
    
    if not use_ai:
        logger.info("No OpenAI API key found, using rule-based optimization")
        return rule_based_optimization(resume_text, job_description)
    
    # Create optimization prompt
    prompt = f"""You are an expert resume optimization consultant. Your task is to optimize this resume specifically for the given job description while maintaining truthfulness and the candidate's authentic experience.

ORIGINAL RESUME:
{resume_text[:3000]}

TARGET JOB DESCRIPTION:
{job_description[:2000]}

Please provide an optimized version that:

1. **Keyword Optimization**: Naturally integrate relevant keywords from job description
2. **Content Reordering**: Prioritize most relevant experience for this role
3. **Achievement Enhancement**: Strengthen accomplishment descriptions with metrics
4. **Skill Highlighting**: Emphasize skills that match job requirements
5. **ATS Optimization**: Ensure clean, scannable formatting
6. **Truthful Enhancement**: Only enhance existing content, never fabricate

Return your response in JSON format:

{{
    "optimized_resume": "<complete optimized resume text>",
    "improvements_made": [
        {{
            "category": "<Keywords|Structure|Content|Formatting>",
            "change": "<description of what was changed>",
            "reason": "<why this change improves the resume>"
        }}
    ],
    "keyword_additions": ["<new keywords added>"],
    "score_improvement": {{
        "original_score": <estimated 0-100>,
        "optimized_score": <estimated 0-100>,
        "improvement_areas": ["<areas that were improved>"]
    }},
    "success": true
}}

OPTIMIZATION GUIDELINES:
- Maintain the candidate's authentic voice and experience
- Only enhance existing accomplishments, never add fake experience
- Integrate keywords naturally, avoiding keyword stuffing
- Improve readability and ATS compatibility
- Focus on achievements relevant to the target role
- Use strong action verbs and quantified results

Return ONLY the JSON response."""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].strip()
            
            result = json.loads(ai_response)
            
            # Validate response structure
            required_fields = ["optimized_resume", "improvements_made", "keyword_additions", "score_improvement", "success"]
            if not all(field in result for field in required_fields):
                raise ValueError("Missing required fields in AI response")
            
            logger.info("AI resume optimization completed successfully")
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI optimization response: {e}")
            logger.error(f"AI Response: {ai_response[:500]}...")
            return rule_based_optimization(resume_text, job_description)
            
    except Exception as e:
        logger.error(f"AI optimization failed: {e}")
        return rule_based_optimization(resume_text, job_description)


def rule_based_optimization(resume_text: str, job_description: str) -> dict:
    """Rule-based resume optimization as fallback"""
    
    # Analyze job description for keywords
    job_lower = job_description.lower()
    
    # Extract important keywords from job description
    important_words = []
    tech_skills = [
        "python", "javascript", "java", "react", "angular", "vue", "node.js", "aws", "azure", "docker", 
        "kubernetes", "sql", "mongodb", "git", "agile", "scrum", "ci/cd", "terraform", "jenkins"
    ]
    
    for skill in tech_skills:
        if skill in job_lower and skill.lower() not in resume_text.lower():
            important_words.append(skill.title())
    
    # Basic optimization - add missing keywords and improve formatting
    optimized_resume = resume_text
    improvements = []
    
    # Add bullet points if missing
    if "•" not in optimized_resume and "\n-" not in optimized_resume:
        # Convert paragraphs to bullet points
        lines = optimized_resume.split('\n')
        optimized_lines = []
        for line in lines:
            if line.strip() and len(line.strip()) > 30 and not line.strip().startswith('•'):
                optimized_lines.append("• " + line.strip())
            else:
                optimized_lines.append(line)
        optimized_resume = '\n'.join(optimized_lines)
        improvements.append({
            "category": "Formatting",
            "change": "Added bullet points for better readability",
            "reason": "Improves ATS scanning and visual appeal"
        })
    
    # Suggest adding missing keywords
    if important_words:
        skills_section = f"\n\nAdditional Relevant Skills: {', '.join(important_words[:5])}"
        optimized_resume += skills_section
        improvements.append({
            "category": "Keywords",
            "change": f"Added relevant skills: {', '.join(important_words[:3])}",
            "reason": "Improves keyword match with job requirements"
        })
    
    return {
        "optimized_resume": optimized_resume,
        "improvements_made": improvements,
        "keyword_additions": important_words[:5],
        "score_improvement": {
            "original_score": 65,
            "optimized_score": 78,
            "improvement_areas": ["Keyword optimization", "Formatting", "ATS compatibility"]
        },
        "success": True
    }


@app.post("/api/resume-analysis/optimize")
async def optimize_resume_for_job(
    resume_text: str = Form(...),
    job_description: str = Form(...)
):
    """Optimize resume for a specific job description"""
    try:
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Resume text cannot be empty")
        
        if not job_description.strip():
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        
        # AI-powered resume optimization
        optimization_result = await ai_optimize_resume(resume_text, job_description)
        
        return {
            "success": True,
            "optimization": optimization_result
        }
    except Exception as e:
        logger.error(f"Error optimizing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resume-analysis/compare")
async def compare_resume_versions(
    original_resume: str = Form(...),
    optimized_resume: str = Form(...),
    job_description: str = Form(None)
):
    """Compare two resume versions and provide analysis"""
    try:
        if not original_resume.strip() or not optimized_resume.strip():
            raise HTTPException(status_code=400, detail="Both resume versions are required")
        
        # Analyze both versions
        original_analysis = await ai_analyze_resume(original_resume, job_description)
        optimized_analysis = await ai_analyze_resume(optimized_resume, job_description)
        
        # Calculate improvements
        score_improvement = optimized_analysis["overall_score"] - original_analysis["overall_score"]
        keyword_improvement = optimized_analysis["keyword_optimization"]["keyword_match_score"] - original_analysis["keyword_optimization"]["keyword_match_score"]
        ats_improvement = optimized_analysis["ats_compatibility"]["score"] - original_analysis["ats_compatibility"]["score"]
        
        comparison = {
            "original_analysis": original_analysis,
            "optimized_analysis": optimized_analysis,
            "improvements": {
                "overall_score_change": score_improvement,
                "keyword_score_change": keyword_improvement,
                "ats_score_change": ats_improvement,
                "recommendation": "Use optimized version" if score_improvement > 5 else "Minimal improvement - either version acceptable"
            },
            "summary": {
                "better_version": "optimized" if score_improvement > 2 else "original" if score_improvement < -2 else "similar",
                "key_improvements": [],
                "areas_improved": []
            }
        }
        
        # Identify key improvements
        if keyword_improvement > 5:
            comparison["summary"]["key_improvements"].append("Better keyword optimization")
            comparison["summary"]["areas_improved"].append("Keywords")
        
        if ats_improvement > 5:
            comparison["summary"]["key_improvements"].append("Improved ATS compatibility")
            comparison["summary"]["areas_improved"].append("ATS Format")
        
        if score_improvement > 10:
            comparison["summary"]["key_improvements"].append("Significant overall improvement")
        
        return {
            "success": True,
            "comparison": comparison
        }
        
    except Exception as e:
        logger.error(f"Error comparing resume versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)