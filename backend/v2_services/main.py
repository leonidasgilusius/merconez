from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
import requests

app = FastAPI(title="Bhashini V2 Orchestration Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# This is the central in-memory "database" for all orchestration jobs.
jobs = {}

# --- Pydantic Models ---

class Job(BaseModel):
    """A generic model to represent the status of any asynchronous job."""
    jobId: str
    status: str
    result: dict | None = None

# Models for the request bodies of our frameworks
class DocumentTranslationRequest(BaseModel):
    image_file_path: str

class SpeechTranslationRequest(BaseModel):
    audio_file_path: str

class TextToSpeechRequest(BaseModel):
    text: str
    gender: str = "female"

# NEW: Request model for the Speech-to-Speech pipeline
class SpeechToSpeechRequest(BaseModel):
    audio_file_path: str
    gender: str = "female"


# --- Reusable Helper Function for Polling ---

def poll_for_result(service_name: str, job_id: str, url: str) -> dict:
    """A helper function to poll any v1 service job until it's complete or fails."""
    while True:
        print(f"ORCHESTRATOR: Polling {service_name} job: {job_id}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "completed":
            print(f"ORCHESTRATOR: {service_name} job {job_id} completed.")
            return data["result"]
        elif data["status"] == "failed":
            error_details = data.get('result', {}).get('error', 'Unknown error')
            raise Exception(f"{service_name} service failed: {error_details}")
        
        time.sleep(2)


# --- Framework 1: Document (Image) Translation Pipeline (No changes) ---

def run_document_translation_pipeline(job_id: str, file_path: str):
    try:
        # Step 1: Call OCR to get Malayalam text from an image
        print("ORCHESTRATOR (DOC-PIPE): Calling v1 OCR service.")
        ocr_payload = {"image_file_path": file_path, "language": "MALAYALAM"}
        ocr_response = requests.post("http://127.0.0.1:5003/api/v1/ocr/jobs", json=ocr_payload)
        ocr_response.raise_for_status()
        ocr_job_id = ocr_response.json()["jobId"]
        ocr_result = poll_for_result("OCR", ocr_job_id, f"http://127.0.0.1:5003/api/v1/ocr/jobs/{ocr_job_id}")
        extracted_text = ocr_result["text"]

        # Step 2: Call MT to translate the extracted Malayalam text to English
        print("ORCHESTRATOR (DOC-PIPE): Calling v1 MT service.")
        mt_payload = {"text": extracted_text, "language1": "MALAYALAM", "language2": "ENGLISH"}
        mt_response = requests.post("http://127.0.0.1:5004/api/v1/translate/jobs", json=mt_payload)
        mt_response.raise_for_status()
        mt_job_id = mt_response.json()["jobId"]
        mt_result = poll_for_result("MT", mt_job_id, f"http://127.0.0.1:5004/api/v1/translate/jobs/{mt_job_id}")
        translated_text = mt_result["translatedText"]

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = {"extracted_malayalam_text": extracted_text, "translated_english_text": translated_text}
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

# --- Framework 2: Speech Translation Pipeline (No changes) ---

def run_speech_translation_pipeline(job_id: str, file_path: str):
    try:
        # Step 1: Call ASR to get Malayalam text from audio
        print("ORCHESTRATOR (SPEECH-PIPE): Calling v1 ASR service.")
        asr_payload = {"audio_file_path": file_path, "language": "MALAYALAM"}
        asr_response = requests.post("http://127.0.0.1:5001/api/v1/asr/jobs", json=asr_payload)
        asr_response.raise_for_status()
        asr_job_id = asr_response.json()["jobId"]
        asr_result = poll_for_result("ASR", asr_job_id, f"http://127.0.0.1:5001/api/v1/asr/jobs/{asr_job_id}")
        transcribed_text = asr_result["text"]

        # Step 2: Call MT to translate the transcribed Malayalam text to English
        print("ORCHESTRATOR (SPEECH-PIPE): Calling v1 MT service.")
        mt_payload = {"text": transcribed_text, "language1": "MALAYALAM", "language2": "ENGLISH"}
        mt_response = requests.post("http://127.0.0.1:5004/api/v1/translate/jobs", json=mt_payload)
        mt_response.raise_for_status()
        mt_job_id = mt_response.json()["jobId"]
        mt_result = poll_for_result("MT", mt_job_id, f"http://127.0.0.1:5004/api/v1/translate/jobs/{mt_job_id}")
        translated_text = mt_result["translatedText"]

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = {"transcribed_malayalam_text": transcribed_text, "translated_english_text": translated_text}
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

# --- Framework 3: Text-to-Speech Synthesis Pipeline (No changes) ---

def run_text_to_speech_pipeline(job_id: str, text: str, gender: str):
    try:
        # Step 1: Call MT to translate English text to Malayalam
        print("ORCHESTRATOR (TTS-PIPE): Calling v1 MT service.")
        mt_payload = {"text": text, "language1": "ENGLISH", "language2": "MALAYALAM"}
        mt_response = requests.post("http://127.0.0.1:5004/api/v1/translate/jobs", json=mt_payload)
        mt_response.raise_for_status()
        mt_job_id = mt_response.json()["jobId"]
        mt_result = poll_for_result("MT", mt_job_id, f"http://127.0.0.1:5004/api/v1/translate/jobs/{mt_job_id}")
        translated_text = mt_result["translatedText"]

        # Step 2: Call TTS to get Malayalam speech from the translated text
        print("ORCHESTRATOR (TTS-PIPE): Calling v1 TTS service.")
        tts_payload = {"text_to_speak": translated_text, "gender": gender, "language": "MALAYALAM"}
        tts_response = requests.post("http://127.0.0.1:5002/api/v1/tts/jobs", json=tts_payload)
        tts_response.raise_for_status()
        tts_job_id = tts_response.json()["jobId"]
        tts_result = poll_for_result("TTS", tts_job_id, f"http://127.0.0.1:5002/api/v1/tts/jobs/{tts_job_id}")
        audio_url = tts_result["audio_url"]
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = {"source_english_text": text, "translated_malayalam_text": translated_text, "malayalam_audio_url": audio_url}
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

# --- NEW: Framework 4: Speech-to-Speech Translation Pipeline ---

def run_speech_to_speech_pipeline(job_id: str, file_path: str, gender: str):
    try:
        # Step 1: Call ASR to get Malayalam text from audio
        print("ORCHESTRATOR (S2S-PIPE): Calling v1 ASR service.")
        asr_payload = {"audio_file_path": file_path, "language": "MALAYALAM"}
        asr_response = requests.post("http://127.0.0.1:5001/api/v1/asr/jobs", json=asr_payload)
        asr_response.raise_for_status()
        asr_job_id = asr_response.json()["jobId"]
        asr_result = poll_for_result("ASR", asr_job_id, f"http://127.0.0.1:5001/api/v1/asr/jobs/{asr_job_id}")
        transcribed_text = asr_result["text"]

        # Step 2: Call MT to translate the transcribed Malayalam text to English
        print("ORCHESTRATOR (S2S-PIPE): Calling v1 MT service.")
        mt_payload = {"text": transcribed_text, "language1": "MALAYALAM", "language2": "ENGLISH"}
        mt_response = requests.post("http://127.0.0.1:5004/api/v1/translate/jobs", json=mt_payload)
        mt_response.raise_for_status()
        mt_job_id = mt_response.json()["jobId"]
        mt_result = poll_for_result("MT", mt_job_id, f"http://127.0.0.1:5004/api/v1/translate/jobs/{mt_job_id}")
        translated_english_text = mt_result["translatedText"]

        # Step 3: Call TTS to get English speech from the translated English text
        print("ORCHESTRATOR (S2S-PIPE): Calling v1 TTS service for English.")
        tts_payload = {"text_to_speak": translated_english_text, "gender": gender, "language": "ENGLISH"}
        tts_response = requests.post("http://127.0.0.1:5002/api/v1/tts/jobs", json=tts_payload)
        tts_response.raise_for_status()
        tts_job_id = tts_response.json()["jobId"]
        tts_result = poll_for_result("TTS", tts_job_id, f"http://127.0.0.1:5002/api/v1/tts/jobs/{tts_job_id}")
        english_audio_url = tts_result["audio_url"]
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = {
            "source_malayalam_text": transcribed_text,
            "translated_english_text": translated_english_text,
            "english_audio_url": english_audio_url
        }
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}

# --- API Endpoints ---

# Endpoints for Framework 1 (No changes)
@app.post("/api/v2/document-translation", response_model=Job, status_code=202, tags=["Framework 1: Document Translation"])
async def start_doc_trans_job(request: DocumentTranslationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_document_translation_pipeline, job_id, request.image_file_path)
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/document-translation/jobs/{job_id}", response_model=Job, tags=["Framework 1: Document Translation"])
async def get_doc_trans_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# Endpoints for Framework 2 (No changes)
@app.post("/api/v2/speech-translation", response_model=Job, status_code=202, tags=["Framework 2: Speech Translation"])
async def start_speech_trans_job(request: SpeechTranslationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_speech_translation_pipeline, job_id, request.audio_file_path)
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/speech-translation/jobs/{job_id}", response_model=Job, tags=["Framework 2: Speech Translation"])
async def get_speech_trans_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# Endpoints for Framework 3 (No changes)
@app.post("/api/v2/text-to-speech", response_model=Job, status_code=202, tags=["Framework 3: Text to Speech"])
async def start_tts_synth_job(request: TextToSpeechRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_text_to_speech_pipeline, job_id, request.text, request.gender)
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/text-to-speech/jobs/{job_id}", response_model=Job, tags=["Framework 3: Text to Speech"])
async def get_tts_synth_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# NEW: Endpoints for Framework 4
@app.post("/api/v2/speech-to-speech", response_model=Job, status_code=202, tags=["Framework 4: Speech-to-Speech Translation"])
async def start_s2s_trans_job(request: SpeechToSpeechRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_speech_to_speech_pipeline, job_id, request.audio_file_path, request.gender)
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/speech-to-speech/jobs/{job_id}", response_model=Job, tags=["Framework 4: Speech-to-Speech Translation"])
async def get_s2s_trans_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

