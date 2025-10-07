import os
import json
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv() 

def get_email_schema():
    """Defines the strict JSON schema for the email output."""
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "subject": types.Schema(
                type=types.Type.STRING,
                description="The professional subject line for the email."
            ),
            "body": types.Schema(
                type=types.Type.STRING,
                description="The full body of the professional email, using paragraphs and newlines for readability."
            )
        },
        required=["subject", "body"]
    )

def clean_llm_response(response_text):
    """
    Cleans LLM response to ensure valid JSON by isolating content 
    between the first '{' and the last '}'.
    """
    start = response_text.find('{')
    end = response_text.rfind('}')

    if start == -1 or end == -1 or end < start:
        raise ValueError("Invalid JSON response format: Braces not found or mismatched.")

    json_str = response_text[start : end + 1]
    return json_str


def generate_feedback_email(candidate_name, job_title, match_score, remark, missing_skills_list):
    """
    Generates a structured, personalized feedback email using the Gemini API.
    """
    if not os.getenv("GEMINI_API_KEY"):
         return {"error": "GEMINI_API_KEY is not set in .env file."}

    try:
        client = genai.Client() 
    except Exception as e:
        return {"error": f"Error initializing Gemini client: {e}"}

    missing_skills_str = ", ".join(missing_skills_list) if missing_skills_list else "None explicitly listed."

    if match_score >= 80:
        tone = "Highly positive. The email should express strong interest and next steps."
        closing_line = "We are highly impressed and would like to proceed with scheduling an interview. Please reply to this email to confirm your availability."
    elif match_score >= 50:
        tone = "Professional and balanced. Acknowledge strengths while politely outlining the required gap."
        closing_line = "We encourage you to use the feedback below for future applications. We may contact you for other roles."
    else:
        tone = "Polite and constructive. Gently decline the application for now, providing clear, actionable feedback."
        closing_line = "While we move forward with other candidates at this time, we encourage you to gain the noted experience and apply for future roles."

    prompt = f"""
    Generate a professional and personalized email to a job candidate with the following details. 
    The email must adhere to a {tone}.

    **Candidate Details:**
    - Name: {candidate_name}
    - Job Applied For: {job_title}
    - Match Score (0-100): {match_score}
    - Match Summary/Remark: "{remark}"
    - Critical Missing Skills: {missing_skills_str}

    **Email Structure Requirements:**
    1. **Salutation:** Start with "Dear [Candidate Name]".
    2. **Acknowledge Application:** Briefly thank them for their interest.
    3. **Provide Context:** Mention the summary remark to justify the result. Don't show the score.
    4. **Constructive Feedback:** Explicitly mention the missing skills as areas for development. (Use the list: {missing_skills_str}).
    5. **Closing:** Use the closing line: "{closing_line}"
    6. **Signature Requirements:**The email body must end with the final message, followed by the text: 
    "\\n\\nSincerely,\\n\\nThe Hiring Team"
    (Note: You must use the JSON newline escape sequence '\\n' to separate the lines.)



    Output the result strictly in the required JSON format.


    **EXAMPLE (Score 65% - Professional and Balanced Tone):**
    ```json
    {{
      "subject": "Update on Your Application for Senior Cloud Solutions Architect",
      "body": "Dear Alex Chen,\\n\\nThank you for your interest in the Senior Cloud Solutions Architect position and for taking the time to submit your application. \\n\\nYour profile showed excellent technical alignment, especially in cloud architecture and Terraform. This strong foundation is highly commendable.\\n\\nTo fully align with the senior requirements of this role, we recommend focusing on gaining further experience in specific areas. The critical skills currently missing include CI/CD pipeline management, multi-cloud governance experience, and advanced Python scripting for automation.\\n\\nWe encourage you to use the feedback below for future applications. We may contact you for other roles.\\n\\nSincerely,\\n\\nThe Hiring Team"
    }}
    ```
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7, 
                response_mime_type="application/json", 
                response_schema=get_email_schema(),
            )
        )
        cleaned_json_str = clean_llm_response(response.text)
        return json.loads(cleaned_json_str)

    except json.JSONDecodeError:
        return {"error": f"Failed to decode JSON response from API. Raw output: {response.text}"}
    except Exception as e:
        return {"error": f"An error occurred during API call: {e}"}


# if __name__ == '__main__':

#     candidate_data = {
#         "candidate_name": "Alex Chen",
#         "job_title": "Senior Cloud Solutions Architect",
#         "match_results": {
#             "match_score": 65,
#             "summary_remark": "Excellent technical alignment, especially in cloud architecture and Terraform. Focus on gaining experience in multi-cloud governance to maximize future potential.",
#             "missing_skills": ["CI/CD pipeline management", "Multi-cloud governance experience", "Advanced Python scripting for automation"]
#         }
#     }
    
#     print("--- Generating Personalized Feedback Email with Gemini API ---")
    
#     email_output = generate_feedback_email(
#         candidate_name=candidate_data["candidate_name"],
#         job_title=candidate_data["job_title"],
#         match_score=candidate_data["match_results"]["match_score"],
#         remark=candidate_data["match_results"]["summary_remark"],
#         missing_skills_list=candidate_data["match_results"]["missing_skills"]
#     )

#     print("\n" + "="*70)
#     print(f"Generated Email for: {candidate_data['candidate_name']}")
#     print("="*70)
    
#     if "error" in email_output:
#         print(f"**Error:** {email_output['error']}")
#     else:
#         print(f"Subject: {email_output.get('subject')}")
#         print("-" * 50)
#         print(email_output.get('body'))
            
#     print("="*70)