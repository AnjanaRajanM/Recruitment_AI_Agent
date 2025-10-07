import streamlit as st
import pandas as pd
import docx2txt
from PyPDF2 import PdfReader
import requests 
import urllib.parse


API_BASE_URL = "http://localhost:8000" 


st.set_page_config(
    page_title="JD Input Module",
    layout="wide",
    initial_sidebar_state="expanded"
)


if 'job_description_text' not in st.session_state:
    st.session_state.job_description_text = ""


def extract_text_from_upload(uploaded_file):
    """Extracts text from PDF or DOCX file. (No change here)"""
    text = ""
    file_type = uploaded_file.type
    
    try:
        if file_type == "application/pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = docx2txt.process(uploaded_file)
        elif file_type == "application/msword":
             st.warning("Handling .doc files is complex and not fully supported by standard libraries. Please use .docx or PDF.")
             return None
        else:
            st.error(f"Unsupported file type: {uploaded_file.type}. Please upload PDF or DOCX.")
            return None
        return text
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None


def generate_jd_via_api(job_title, years_of_experience, must_have_skills, company_name, employment_type, industry, location):
    """Calls the FastAPI endpoint for JD generation."""
    url = f"{API_BASE_URL}/generate-jd"
    payload = {
        "job_title": job_title, 
        "years_of_experience": years_of_experience, 
        "must_have_skills": must_have_skills,   
        "company_name": company_name,          
        "employment_type": employment_type,    
        "industry": industry,
        "location": location
    }

    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() 
        return response.json().get("job_description", "Error: JD field missing from API response.")
    except requests.exceptions.RequestException as e:
        error_detail = response.json().get("detail") if response.content else "Unknown error."
        return f"Error connecting to JD AI service ({response.status_code if 'response' in locals() else 'N/A'}): {error_detail}"
    except Exception as e:
        return f"Unexpected error during JD generation: {e}"


def generate_email_via_api(name, title, score, remark, missing_skills_str):
    """Calls the FastAPI endpoint for single email generation (Fallback)."""
    url = f"{API_BASE_URL}/generate-email" 
    
    missing_skills_list = [s.strip() for s in missing_skills_str.split(',') if s.strip()]

    payload = {
        "candidate_name": name,
        "job_title": title,
        "match_score": score,
        "remark": remark,
        "missing_skills": missing_skills_list
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json() 
    except requests.exceptions.RequestException as e:
        error_detail = response.json().get("detail") if response.content else "Unknown error."
        return {"error": f"Single Email API Error: {response.status_code if 'response' in locals() else 'N/A'} - {error_detail}"}
    except Exception as e:
        return {"error": f"Unexpected error during single email generation: {e}"}

def get_matching_data_gemini(resume_text, jd_text):
    """
    Calls the FastAPI endpoint for resume matching and maps its output.
    """
    st.text(f"Analyzing {len(resume_text)} characters.")

    url = f"{API_BASE_URL}/match-resume"
    payload = {
        "jd_text": jd_text,
        "resume_text": resume_text
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        match_output = response.json()

        candidate_name = match_output.get("candidate_name", "Unknown Candidate")
        candidate_email = match_output.get("candidate_email", "no-email@example.com")
        

        return {
            "Candidate Name": candidate_name,    
            "Candidate Email": candidate_email,  
            "Score": match_output.get("match_score", 0),
            "Missing Skills": ", ".join(match_output.get("missing_skills", [])), 
            "Remarks": match_output.get("summary_remark", "No summary provided.")
        }
    except requests.exceptions.RequestException as e:
        error_detail = response.json().get("detail") if response.content else "Unknown error."
        return {
            "Score": 0,
            "Missing Skills": f"API Error: {response.status_code if 'response' in locals() else 'N/A'} - {error_detail}",
            "Remarks": "Processing failed. Check FastAPI server logs."
        }
    except Exception as e:
        return {
            "Score": 0,
            "Missing Skills": f"Unknown Error: {e}",
            "Remarks": "Processing failed."
        }




def generate_batch_emails_via_api(candidate_results_list, job_title):
    """
    Calls the FastAPI endpoint for batch email generation.
    It expects the API to return a list of email objects.
    """
    url = f"{API_BASE_URL}/generate-batch-emails" 
    payload_list = []
    for result in candidate_results_list:
        missing_skills_list = [s.strip() for s in result["Missing Skills"].split(',') if s.strip()]
        
        payload_list.append({
            "candidate_name": result["Candidate Name"],
            "job_title": job_title, 
            "match_score": result["Score"],
            "remark": result["Remarks"],
            "missing_skills": missing_skills_list
        })
        
    full_payload = {
        "job_title": job_title,
        "candidates": payload_list
    }

    try:
        response = requests.post(url, json=full_payload)
        response.raise_for_status()
        
        return response.json() 
    
    except requests.exceptions.RequestException as e:
        error_detail = response.json().get("detail") if response.content else "Unknown error."
        return {"error": f"Batch Email API Error: {response.status_code if 'response' in locals() else 'N/A'} - {error_detail}"}
    except Exception as e:
        return {"error": f"Unexpected error during batch email generation: {e}"}



st.title("Job Description Input Module")
st.markdown("Choose one of the three methods below to input the Job Description.")


tab1, tab2, tab3 = st.tabs(["📤 Upload File", "✍️ Manual Input", "🤖 Generate JD"])


with tab1:
    st.header("Upload a Job Description File")
    uploaded_file = st.file_uploader(
        "Upload a PDF or DOCX file",
        type=["pdf", "docx"],
        help="The text will be automatically extracted from the file."
    )

    if uploaded_file is not None:
        with st.spinner('Extracting text...'):
            extracted_text = extract_text_from_upload(uploaded_file)
            
            if extracted_text and len(extracted_text.strip()) > 50: 
                st.session_state.job_description_text = extracted_text
                st.success(f"Successfully extracted text from **{uploaded_file.name}**.")
            elif extracted_text is not None:
                 st.warning("Extracted text seems too short or empty. Please review the file content.")
                 st.session_state.job_description_text = extracted_text if extracted_text else ""


with tab2:
    st.header("Enter Job Description Manually")
    manual_jd = st.text_area(
        "Paste or type the full Job Description here:",
        height=400,
        key="manual_jd_input",
        placeholder="E.g., We are looking for a Senior Software Engineer..."
    )

    if st.button("Use Manual Input", type="primary"):
        if manual_jd.strip():
            st.session_state.job_description_text = manual_jd
            st.success("Manual Job Description stored.")
        else:
            st.error("Please enter the Job Description text.")


with tab3:
    st.header("Generate Job Description with AI")
    with st.form("jd_generation_form"):
        col_t, col_e = st.columns(2)
        with col_t:
            job_title = st.text_input("Job Title", key="gen_title", value="Data Scientist")
        with col_e:
            years_of_experience = st.number_input("Years of Experience (min)", min_value=0, max_value=30, value=3, key="gen_exp")

        must_have_skills = st.text_input(
            "Must-have Skills (comma-separated)", 
            key="gen_skills", 
            value="Python, SQL, Machine Learning, TensorFlow"
        )
        
        company_name = st.text_input("Company Name", key="gen_company", value="Tech Innovators Inc.")

        col_type, col_ind, col_loc = st.columns(3)
        with col_type:
            employment_type = st.selectbox(
                "Employment Type", 
                options=["Full-time", "Part-time", "Contract", "Internship"], 
                key="gen_type"
            )
        with col_ind:
            industry = st.text_input("Industry", key="gen_industry", value="Technology")
        with col_loc:
            location = st.text_input("Location", key="gen_location", value="Remote")

        submitted = st.form_submit_button("Generate JD and Use It", type="primary")


    if submitted:
        if job_title and must_have_skills and company_name:
            with st.spinner('Generating Job Description.'):
                generated_text = generate_jd_via_api(
                    job_title=job_title,
                    years_of_experience=years_of_experience,
                    must_have_skills=must_have_skills,
                    company_name=company_name,
                    employment_type=employment_type,
                    industry=industry,
                    location=location
                )


            if generated_text.startswith("Error"):
                st.error(f"AI Generation Error: {generated_text}")
            else:
                st.session_state.job_description_text = generated_text
                st.success("Job Description generated and stored! See the output below.")
                st.markdown("---")
                st.subheader("Generated Job Description Preview:")
                st.markdown(generated_text) 
        else:
            st.error("Please fill out all required fields (Job Title, Skills, Company Name) to generate the JD.")



st.markdown("---")


# if st.session_state.job_description_text:
#     st.info("A Job Description is ready for processing.")
#     with st.expander("Show Stored JD Text"):
#         st.code(st.session_state.job_description_text)
        
# else:
#     st.warning("No Job Description has been input yet. Please use one of the tabs above.")


if st.session_state.job_description_text:
    
    st.header("Resume Upload and Candidate Matching")
 
    st.subheader("Upload Candidate Resumes (Max 10)")
    uploaded_resumes = st.file_uploader(
        "Select PDF or DOCX files",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="resume_upload_key"
    )

    if uploaded_resumes:
        if len(uploaded_resumes) > 10:
            st.warning("You have uploaded more than 10 files. Only the first 10 will be processed.")
            uploaded_resumes = uploaded_resumes[:10]
            
        if st.button(f"Analyze {len(uploaded_resumes)} Resume(s)", type="primary"):
            st.session_state.resume_results = [] 
            
            with st.spinner(f"Processing and matching {len(uploaded_resumes)} resume(s)."):
                jd_text = st.session_state.job_description_text
                
                for i, file in enumerate(uploaded_resumes):
                    resume_text = extract_text_from_upload(file)
                    
                    if not resume_text or len(resume_text.strip()) < 50:
                        st.warning(f"Skipping **{file.name}**: Could not extract sufficient text.")
                        continue
                        
                    matching_data = get_matching_data_gemini(resume_text, jd_text)
                    
                    result = {
                        "Candidate File": file.name,
                        **matching_data,
                    }
                    st.session_state.resume_results.append(result)
                
            st.success("Analysis complete! See results below.")
            


    if 'resume_results' in st.session_state and st.session_state.resume_results:
        st.markdown("---")
        st.subheader("📊 Candidate Matching Results")

        df = pd.DataFrame(st.session_state.resume_results)
        df_display = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
        df_display.index = df_display.index + 1

        cols_to_display = ["Candidate File", "Candidate Name", "Score", "Remarks", "Missing Skills"]

        def color_score(val):
            color = 'green' if val >= 80 else ('orange' if val >= 60 else 'red')
            return f'background-color: {color}; color: white'

        st.dataframe(
            df_display[cols_to_display].style.applymap(color_score, subset=['Score']),
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score (%)",
                    help="Matching score out of 100",
                    format="%d",
                    min_value=0,
                    max_value=100,
                )
            },
            hide_index=False,
            use_container_width=True
        )


        st.markdown("---")
        st.subheader("Personalized Email Generation")

        job_title_for_email = st.session_state.job_description_text.split('\n')[0].strip() 
        if len(job_title_for_email) > 100: job_title_for_email = "The Applied Role" 

        if 'batch_emails_output' not in st.session_state:
            st.session_state.batch_emails_output = {} 

        candidates_for_batch = st.session_state.resume_results

        if st.button("Generate ALL Personalized Emails (Batch Call)", key="generate_all_emails_btn", type="primary"):
            if not candidates_for_batch:
                st.warning("No candidate results to process.")
            else:
                with st.spinner(f'Generating professional e-mails for {len(candidates_for_batch)} candidates in one batch.'):
                    batch_emails_result = generate_batch_emails_via_api(
                        candidate_results_list=candidates_for_batch,
                        job_title=job_title_for_email
                    )
                
                if "error" in batch_emails_result:
                    st.error(f"Batch E-mail Generation Error: {batch_emails_result['error']}")
                    st.session_state.batch_emails_output = {}
                else:
                    st.success(f"Successfully generated {len(batch_emails_result)} e-mails in a single API call.")
                    email_map = {email['candidate_name']: email for email in batch_emails_result}
                    st.session_state.batch_emails_output = email_map


        for i, result in df_display.iterrows():
            name = result["Candidate Name"]
            score = result["Score"]
            
            with st.expander(f"Review Email: {name} (Score: {score}%)"):
                st.markdown(f"**Match Remark:** *{result['Remarks']}*")
                
                email_output = st.session_state.batch_emails_output.get(name)
                
                candidate_email_address = result.get("Candidate Email", "recipient@example.com")

                if email_output:
                    st.success("Email Ready (Generated via Batch)")
                    
                    email_subject = email_output.get('subject', 'No Subject')
                    email_body = email_output.get('body', 'No Body')
                    
                    st.info(f"Recipient Email: **{candidate_email_address}**")
                    
                    st.code(f"Subject: {email_subject}", language="text")
                    st.markdown("---")
                    st.markdown(email_body.replace('\\n', '  \n')) 
                    
                    st.markdown("---")

                else:
                    st.info("Email not yet generated by batch, or batch failed.")

                if st.button(f"Generate/Re-Generate This Email ONLY", key=f"single_gen_{i}"):
                    with st.spinner(f'Generating single email for {name}...'):
                        individual_email = generate_email_via_api(
                            name=name,
                            title=job_title_for_email,
                            score=score,
                            remark=result["Remarks"],
                            missing_skills_str=result["Missing Skills"]
                        )
                    
                    if "error" in individual_email:
                        st.error(f"Single Generation Error: {individual_email['error']}")
                    else:
                        st.session_state.batch_emails_output[name] = {
                            "candidate_name": name, 
                            "subject": individual_email["subject"],
                            "body": individual_email["body"]
                        }
                        st.rerun() 
    # else:
    #     st.subheader("Ready to start the matching process?")
    #     st.warning("Please input the Job Description using one of the methods above to unlock the Resume Analyzer.")
