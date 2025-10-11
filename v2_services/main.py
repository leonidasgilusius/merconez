from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

jobs = {}

# --- Pydantic Models ---
class Job(BaseModel):
    jobId: str
    status: str
    result: dict | None = None

# UPDATED: The request model now needs to know languages for OCR and MT
class DocumentTranslationRequest(BaseModel):
    image_file_path: str
    ocr_language: str # Example: "ENGLISH"
    mt_source_language: str # Example: "en"
    mt_target_language: str # Example: "hi"


# --- Orchestration Logic ---
# UPDATED: The function now accepts all language parameters
def run_document_translation_pipeline(job_id: str, image_path: str, ocr_lang: str, mt_source: str, mt_target: str):
    try:
        # Step 1: Call v1 OCR service (This part is now working)
        print(f"ORCHESTRATOR: Calling v1 OCR service for language: {ocr_lang}")
        ocr_payload = {"image_file_path": image_path, "language": ocr_lang}
        ocr_response = requests.post("http://127.0.0.1:5003/api/v1/ocr/jobs", json=ocr_payload)
        ocr_response.raise_for_status()
        ocr_job_id = ocr_response.json()["jobId"]
        
        # Step 2: Poll for OCR Result
        extracted_text = ""
        while True:
            # ... (polling logic is the same)
            ocr_status_response = requests.get(f"http://127.0.0.1:5003/api/v1/ocr/jobs/{ocr_job_id}")
            ocr_status_response.raise_for_status()
            ocr_data = ocr_status_response.json()
            if ocr_data["status"] == "completed":
                extracted_text = ocr_data["result"]["text"]
                print(f"ORCHESTRATOR: OCR completed.")
                break
            elif ocr_data["status"] == "failed":
                raise Exception(f"OCR service failed: {ocr_data['result'].get('error', 'Unknown error')}")
            time.sleep(2)

        # Step 3: Call v1 MT Service with the extracted text and languages
        print(f"ORCHESTRATOR: Sending extracted text to MT service for {mt_source}->{mt_target} translation.")
        
        # UPDATED: The JSON payload for MT now includes all required fields
        mt_payload = {
            "text": extracted_text,
            "sourceLang": mt_source,
            "targetLang": mt_target
        }
        mt_response = requests.post("http://127.0.0.1:5004/api/v1/translate", json=mt_payload)
        mt_response.raise_for_status()
        translated_text = mt_response.json()["translatedText"]
        print(f"ORCHESTRATOR: MT completed.")
        
        # Step 4: Finalize the v2 job
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = {"extracted_text": extracted_text, "translated_text": translated_text}
        
    except Exception as e:
        print(f"ORCHESTRATOR ERROR: Pipeline failed for job {job_id}. Reason: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

# --- API Endpoints ---
@app.post("/api/v2/translate-document", response_model=Job, status_code=202)
async def start_document_translation_job(request: DocumentTranslationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    
    # UPDATED: Pass all language parameters to the background task
    background_tasks.add_task(
        run_document_translation_pipeline,
        job_id,
        request.image_file_path,
        request.ocr_language,
        request.mt_source_language,
        request.mt_target_language
    )
    return {"jobId": job_id, "status": "processing", "result": None}

@app.get("/api/v2/translate-document/jobs/{job_id}", response_model=Job)
async def get_document_translation_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}