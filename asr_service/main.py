from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

jobs = {}

class Job(BaseModel):
    jobId: str
    status: str
    result: dict | None = None

class AsrRequest(BaseModel):
    # The user will provide the path to a local file for our script to use.
    audio_file_path: str

def process_asr_task(job_id: str, file_path: str):
    asr_api_url = os.getenv("ASR_API_URL")
    asr_access_token = os.getenv("ASR_ACCESS_TOKEN")

    if not asr_api_url or not asr_access_token:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": "Server configuration error: Missing ASR API credentials"}
        return

    print(f"BACKGROUND TASK: Started ASR processing for job: {job_id}")

    headers = {"access-token": asr_access_token}

    try:
        # The API expects the audio file as form-data
        with open(file_path, "rb") as audio_file:
            files = {
                "audio_file": (os.path.basename(file_path), audio_file, "audio/wav")
            }
            response = requests.post(asr_api_url, headers=headers, files=files, verify=False)
            response.raise_for_status()

        api_response_data = response.json()
        
        if api_response_data.get("status") == "success":
            # The response key is "recognized_text" according to the docs
            recognized_text = api_response_data["data"]["recognized_text"]
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {"text": recognized_text}
        else:
            error_message = api_response_data.get("message", "Unknown ASR API error")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["result"] = {"error": error_message}
            
    except Exception as e:
        print(f"BACKGROUND TASK ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

    print(f"BACKGROUND TASK: Finished ASR processing for job: {job_id}")

@app.post("/api/v1/asr/jobs", response_model=Job, status_code=202)
async def start_asr_job(request: AsrRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    
    # Check if the file exists before starting the background task
    if not os.path.exists(request.audio_file_path):
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": "File not found"}
        raise HTTPException(status_code=400, detail=f"File not found at path: {request.audio_file_path}")
    
    background_tasks.add_task(process_asr_task, job_id, request.audio_file_path)
    
    return {"jobId": job_id, "status": "processing", "result": None}

@app.get("/api/v1/asr/jobs/{job_id}", response_model=Job)
async def get_asr_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"jobId": job_id, **job}