from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..')) 

if project_root not in sys.path:
    sys.path.append(project_root)


try:
    from gen_ai.generate_jd import generate_job_description 
    from gen_ai.score_matching import match_and_score_gemini 
    from gen_ai.generate_email_batch import generate_batch_feedback_emails 
    from gen_ai.generate_email_single import generate_feedback_email 
except ImportError as e:
    print(f"FATAL: Could not import AI logic. Check Python path and gen_ai structure: {e}")
    sys.exit(1)


app = FastAPI(
    title="Recruitment AI Agent API",
    description="Backend service for JD Generation and Resume Matching using Gemini."
)


class JDRequest(BaseModel):
    job_title: str
    years_of_experience: int
    must_have_skills: str
    company_name: str
    employment_type: str
    industry: str
    location: str

class JDResponse(BaseModel):
    job_description: str

class MatchRequest(BaseModel):
    jd_text: str
    resume_text: str

class BatchCandidateEmailRequest(BaseModel):
    candidate_name: str
    job_title: str 
    match_score: int
    remark: str
    missing_skills: list[str]

class BatchEmailRequest(BaseModel):
    job_title: str
    candidates: list[BatchCandidateEmailRequest]

class BatchEmailResponseItem(BaseModel):
    candidate_name: str
    subject: str
    body: str


class MatchResponse(BaseModel):
    candidate_name: str  
    candidate_email: str 
    match_score: int
    summary_remark: str
    missing_skills: list[str]


class EmailRequest(BaseModel):
    candidate_name: str
    job_title: str
    match_score: int
    remark: str
    missing_skills: list[str]

class EmailResponse(BaseModel):
    subject: str
    body: str


@app.post("/generate-email", response_model=EmailResponse)
def generate_email_api(request: EmailRequest):
    """Generates a personalized feedback email for a candidate using Gemini (Single Call)."""
    email_output = generate_feedback_email(
        candidate_name=request.candidate_name,
        job_title=request.job_title,
        match_score=request.match_score,
        remark=request.remark,
        missing_skills_list=request.missing_skills
    )
    
    if "error" in email_output:
        raise HTTPException(status_code=500, detail=email_output['error'])
        
    return EmailResponse(
        subject=email_output.get("subject", "No Subject Generated"),
        body=email_output.get("body", "No Body Generated")
    )

@app.post("/match-resume", response_model=MatchResponse)
def match_resume_api(request: MatchRequest):
    """Performs semantic matching and scoring between JD and Resume."""
    
    match_output = match_and_score_gemini(
        jd_text=request.jd_text, 
        resume_text=request.resume_text
    )
    
    if "error" in match_output:
        raise HTTPException(status_code=500, detail=match_output.get('error', 'Unknown AI processing error.'))

    return MatchResponse(
        candidate_name=match_output.get("candidate_name", "Unknown Candidate"), # <--- MAPPED
        candidate_email=match_output.get("candidate_email", "no-email@example.com"), # <--- MAPPED
        match_score=match_output.get("match_score", 0),
        summary_remark=match_output.get("summary_remark", "Processing failed."),
        missing_skills=match_output.get("missing_skills", []),
    )


@app.post("/generate-jd", response_model=JDResponse)
def generate_jd_api(request: JDRequest):
    """Generates a comprehensive Job Description using the Gemini API."""
    
    jd_text = generate_job_description(
        job_title=request.job_title,
        years_of_experience=request.years_of_experience,
        must_have_skills=request.must_have_skills,
        company_name=request.company_name,
        employment_type=request.employment_type,
        industry=request.industry,
        location=request.location
    )
    
    if jd_text.startswith("Error"):
        raise HTTPException(status_code=500, detail=jd_text)
        
    return JDResponse(job_description=jd_text)



@app.post("/generate-batch-emails", response_model=list[BatchEmailResponseItem])
def generate_batch_emails_api(request: BatchEmailRequest):
    """
    Generates personalized feedback emails for multiple candidates in a single LLM batch call.
    """
    candidate_results_list = [
        {
            "candidate_name": c.candidate_name,
            "match_score": c.match_score,
            "summary_remark": c.remark,
            "missing_skills": c.missing_skills
        }
        for c in request.candidates
    ]

    email_outputs = generate_batch_feedback_emails(
        candidate_results_list=candidate_results_list,
        job_title=request.job_title
    )
    
    if "error" in email_outputs:
        raise HTTPException(status_code=500, detail=email_outputs['error'])
    return [
        BatchEmailResponseItem(
            candidate_name=item.get("candidate_name", "Unknown Candidate"),
            subject=item.get("subject", "No Subject"),
            body=item.get("body", "No Body")
        )
        for item in email_outputs
    ]
    
