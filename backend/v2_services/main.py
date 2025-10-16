from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
import requests
import os 
import json
from dotenv import load_dotenv

from asr_service.main import process_asr_task
from mt_service.main import process_translation_task
from ocr_service.main import process_ocr_task
from tts_service.main import process_tts_task

load_dotenv()

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
    result: str | None = None

# Models for the request bodies of our frameworks
class RequestBase(BaseModel):
    input_language: str
    output_language: str


class DocumentTranslationRequest(RequestBase):
    image_file_path: str

class SpeechTranslationRequest(RequestBase):
    audio_file_path: str

class TextToSpeechRequest(RequestBase):
    text: str
    gender: str = "female"

# NEW: Request model for the Speech-to-Speech pipeline
class SpeechToSpeechRequest(RequestBase):
    audio_file_path: str
    gender: str = "female"

class TextToTextRequest(RequestBase):
    text: str

class ImageToSpeechRequest(RequestBase):
    image_file_path: str
    gender: str = "female"

# --- Framework 1: Document (Image) Translation Pipeline (No changes) ---

def run_document_translation_pipeline(job_id: str, file_path: str, input_language: str, output_language: str):
    try:
        # Step 1: Call OCR to get Malayalam text from an image
        print("ORCHESTRATOR (DOC-PIPE): Calling v1 OCR service.")
        extracted_text = process_ocr_task(file_path, input_language, job_id)

        # Step 2: Call MT to translate the extracted Malayalam text to English
        print("ORCHESTRATOR (DOC-PIPE): Calling v1 MT service.")
        translated_text = process_translation_task(extracted_text, input_language, output_language, job_id)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = translated_text
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = json.dumps({"error": str(e)})
    finally: # <--- ADD THIS BLOCK
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"ORCHESTRATOR (DOC-PIPE): Cleaned up file: {file_path}")
        except Exception as cleanup_err:
            print(f"ORCHESTRATOR (DOC-PIPE): Warning: Failed to delete {file_path}: {cleanup_err}")

# --- Framework 2: Speech Translation Pipeline (No changes) ---

def run_speech_translation_pipeline(job_id: str, file_path: str, input_language: str, output_language: str):
    try:
        # Step 1: Call ASR to get text from audio
        print("ORCHESTRATOR (SPEECH-PIPE): Calling v1 ASR service.")
        transcribed_text = process_asr_task(file_path, input_language, job_id)

        # Step 2: Call MT to translate the transcribed Malayalam text to English
        print("ORCHESTRATOR (SPEECH-PIPE): Calling v1 MT service.")
        translated_text = process_translation_task(transcribed_text, input_language, output_language, job_id)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = translated_text
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = json.dumps({"error": str(e)}) 
    finally: # <--- ADD THIS BLOCK
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"ORCHESTRATOR (DOC-PIPE): Cleaned up file: {file_path}")
        except Exception as cleanup_err:
            print(f"ORCHESTRATOR (DOC-PIPE): Warning: Failed to delete {file_path}: {cleanup_err}")


# --- Framework 3: Text-to-Speech Synthesis Pipeline (No changes) ---

def run_text_to_speech_pipeline(job_id: str, text: str, gender: str, input_language: str, output_language: str):
    try:
        # Step 1: Call MT to translate English text to Malayalam
        print("ORCHESTRATOR (TTS-PIPE): Calling v1 MT service.")
        translated_text = process_translation_task(text, input_language, output_language, job_id)

        # Step 2: Call TTS to get Malayalam speech from the translated text
        print("ORCHESTRATOR (TTS-PIPE): Calling v1 TTS service.")
        audio_url = process_tts_task(translated_text, gender, output_language, job_id)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = audio_url
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = json.dumps({"error": str(e)}) 

# --- NEW: Framework 4: Speech-to-Speech Translation Pipeline ---

def run_speech_to_speech_pipeline(job_id: str, file_path: str, gender: str, input_language: str, output_language: str):
    try:
        # Step 1: Call ASR to get text from audio
        print("ORCHESTRATOR (S2S-PIPE): Calling v1 ASR service.")
        transcribed_text = process_asr_task(file_path, input_language, job_id)

        # Step 2: Call MT to translate the transcribed text
        print("ORCHESTRATOR (S2S-PIPE): Calling v1 MT service.")
        translated_text = process_translation_task(transcribed_text, input_language, output_language, job_id)

        # Step 3: Call TTS to get English speech from the translated English text
        print(f"ORCHESTRATOR (S2S-PIPE): Calling v1 TTS service for {output_language}.")
        audio_url = process_tts_task(translated_text, gender, output_language, job_id)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = audio_url
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = json.dumps({"error": str(e)})
    finally: # <--- ADD THIS BLOCK
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"ORCHESTRATOR (DOC-PIPE): Cleaned up file: {file_path}")
        except Exception as cleanup_err:
            print(f"ORCHESTRATOR (DOC-PIPE): Warning: Failed to delete {file_path}: {cleanup_err}")



# frame 5 text to text
def run_text_to_text_pipeline(job_id: str, text: str, input_language: str, output_language: str):
    try:
        # Step 1: Call MT to translate (This is the entire pipeline)
        print("ORCHESTRATOR (T2T-PIPE): Calling v1 MT service.")
        translated_text = process_translation_task(text, input_language, output_language, job_id)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = translated_text
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = json.dumps({"error": str(e)}) # <-- FIX: JSON DUMP APPLIED


# In backend/v2_services/main.py

# --- NEW: Framework 6: Image-to-Audio Pipeline (OCR -> MT -> TTS) ---

def run_image_to_audio_pipeline(job_id: str, file_path: str, gender: str, input_language: str, output_language: str):
    try:
        # Step 1: Call OCR to get text from the image
        print("ORCHESTRATOR (I2A-PIPE): Calling v1 OCR service.")
        extracted_text = process_ocr_task(file_path, input_language, job_id)

        # Step 2: Call MT to translate the extracted text
        print("ORCHESTRATOR (I2A-PIPE): Calling v1 MT service.")
        translated_text = process_translation_task(extracted_text, input_language, output_language, job_id)
        
        # Step 3: Call TTS to get audio output
        print(f"ORCHESTRATOR (I2A-PIPE): Calling v1 TTS service for {output_language}.")
        audio_url = process_tts_task(translated_text, gender, output_language, job_id)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = audio_url
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = json.dumps({"error": str(e)}) 
    finally:
        # CRITICAL: File cleanup
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"ORCHESTRATOR (I2A-PIPE): Cleaned up file: {file_path}")
        except Exception as cleanup_err:
            print(f"ORCHESTRATOR (I2A-PIPE): Warning: Failed to delete {file_path}: {cleanup_err}")


# --- API Endpoints ---

# Endpoints for Framework 1
@app.post("/api/v2/document-translation", response_model=Job, status_code=202, tags=["Framework 1: Document Translation"])
async def start_doc_trans_job(request: DocumentTranslationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_document_translation_pipeline, job_id, request.image_file_path, request.input_language.upper(), request.output_language.upper())
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/document-translation/jobs/{job_id}", response_model=Job, tags=["Framework 1: Document Translation"])
async def get_doc_trans_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# Endpoints for Framework 2 
@app.post("/api/v2/speech-translation", response_model=Job, status_code=202, tags=["Framework 2: Speech Translation"])
async def start_speech_trans_job(request: SpeechTranslationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_speech_translation_pipeline, job_id, request.audio_file_path, request.input_language.upper(), request.output_language.upper())
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/speech-translation/jobs/{job_id}", response_model=Job, tags=["Framework 2: Speech Translation"])
async def get_speech_trans_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# Endpoints for Framework 3 
@app.post("/api/v2/text-to-speech", response_model=Job, status_code=202, tags=["Framework 3: Text to Speech"])
async def start_tts_synth_job(request: TextToSpeechRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_text_to_speech_pipeline, job_id, request.text, request.gender, request.input_language.upper(), request.output_language.upper())
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/text-to-speech/jobs/{job_id}", response_model=Job, tags=["Framework 3: Text to Speech"])
async def get_tts_synth_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# Endpoints for Framework 4
@app.post("/api/v2/speech-to-speech", response_model=Job, status_code=202, tags=["Framework 4: Speech-to-Speech Translation"])
async def start_s2s_trans_job(request: SpeechToSpeechRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_speech_to_speech_pipeline, job_id, request.audio_file_path, request.gender, request.input_language.upper(), request.output_language.upper())
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/speech-to-speech/jobs/{job_id}", response_model=Job, tags=["Framework 4: Speech-to-Speech Translation"])
async def get_s2s_trans_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# Endpoints for Framework 5
@app.post("/api/v2/text-to-text", response_model=Job, status_code=202, tags=["Framework 5: Text to Text"])
async def start_t2t_job(request: TextToTextRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}

    background_tasks.add_task(run_text_to_text_pipeline, job_id, request.text, request.input_language.upper(), request.output_language.upper())
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/text-to-text/jobs/{job_id}", response_model=Job, tags=["Framework 5: Text to Text"])
async def get_t2t_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# Endpoints for Framework 6
@app.post("/api/v2/image-to-audio", response_model=Job, status_code=202, tags=["Framework 6: Image to Audio"])
async def start_i2a_job(request: ImageToSpeechRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_image_to_audio_pipeline, job_id, request.image_file_path, request.gender, request.input_language.upper(), request.output_language.upper())
    return {"jobId": job_id, "status": "processing"}

@app.get("/api/v2/image-to-audio/jobs/{job_id}", response_model=Job, tags=["Framework 6: Image to Audio"])
async def get_i2a_status(job_id: str):
    if not (job := jobs.get(job_id)): raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}


from fastapi import UploadFile, File, Form, BackgroundTasks
import shutil
import os
import uuid

# Use a specific UPLOAD_DIR definition to ensure files are located correctly
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/v2/file-upload/audio", tags=["Utility"])
async def upload_audio_file(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")

    try:
        with open(file_path, "wb") as buffer:
            # IMPORTANT: Use file.read() for async FastAPI context
            file_content = await file.read()
            buffer.write(file_content)

        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {e}")


@app.post("/api/v2/file-upload/image", tags=["Utility"])
async def upload_image_file(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")

    try:
        with open(file_path, "wb") as buffer:
            # IMPORTANT: Use file.read() for async FastAPI context
            file_content = await file.read()
            buffer.write(file_content)

        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")


from . import conversation_service
app.include_router(conversation_service.router)

