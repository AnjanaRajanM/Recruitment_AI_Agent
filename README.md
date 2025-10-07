# Recruitment AI Agent

> Recruitment AI Agent: A full-stack FastAPI / Streamlit application using Gemini for semantic resume scoring, JD generation, and reliable Batch Personalized Emails. Optimized with a hybrid LLM calling strategy for maximum efficiency and stability.

***

## Project Overview

This project implements a fully functional AI-powered agent designed to automate the initial screening and candidate communication workflow for HR professionals. It streamlines the process from Job Description (JD) input to final personalized email feedback, leveraging advanced LLM capabilities while maintaining a highly optimized and stable backend architecture.

***

## Key Features

The application provides a comprehensive end-to-end solution:

1.  **Flexible JD Input:** Input the Job Description via three methods: File Upload (PDF/DOCX), Manual Paste, or AI Generation (by providing core parameters).
2.  **Semantic Resume Matching:** Upload up to 10 candidate resumes for simultaneous processing. The system calculates a precise Match Score (0-100) based on the semantic alignment with the JD.
3.  **Structured Candidate Data:** For each resume, the API returns clean, structured JSON containing the Match Score, a Summary Remark, a list of Missing Skills, and the Candidate Name/Email extracted from the resume.
4.  **Optimized Email Generation:** Generate professional, personalized interview or rejection emails based on the match score.
    * Batch Call: Generate emails for all candidates in a single, efficient API request.
    * Single Fallback: Option to re-generate an individual email instantly.

***

## Architecture and Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **Backend API** | **FastAPI** | Provides robust, asynchronous API endpoints for all business and AI logic (JD Generation, Matching, Batch Emails). |
| **Frontend UI** | **Streamlit** | Interactive user interface for file uploads, input forms, and dynamic display of results and dataframes. |
| **AI Engine** | **Google Gemini API** (`gemini-2.5-flash`) | Core model for all complex reasoning, scoring, and generation tasks. Selected for its speed, low cost, and high performance with structured output. |
| **Pre-Processing** | **SpaCy** | Used for preliminary text processing and advanced keyword/entity extraction to augment and guide the LLM's performance. |

***

## AI Logic and Optimization (Mandatory Explanation)

The architecture is built on a **Hybrid LLM Strategy** to ensure the best balance between speed, cost, and reliability.

### 1. Hybrid LLM Calling Strategy

We treat the LLM as a tool and use the most efficient call type for the specific task:

* **Individual Calls (`/match-resume`):** Used for resume matching. This task requires complex, multi-step analysis across two large documents (JD + Resume). Individual calls are necessary here to ensure high accuracy and avoid exceeding context limits in a batch.
* **Batch Call (`/generate-batch-emails`):** Used for generating candidate emails. This task consolidates the required data (scores, names, remarks) for up to 10 candidates into a **single Gemini API request**. This significantly reduces overall latency and API cost compared to 10 separate calls.

### 2. Structured Output & Reliability

All core API endpoints rely on **JSON Schema enforcement** (`response_schema` in the `GenerateContentConfig`) to guarantee reliable output:

* **Pydantic Schema:** FastAPI models map directly to the Gemini output schema, ensuring smooth data flow.
* **Data Integrity:** The prompt strictly enforces that the `missing_skills` field must always return a **JSON Array (`[]`)**, even if it is empty. This prevents Python runtime errors (`TypeError` on `.join()`) and validates against the schema consistently.

### 3. Prompt Augmentation

The `match-resume` endpoint utilizes a **SpaCy-powered pre-processing step**:
* The `extract_entities_spacy` function uses **lemmatization** and **noun chunking** to extract high-signal keywords ("machine learning," "cloud infrastructure") instead of noisy single tokens.
* These clean keywords are injected into the Gemini prompt to guide the LLM's attention, resulting in a more focused and accurate semantic score.

***

## Setup Instructions

### 1. Prerequisites

* Python 3.8+
* A **GEMINI_API_KEY** from Google AI Studio.

### 2. Installation

1.  **Clone the repository:**
    ```
    git clone [YOUR_REPO_URL]
    cd recruitment-ai-agent
    ```

2.  **Create and activate a virtual environment:**
    ```
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies (requires a `requirements.txt` file):**
    ```
    pip install -r requirements.txt
    ```

4.  **Download the required SpaCy model:**
    ```
    python -m spacy download en_core_web_md
    ```

### 3. Configuration

Create a file named `.env` in the project root directory and add your API key:
