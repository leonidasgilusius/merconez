from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import os
import requests

app = FastAPI()

# In-memory dictionary to store job statuses.
# In a production environment, you would use a more persistent store like Redis or a database.
jobs = {}

# --- Pydantic Models ---

class Job(BaseModel):
    """Represents the structure of a job's status and result."""
    jobId: str
    status: str
    result: dict | None = None

class TranslationRequest(BaseModel):
    """Defines the request body for initiating a translation."""
    text: str
    language1: str
    language2: str


# --- Background Task Logic ---

def process_translation_task(job_id: str, text: str, language1: str, language2: str):
    """
    This function runs in the background to process the translation request.
    It calls the external Bhashini MT API and updates the job status upon completion or failure.
    """
    lang1_upper = language1.upper()
    lang2_upper = language2.upper()

    print(f"BACKGROUND TASK: Started translation for job: {job_id}")

    mt_api_url = os.getenv(f"MT_{lang1_upper}_{lang2_upper}_API_URL")
    mt_access_token = os.getenv(f"MT_{lang1_upper}_{lang2_upper}_ACCESS_TOKEN")

    # Handle configuration errors
    if not mt_api_url or not mt_access_token:
        print(f"BACKGROUND TASK ERROR: Server configuration error for job {job_id}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": "Server configuration error: Missing API URL or Token"}
        return

    headers = {"access-token": mt_access_token}
    payload = {"input_text": text}

    try:
        # Call the external Bhashini MT API
        # verify=False is used here as in the original code, but be cautious with this in production.
        response = requests.post(mt_api_url, headers=headers, json=payload, verify=False)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        api_response_data = response.json()

        # Check the status within the API response body
        if api_response_data.get("status") == "success":
            translated_text = api_response_data["data"]["output_text"]
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {"translatedText": translated_text}
        else:
            error_message = api_response_data.get("message", "Unknown Bhashini API error")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["result"] = {"error": f"Bhashini API Error: {error_message}"}

    except Exception as e:
        # Catch any exception during the API call or response processing
        print(f"BACKGROUND TASK ERROR: An exception occurred for job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

    print(f"BACKGROUND TASK: Finished translation processing for job: {job_id}")


# --- API Endpoints ---

@app.post("/api/v1/translate/jobs", response_model=Job, status_code=202)
async def start_translation_job(request: TranslationRequest, background_tasks: BackgroundTasks):
    """
    Accepts a translation request, creates a new job, and starts the processing in the background.
    Returns immediately with a job ID.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}

    # Add the long-running translation task to the background queue
    background_tasks.add_task(
        process_translation_task,
        job_id,
        request.text,
        request.language1,
        request.language2
    )

    return {"jobId": job_id, "status": "processing", "result": None}


@app.get("/api/v1/translate/jobs/{job_id}", response_model=Job)
async def get_translation_job_status(job_id: str):
    """
    Poll this endpoint with a job ID to get the current status and result of a translation job.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"jobId": job_id, **job}
