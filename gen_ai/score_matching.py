import os
import json
import spacy
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def get_match_schema():
    """Defines the strict JSON schema for the match results, now including name and email."""
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "candidate_name": types.Schema( 
                type=types.Type.STRING,
                description="The full name of the candidate extracted from the resume."
            ),
            "candidate_email": types.Schema( 
                type=types.Type.STRING,
                description="The primary email address of the candidate extracted from the resume."
            ),
            "match_score": types.Schema(
                type=types.Type.INTEGER,
                description="The candidate's score as a percentage (0-100) based on semantic matching of the JD requirements to the resume content."
            ),
            "summary_remark": types.Schema(
                type=types.Type.STRING,
                description="A brief, encouraging remark (1-2 sentences) justifying the score, highlighting a major strength and weakness."
            ),
            "missing_skills": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="A list of 3-5 critical 'must-have' skills or experiences from the JD that were either missing or weak in the resume."
            )
        },
        required=["candidate_name", "candidate_email", "match_score", "summary_remark", "missing_skills"]
    )


try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Warning: spaCy model 'en_core_web_md' not found. Please run 'python -m spacy download en_core_web_md'")
    nlp = None


def extract_entities_spacy(text):
    """
    Uses spaCy for improved Named Entity Recognition (NER) and targeted extraction
    of skills/keywords using normalization (lemma) and multi-word phrases (noun chunks).
    """
    if not nlp:
        return {"extracted_entities": [], "keywords_proxy": ""} 
        
    doc = nlp(text)
    
    entities = []
    for ent in doc.ents:
        if ent.label_ in ["ORG", "GPE", "DATE", "PRODUCT", "LANGUAGE", "PERSON", "TECH", "SKILL"]:
            entities.append(f"{ent.label_}: {ent.text}")
            
    skills_from_chunks = [
        chunk.text.lower().strip() 
        for chunk in doc.noun_chunks 
        if len(chunk.text.split()) > 1 and len(chunk.text) > 5
    ]

    skills_from_tokens = [
        token.lemma_.lower()
        for token in doc 
        if token.pos_ in ["NOUN", "PROPN"] 
        and not token.is_stop            
        and len(token.lemma_) > 2          
    ]

    all_skills = list(set(skills_from_chunks + skills_from_tokens))
    
    MAX_KEYWORDS = 30
    
    return {
        "summary": text[:500].replace('\n', ' '), 
        "extracted_entities": entities,
        "keywords_proxy": ", ".join(all_skills[:MAX_KEYWORDS]) 
    }



def match_and_score_gemini(jd_text, resume_text):
    """
    Performs deep semantic matching and scoring using the Gemini API.
    """
    if not os.getenv("GEMINI_API_KEY"):
         return {"error": "GEMINI_API_KEY is not set in .env file."}

    jd_data = extract_entities_spacy(jd_text)
    resume_data = extract_entities_spacy(resume_text)

    try:
        client = genai.Client() 
    except Exception as e:
        return {"error": f"Error initializing Gemini client: {e}"}

    prompt = f"""
    You are an expert AI recruiter. Your task is to **extract the candidate's name and email**, and then semantically compare a Job Description (JD) and a Resume to produce a single match score (0-100) and an analysis.

    **Instructions:**
    1. **REQUIRED EXTRACTION:** Extract the **Full Name** and **Primary Email** of the candidate from the resume and place them into the designated JSON fields. If data is not found, use "Unknown Candidate" and "no-email-found@example.com".
    2. The core score must be based on the semantic match between the JD's 'Required Qualifications' and the Resume's 'Experience' and 'Skills' sections.
    3. The score should heavily weight the Must-Have Skills listed in the JD.
    4. Output must be STRICTLY in the required JSON format.
    5. For missing_skills STRICTLY give the missing skills from the resume compared to job description. If there is no missing skills then give a summary that all the skills are matched.

    ---
    
    **Job Description (JD) Content:**
    {jd_text}
    
    **Candidate Resume Content:**
    {resume_text}

    ---
    
    **Structured Data extracted via spaCy (For reference and structure):**
    - **JD Keywords:** {jd_data['keywords_proxy']}
    - **Resume Keywords:** {resume_data['keywords_proxy']}
    
    **Output Example (Must be a JSON object - UPDATED):**
    ```json
    {{
      "candidate_name": "Alex Chen",
      "candidate_email": "alex.chen@example.com",
      "match_score": 90,
      "summary_remark": "Excellent technical alignment, especially in cloud architecture and Terraform. Focus on gaining experience in multi-cloud governance to maximize future potential.",
      "missing_skills": ["CI/CD pipeline management", "Multi-cloud governance experience", "Advanced Python scripting for automation"]
    }}
    ```
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, 
                response_mime_type="application/json", 
                response_schema=get_match_schema(),
            )
        )
        
        return json.loads(response.text)

    except json.JSONDecodeError:
        return {"error": f"Failed to decode JSON response from API. Raw output: {response.text}"}
    except Exception as e:
        return {"error": f"An error occurred during API call: {e}"}


# if __name__ == '__main__':
    
#     sample_jd = """
#     ## Job Summary
#     CloudSphere Innovations is seeking a Senior Cloud Solutions Architect with 
#     a minimum of **5 years** of experience to design and deploy highly scalable, 
#     secure solutions across hybrid environments.
    
#     ## Responsibilities
#     - Lead the design and implementation of cloud solutions using Infrastructure as Code (IaC).
#     - Establish best practices for security and cost optimization on AWS.
#     - Develop and manage CI/CD pipelines for automated deployment.
    
#     ## Required Qualifications
#     - Minimum of 5 years of professional experience in Cloud Architecture.
#     - **Must-Have Skills:** AWS, Kubernetes, Terraform, Python, CI/CD.
#     - Expertise in networking, security, and compliance.
    
#     ## What We Offer
#     - Competitive salary.
#     - Generous PTO and professional development budget.
#     """

#     sample_resume = """
#     **Name:** Alex Chen
#     **Experience (4 years total):**
#     - Cloud Engineer at TechForward (3 years): Focused on migrating applications 
#       to AWS. Strong experience with EC2, VPC, and S3. Proficient in **Terraform** for managing infrastructure. Developed internal tools using **Python** for 
#       reporting. Completed advanced training in **Kubernetes** administration.
#     - Junior Developer at WebSoft (1 year): Front-end development.
    
#     **Skills:** AWS, Terraform (advanced), Python (intermediate), Kubernetes, Docker, Linux.
#     """

#     print("--- Running Hybrid Match & Score Analysis ---")
    
#     match_results = match_and_score_gemini(sample_jd, sample_resume)

#     print("\n" + "="*70)
#     print(f"Match Results for Candidate Alex Chen against Senior Cloud Architect JD")
#     print("="*70)
    
#     if "error" in match_results:
#         print(f"**Error:** {match_results['error']}")
#     else:
#         print(f"Name: {match_results.get('candidate_name', 'N/A')}")
#         print(f"Email: {match_results.get('candidate_email', 'N/A')}")
#         print(f"SCORE: {match_results.get('match_score', 'N/A')}/100 🎯")
#         print("\nSUMMARY REMARK:")
#         print(f"    {match_results.get('summary_remark', 'N/A')}")
#         print("\nCRITICAL GAPS:")
#         for skill in match_results.get('missing_skills', []):
#             print(f"    - {skill}")
            
#     print("="*70)