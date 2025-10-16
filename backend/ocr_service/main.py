from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import os
import requests

app = FastAPI()

jobs = {}

class Job(BaseModel):
    jobId: str
    status: str
    result: dict | None = None

class OcrRequest(BaseModel):
    image_file_path: str
    language: str

def process_ocr_task(job_id: str, file_path: str, language: str):
    ocr_api_url = os.getenv(f"OCR_{language}_API_URL")
    ocr_access_token = os.getenv(f"OCR_{language}_ACCESS_TOKEN")

    if not ocr_api_url or not ocr_access_token:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": "Server configuration error: Missing OCR API credentials"}
        return

    print(f"BACKGROUND TASK: Started OCR processing for job: {job_id}")

    headers = {"access-token": ocr_access_token}

    try:
        # The API expects the image file as form-data with the key "file" 
        with open(file_path, "rb") as image_file:
            files = {
                "file": (os.path.basename(file_path), image_file, "image/jpeg")
            }
            response = requests.post(ocr_api_url, headers=headers, files=files, verify=False)
            response.raise_for_status()

        api_response_data = response.json()
        
        if api_response_data.get("status") == "success":
            # The response key is "decoded_text" according to the docs [cite: 67]
            decoded_text = api_response_data["data"]["decoded_text"]
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {"text": decoded_text}
        else:
            error_message = api_response_data.get("message", "Unknown OCR API error")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["result"] = {"error": error_message}
            
    except Exception as e:
        print(f"BACKGROUND TASK ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

    print(f"BACKGROUND TASK: Finished OCR processing for job: {job_id}")

@app.post("/api/v1/ocr/jobs", response_model=Job, status_code=202)
async def start_ocr_job(request: OcrRequest, background_tasks: BackgroundTasks):
    language = request.language.upper()
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    
    if not os.path.exists(request.image_file_path):
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": "File not found"}
        raise HTTPException(status_code=400, detail=f"File not found at path: {request.image_file_path}")
    
    background_tasks.add_task(process_ocr_task, job_id, request.image_file_path, language)
    
    return {"jobId": job_id, "status": "processing", "result": None}

@app.get("/api/v1/ocr/jobs/{job_id}", response_model=Job)
async def get_ocr_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"jobId": job_id, **job}