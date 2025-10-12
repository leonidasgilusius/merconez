# backend/v2_services/conversation_service.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import requests
import time
import uuid
import os

# Import the shared jobs dict from main
from .main import jobs

router = APIRouter(tags=["Framework 5: Conversation Translator"])

# ---------------------
# MODELS (EXISTING)
# ---------------------

class ConversationTurn(BaseModel):
    """Single turn in a conversation (audio-based)."""
    speaker: str
    audio_file_path: str
    input_language: str
    output_language: str
    gender: str = "female"

class ConversationJob(BaseModel):
    jobId: str
    status: str
    result: list | None = None

# ---------------------
# NEW MODEL FOR LIVE TURN RESPONSE
# ---------------------

class LiveTranslationResult(BaseModel):
    speaker: str
    input_text: str
    translated_text: str
    output_audio_url: str

# ---------------------
# POLLING HELPER (reuse)
# ---------------------

def poll_for_result(service_name: str, job_id: str, url: str) -> dict:
    while True:
        print(f"CONV-PIPE: Polling {service_name} job: {job_id}")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data["status"] == "completed":
            return data["result"]
        elif data["status"] == "failed":
            err = data.get('result', {}).get('error', 'Unknown error')
            raise Exception(f"{service_name} failed: {err}")
        time.sleep(2)

# ---------------------
# PIPELINE LOGIC (EXISTING BATCH)
# ---------------------

def run_conversation_pipeline(job_id: str, turns: list[ConversationTurn]):
    # ... (Your existing run_conversation_pipeline function remains here for batch processing)
    results = []
    try:
        for i, turn in enumerate(turns):
            print(f"CONV-PIPE: Processing turn {i+1}/{len(turns)} from {turn.speaker}")

            # 1️⃣ ASR
            asr_payload = {"audio_file_path": turn.audio_file_path, "language": turn.input_language}
            asr_r = requests.post("http://127.0.0.1:5001/api/v1/asr/jobs", json=asr_payload)
            asr_r.raise_for_status()
            asr_job = asr_r.json()["jobId"]
            asr_res = poll_for_result("ASR", asr_job, f"http://127.0.0.1:5001/api/v1/asr/jobs/{asr_job}")
            text = asr_res["text"]

            # 2️⃣ MT
            mt_payload = {"text": text, "language1": turn.input_language, "language2": turn.output_language}
            mt_r = requests.post("http://127.0.0.1:5004/api/v1/translate/jobs", json=mt_payload)
            mt_r.raise_for_status()
            mt_job = mt_r.json()["jobId"]
            mt_res = poll_for_result("MT", mt_job, f"http://127.0.0.1:5004/api/v1/translate/jobs/{mt_job}")
            translated_text = mt_res["translatedText"]

            # 3️⃣ TTS
            tts_payload = {"text_to_speak": translated_text, "gender": turn.gender, "language": turn.output_language}
            tts_r = requests.post("http://127.0.0.1:5002/api/v1/tts/jobs", json=tts_payload)
            tts_r.raise_for_status()
            tts_job = tts_r.json()["jobId"]
            tts_res = poll_for_result("TTS", tts_job, f"http://127.0.0.1:5002/api/v1/tts/jobs/{tts_job}")
            audio_url = tts_res["audio_url"]

            results.append({
                "speaker": turn.speaker,
                "input_text": text,
                "translated_text": translated_text,
                "output_audio_url": audio_url
            })

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = results

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}


# ---------------------
# NEW LIVE PIPELINE LOGIC
# ---------------------

# NOTE: Ensure 'import os' is added to the top of conversation_service.py for this to work.

def process_single_live_turn(turn: ConversationTurn) -> dict:
    """
    Runs the ASR -> MT -> TTS pipeline for a single turn synchronously,
    and ensures the temporary audio file is deleted afterward.
    """
    file_path = turn.audio_file_path # Get the path from the request model
    
    try:
        print(f"LIVE-PIPE: Processing turn from {turn.speaker}")

        # 1️⃣ ASR
        asr_payload = {"audio_file_path": file_path, "language": turn.input_language}
        asr_r = requests.post("http://127.0.0.1:5001/api/v1/asr/jobs", json=asr_payload)
        asr_r.raise_for_status()
        asr_job = asr_r.json()["jobId"]
        asr_res = poll_for_result("ASR", asr_job, f"http://127.0.0.1:5001/api/v1/asr/jobs/{asr_job}")
        input_text = asr_res["text"]

        # 2️⃣ MT
        mt_payload = {"text": input_text, "language1": turn.input_language, "language2": turn.output_language}
        mt_r = requests.post("http://127.0.0.1:5004/api/v1/translate/jobs", json=mt_payload)
        mt_r.raise_for_status()
        mt_job = mt_r.json()["jobId"]
        mt_res = poll_for_result("MT", mt_job, f"http://127.0.0.1:5004/api/v1/translate/jobs/{mt_job}")
        translated_text = mt_res["translatedText"]

        # 3️⃣ TTS
        tts_payload = {"text_to_speak": translated_text, "gender": turn.gender, "language": turn.output_language}
        tts_r = requests.post("http://127.0.0.1:5002/api/v1/tts/jobs", json=tts_payload)
        tts_r.raise_for_status()
        tts_job = tts_r.json()["jobId"]
        tts_res = poll_for_result("TTS", tts_job, f"http://127.0.0.1:5002/api/v1/tts/jobs/{tts_job}")
        output_audio_url = tts_res["audio_url"]

        return {
            "speaker": turn.speaker,
            "input_text": input_text,
            "translated_text": translated_text,
            "output_audio_url": output_audio_url
        }

    except Exception as e:
        # Re-raise the exception after cleanup (or if cleanup fails)
        raise e 
        
    finally: # <--- CRITICAL CLEANUP BLOCK ADDED HERE
        # Delete the temporary audio file regardless of success or failure
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"LIVE-PIPE: Cleaned up temporary audio file: {file_path}")
        except Exception as cleanup_err:
            print(f"LIVE-PIPE: Warning: Failed to delete {file_path}: {cleanup_err}")


# ---------------------
# API ROUTES (EXISTING BATCH)
# ---------------------

@router.post("/api/v2/conversation", response_model=ConversationJob, status_code=202)
async def start_conversation_job(turns: list[ConversationTurn], background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(run_conversation_pipeline, job_id, turns)
    return {"jobId": job_id, "status": "processing"}

@router.get("/api/v2/conversation/jobs/{job_id}", response_model=ConversationJob)
async def get_conversation_status(job_id: str):
    if not (job := jobs.get(job_id)):
        raise HTTPException(status_code=404, detail="Job not found")
    return {"jobId": job_id, **job}

# ---------------------
# NEW LIVE API ROUTE
# ---------------------

@router.post("/api/v2/live-turn", response_model=LiveTranslationResult, status_code=200)
async def process_live_translation_turn(turn: ConversationTurn):
    """
    Processes a single audio turn immediately and synchronously for a live interpreter experience.
    """
    try:
        result = process_single_live_turn(turn)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live turn processing failed: {e}")