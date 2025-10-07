import os
import json
from google import genai
from google.genai import types

from dotenv import load_dotenv

load_dotenv() 


def get_job_description_schema():
    """
    Defines the JSON output schema using standard Python dictionary structure.
    """
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "job_description": types.Schema(
                type=types.Type.STRING,
                description="The full, comprehensive job description formatted in Markdown."
            )
        },
        required=["job_description"]
    )


def generate_job_description(job_title, years_of_experience, must_have_skills, 
                             company_name, employment_type, industry, location):
    

    if not os.getenv("GEMINI_API_KEY"):
         return ("Error: GEMINI_API_KEY is not set. Please check your .env file.")

    try:
        client = genai.Client() 
    except Exception as e:
        return (f"Error initializing Gemini client. Details: {e}")


    
    markdown_example = """
    **Job Title:** Sample Data Analyst
    **Company:** Example Corp
    **Location:** Remote

    ## Job Summary
    We are looking for a skilled Data Analyst to join our team and turn data into actionable insights, requiring 2 years of relevant experience.

    ## Responsibilities
    - Collect and analyze large datasets from various sources.
    - Develop and maintain reporting dashboards using Python and SQL.
    - Collaborate with stakeholders to define key performance indicators.
    - Ensure data integrity and quality across all reports.

    ## Required Qualifications
    - Minimum of 2 years of professional experience in data analysis.
    - Proficient in: SQL, Python, and Tableau.
    - Strong attention to detail and analytical thinking.

    ## What We Offer
    - Competitive salary and flexible work environment.
    - Opportunities for professional growth and skill development.
    - Comprehensive health and wellness benefits.
    """
    
    escaped_markdown = json.dumps(markdown_example.strip())
    escaped_markdown = escaped_markdown[1:-1] 
    
    prompt = f"""
    Generate a comprehensive, professional, and well-structured Job Description 
    formatted entirely in **Markdown** based on the following specifications:

    1. **Company:** {company_name}
    2. **Job Title:** {job_title}
    3. **Employment Type:** {employment_type}
    4. **Location:** {location}
    5. **Industry:** {industry}
    6. **Minimum Experience:** {years_of_experience} years
    7. **Must-Have Skills:** {must_have_skills}

    The Markdown content MUST include these sections:
    - **Job Summary**
    - **Responsibilities**
    - **Required Qualifications** (Must include the experience and skill requirements)
    - **What We Offer**
    
    ---
    
    **JSON Output Example:**
    
    ```json
    {{
      "job_description": "{escaped_markdown}"
    }}
    ```
    
    Place the complete Markdown content you generate into the 'job_description' key 
    of the required JSON format.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="application/json", 
                response_schema=get_job_description_schema(),
            )
        )
        
        json_data = json.loads(response.text)
        return json_data.get("job_description", "Error: Could not find 'job_description' key in JSON response.")

    except json.JSONDecodeError:
        return f"An error occurred: Failed to decode JSON response from API. Raw output: {response.text}"
    except Exception as e:
        return f"An error occurred during API call: {e}"



# if __name__ == '__main__':
#     sample_inputs = {
#         "job_title": "Senior Cloud Solutions Architect",
#         "years_of_experience": 5,
#         "must_have_skills": "AWS, Kubernetes, Terraform, Python, CI/CD",
#         "company_name": "CloudSphere Innovations",
#         "employment_type": "Full-time",
#         "industry": "Cloud Computing and FinTech",
#         "location": "New York, Hybrid"
#     }

#     print("--- Generating Job Description with Gemini API (JSON Mode) ---")
    
#     jd_output = generate_job_description(**sample_inputs)

#     print("\n" + "="*50)
#     print(f"Generated JD for: {sample_inputs['job_title']} at {sample_inputs['company_name']}")
#     print("="*50)
    
#     if jd_output.startswith("Error"):
#         print(jd_output)
#     else:
#         print(jd_output)
    
#     print("="*50)