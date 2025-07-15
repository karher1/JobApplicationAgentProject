from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from typing import Optional
import os
import tempfile
import pdfplumber
from docx import Document
import asyncio

router = APIRouter()

async def extract_text_from_file(file_path: str, file_ext: str) -> str:
    try:
        if file_ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif file_ext in [".doc", ".docx"]:
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            return "[Unsupported file type for extraction]"
    except Exception as e:
        return f"[Error extracting text: {e}]"

@router.post("/resume/review")
async def review_resume(request: Request, file: UploadFile = File(...)):
    # Save uploaded file to a temp location
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Extract text from PDF/DOCX
    extracted_text = await extract_text_from_file(tmp_path, suffix)

    # Extract skills from resume text using LLM
    skills_prompt = (
        "Extract all technical skills, programming languages, tools, and technologies mentioned in this resume. "
        "Return only a comma-separated list of skills. Be specific and comprehensive.\n\n"
        f"Resume text:\n\n{extracted_text}"
    )

    # Extract ATS keywords
    ats_prompt = (
        "Identify important ATS keywords from this resume that would help with applicant tracking systems. "
        "Focus on job titles, certifications, technical skills, and industry terms. "
        "Return only a comma-separated list of keywords.\n\n"
        f"Resume text:\n\n{extracted_text}"
    )

    # Provide comprehensive analysis
    comprehensive_prompt = (
        "Analyze this resume comprehensively and provide specific, actionable feedback. "
        "Focus on: 1) ATS optimization, 2) Content improvements, 3) Structure and formatting, "
        "4) Missing sections, 5) Specific suggestions for improvement. "
        "Be detailed and provide concrete examples.\n\n"
        f"Resume text:\n\n{extracted_text}"
    )
    
    # Provide story-driven improvement suggestions
    improvement_prompt = (
        "Based on this resume, provide 5 specific improvements using story-driven principles that hiring managers love. "
        "Focus on transforming generic bullets into memorable stories. Use these frameworks:\n"
        "1. Problem-Solution Arc: How they noticed problems and created unique solutions\n"
        "2. Transformation Stories: How they inherited bad situations and dramatically improved them\n"
        "3. Innovation Narratives: How they did things differently than standard approaches\n"
        "4. Connection Stories: How they built bridges between teams/departments\n"
        "5. Personal Brand Thread: What makes this person uniquely valuable\n\n"
        "Give specific before/after examples where possible.\n\n"
        f"Resume text:\n\n{extracted_text}"
    )
    
    # Provide ATS score and tips
    ats_score_prompt = (
        "Rate this resume's ATS (Applicant Tracking System) compatibility on a scale of 1-10 "
        "and provide 3 specific tips to improve ATS parsing. Focus on formatting, keywords, and structure.\n\n"
        f"Resume text:\n\n{extracted_text}"
    )

    # Call LLM for analysis
    try:
        llm_service = request.app.state.llm_service
        
        # Get skills
        skills_messages = [
            {"role": "system", "content": "You are a resume analyzer that extracts skills."},
            {"role": "user", "content": skills_prompt}
        ]
        skills_response = await llm_service.chat_completion(skills_messages, temperature=0.1, max_tokens=200)
        skills = [skill.strip() for skill in skills_response.split(',') if skill.strip()]
        
        # Get ATS keywords
        ats_messages = [
            {"role": "system", "content": "You are an ATS keyword analyzer."},
            {"role": "user", "content": ats_prompt}
        ]
        ats_response = await llm_service.chat_completion(ats_messages, temperature=0.1, max_tokens=200)
        ats_keywords = [keyword.strip() for keyword in ats_response.split(',') if keyword.strip()]
        
        # Get comprehensive analysis
        comprehensive_messages = [
            {"role": "system", "content": "You are a professional resume coach and career advisor."},
            {"role": "user", "content": comprehensive_prompt}
        ]
        comprehensive_analysis = await llm_service.chat_completion(comprehensive_messages, temperature=0.2, max_tokens=500)
        
        # Get improvement suggestions
        improvement_messages = [
            {"role": "system", "content": "You are a resume optimization expert."},
            {"role": "user", "content": improvement_prompt}
        ]
        improvement_suggestions = await llm_service.chat_completion(improvement_messages, temperature=0.2, max_tokens=400)
        
        # Get ATS score and tips
        ats_messages = [
            {"role": "system", "content": "You are an ATS optimization specialist."},
            {"role": "user", "content": ats_score_prompt}
        ]
        ats_analysis = await llm_service.chat_completion(ats_messages, temperature=0.2, max_tokens=300)
        
        # Generate improved resume with story-driven approach
        improved_resume_prompt = (
            "Transform this resume from generic to memorable using story-driven principles. "
            "A hiring manager said: 'Recruiters don't hire qualifications. They hire people. Your unique story? Only you have that.'\n\n"
            "Apply these storytelling frameworks:\n"
            "1. Problem-Solution Arc: 'Noticed [specific problem] → Created [unique solution] → Delivered [measurable result]'\n"
            "2. Transformation Story: 'Inherited [bad situation] → Implemented [your approach] → Achieved [dramatic improvement]'\n"
            "3. Innovation Narrative: 'Everyone did [standard way] → I tried [different approach] → Results: [breakthrough outcome]'\n"
            "4. Connection Story: 'Realized [gap/disconnect] → Built [bridge/system] → Unlocked [hidden value]'\n\n"
            "Use the formula: Context (5 words) + Action (10 words) + Result (5 words)\n\n"
            "Transform generic bullets like:\n"
            "❌ 'Managed marketing campaigns'\n"
            "✅ 'Turned dying Instagram account into 50K community by spotting untapped micro-influencer strategy'\n\n"
            "❌ 'Collaborated with sales team'\n" 
            "✅ 'Built sales-marketing alignment system after noticing reps wasted 3 hours/day on bad leads'\n\n"
            "Create a personal brand thread (choose one):\n"
            "• The optimizer who finds waste\n"
            "• The connector who builds bridges\n"
            "• The innovator who questions everything\n"
            "• The builder who ships fast\n"
            "• The problem-solver who turns impossible into possible\n\n"
            "Make every bullet reinforce this thread and tell a unique story only this person could tell.\n\n"
            "FORMATTING INSTRUCTIONS:\n"
            "- Use clean, plain text formatting only\n"
            "- Do NOT use markdown symbols like ** or * or # or ---\n"
            "- Use simple capitalization for headers (like 'EXPERIENCE' or 'SKILLS')\n"
            "- Use simple bullet points with - or •\n"
            "- Keep the format professional but readable\n\n"
            f"Original Resume:\n\n{extracted_text}"
        )
        
        improved_resume_messages = [
            {"role": "system", "content": "You are an expert resume writer who transforms generic resumes into memorable stories. You understand that recruiters hire people, not just qualifications. You turn boring responsibility lists into compelling narratives that show the unique value only this person can bring. IMPORTANT: Use clean, plain text formatting. Do NOT use markdown symbols like ** or * or # for formatting. Use simple, readable text only."},
            {"role": "user", "content": improved_resume_prompt}
        ]
        improved_resume_raw = await llm_service.chat_completion(improved_resume_messages, temperature=0.3, max_tokens=1500)
        
        # Clean up any remaining markdown formatting
        improved_resume = improved_resume_raw.replace('**', '').replace('*', '').replace('###', '').replace('##', '').replace('#', '').replace('---', '')
        
    except Exception as e:
        skills = ["Error extracting skills"]
        ats_keywords = ["Error extracting keywords"]
        comprehensive_analysis = f"Error analyzing resume: {e}"
        improvement_suggestions = "Unable to generate improvement suggestions"
        ats_analysis = "Unable to analyze ATS compatibility"
        improved_resume = "Unable to generate improved resume"

    # Clean up temp file
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return JSONResponse(content={
        "success": True,
        "analysis": {
            "skills": skills,
            "ats_keywords": ats_keywords,
            "comprehensive_analysis": comprehensive_analysis,
            "improvement_suggestions": improvement_suggestions,
            "ats_analysis": ats_analysis,
            "improved_resume": improved_resume,
            "raw_text": extracted_text
        }
    })

@router.post("/resume/improve")
async def improve_resume_only(request: Request, file: UploadFile = File(...)):
    """Generate only an improved version of the resume for download"""
    # Save uploaded file to a temp location
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Extract text from PDF/DOCX
    extracted_text = await extract_text_from_file(tmp_path, suffix)

    # Generate improved resume with story-driven approach
    improved_resume_prompt = (
        "Transform this resume from generic to memorable using story-driven principles. "
        "Apply these storytelling frameworks:\n"
        "1. Problem-Solution Arc: 'Noticed [specific problem] → Created [unique solution] → Delivered [measurable result]'\n"
        "2. Transformation Story: 'Inherited [bad situation] → Implemented [your approach] → Achieved [dramatic improvement]'\n"
        "3. Innovation Narrative: 'Everyone did [standard way] → I tried [different approach] → Results: [breakthrough outcome]'\n"
        "4. Connection Story: 'Realized [gap/disconnect] → Built [bridge/system] → Unlocked [hidden value]'\n\n"
        "FORMATTING INSTRUCTIONS:\n"
        "- Use clean, plain text formatting only\n"
        "- Do NOT use markdown symbols like ** or * or # or ---\n"
        "- Use simple capitalization for headers (like 'EXPERIENCE' or 'SKILLS')\n"
        "- Use simple bullet points with - or •\n"
        "- Keep the format professional but readable\n\n"
        "Return ONLY the complete improved resume in a clean, professional format.\n\n"
        f"Original Resume:\n\n{extracted_text}"
    )

    try:
        llm_service = request.app.state.llm_service
        messages = [
            {"role": "system", "content": "You are an expert resume writer who creates compelling, ATS-optimized resumes. IMPORTANT: Use clean, plain text formatting. Do NOT use markdown symbols like ** or * or # for formatting. Use simple, readable text only."},
            {"role": "user", "content": improved_resume_prompt}
        ]
        improved_resume_raw = await llm_service.chat_completion(messages, temperature=0.3, max_tokens=1500)
        
        # Clean up any remaining markdown formatting
        improved_resume = improved_resume_raw.replace('**', '').replace('*', '').replace('###', '').replace('##', '').replace('#', '').replace('---', '')
    except Exception as e:
        improved_resume = f"Error generating improved resume: {e}"

    # Clean up temp file
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    # Return as downloadable text file
    return Response(
        content=improved_resume,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=improved_resume.txt"}
    ) 