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

class TtsRequest(BaseModel):
    text_to_speak: str
    gender: str # As per the docs, this should be "male" or "female" 

def process_tts_task(job_id: str, text: str, gender: str):
    tts_api_url = os.getenv("TTS_API_URL")
    tts_access_token = os.getenv("TTS_ACCESS_TOKEN")

    if not tts_api_url or not tts_access_token:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": "Server configuration error: Missing TTS API credentials"}
        return

    print(f"BACKGROUND TASK: Started TTS processing for job: {job_id}")

    headers = {"access-token": tts_access_token}
    
    # Construct the JSON payload as per the API specification 
    payload = {
        "text": text,
        "gender": gender
    }

    try:
        response = requests.post(tts_api_url, headers=headers, json=payload, verify=False)
        response.raise_for_status()

        api_response_data = response.json()
        
        if api_response_data.get("status") == "success":
            # The response key is "s3_url" inside the "data" object [cite: 88, 87]
            s3_url = api_response_data["data"]["s3_url"]
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {"audio_url": s3_url}
        else:
            error_message = api_response_data.get("message", "Unknown TTS API error")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["result"] = {"error": error_message}
            
    except Exception as e:
        print(f"BACKGROUND TASK ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

    print(f"BACKGROUND TASK: Finished TTS processing for job: {job_id}")

@app.post("/api/v1/tts/jobs", response_model=Job, status_code=202)
async def start_tts_job(request: TtsRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    
    background_tasks.add_task(process_tts_task, job_id, request.text_to_speak, request.gender)
    
    return {"jobId": job_id, "status": "processing", "result": None}

@app.get("/api/v1/tts/jobs/{job_id}", response_model=Job)
async def get_tts_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"jobId": job_id, **job}