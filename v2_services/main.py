from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
import requests
import os
from dotenv import load_dotenv
import base64

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# In-memory "database" to store job statuses
jobs = {}

# --- Pydantic Models ---
class Job(BaseModel):
    jobId: str
    status: str
    result: dict | None = None

# This model MUST match the payload sent by the V2 orchestrator
class TTSRequest(BaseModel):
    text: str
    language: str

# --- Background Task ---
def run_tts_task(job_id: str, text: str, language: str):
    """
    This function runs in the background to call the actual Bhashini TTS API.
    """
    try:
        # Step 1: Dynamically construct the .env variable keys
        # e.g., TTS_MALAYALAM_API_URL
        lang_upper = language.upper()
        api_url_key = f"TTS_{lang_upper}_API_URL"
        access_token_key = f"TTS_{lang_upper}_ACCESS_TOKEN"

        api_url = os.getenv(api_url_key)
        access_token = os.getenv(access_token_key)

        if not api_url or not access_token:
            raise ValueError(f"API URL or Access Token not found in .env for {api_url_key}")

        print(f"TTS_SERVICE: Calling Bhashini API at {api_url} for job {job_id}")

        # Step 2: Prepare the payload and headers for the Bhashini API
        # This payload structure is an assumption based on common TTS APIs.
        # You may need to adjust it to match the exact Bhashini spec.
        payload = {
            "input_text": text,
            "gender": "female" # Or another required parameter
        }
        
        headers = {
            "access-token": access_token,
            "Content-Type": "application/json"
        }

        # Step 3: Make the call to the actual Bhashini API
        response = requests.post(api_url, json=payload, headers=headers, verify=False)
        response.raise_for_status()
        
        api_result = response.json()
        
        # Step 4: Save the audio output
        # Assuming the API returns base64 encoded audio
        if "data" in api_result and "output_audio" in api_result["data"]:
            audio_base64 = api_result["data"]["output_audio"]
            
            # Ensure an 'outputs' directory exists
            output_dir = "outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            # Create a unique file path for the output audio
            audio_file_path = os.path.join(output_dir, f"{job_id}.wav")
            
            with open(audio_file_path, "wb") as audio_file:
                audio_file.write(base64.b64decode(audio_base64))
            
            # Step 5: Update the job status with the path to the file
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {"audio_file_path": audio_file_path}
            print(f"TTS_SERVICE: Job {job_id} completed. Audio saved to {audio_file_path}")
        else:
            raise ValueError("Bhashini API response did not contain expected audio data.")

    except Exception as e:
        print(f"TTS_SERVICE ERROR: Job {job_id} failed. Reason: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

# --- API Endpoints ---
@app.post("/api/v1/tts/jobs", response_model=Job, status_code=202)
async def start_tts_job(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Starts an asynchronous Text-to-Speech job.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    
    background_tasks.add_task(
        run_tts_task, 
        job_id, 
        request.text, 
        request.language
    )
    
    return {"jobId": job_id, "status": "processing", "result": None}

@app.get("/api/v1/tts/jobs/{job_id}", response_model=Job)
async def get_tts_status(job_id: str):
    """
    Polls for the status and result of a TTS job.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"jobId": job_id, **job}
