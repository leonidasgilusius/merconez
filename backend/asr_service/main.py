import os
import requests

def process_asr_task(audio_file_path: str, language: str, job_id: str):
    language = language.upper()

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"File not found at path: {audio_file_path}")
    
    asr_api_url = os.getenv(f"ASR_{language}_API_URL")
    asr_access_token = os.getenv("BHASHINI_API_KEY")

    if not asr_api_url or not asr_access_token:
        raise Exception("Server configuration error: Missing ASR API credentials")

    headers = {"access-token": asr_access_token}
    file_path = audio_file_path

    # The API expects the audio file as form-data
    with open(file_path, "rb") as audio_file:
        files = {
            "audio_file": (os.path.basename(file_path), audio_file, "audio/wav")
        }
        print(f"BACKGROUND TASK: Started ASR processing for job: {job_id}")
        response = requests.post(asr_api_url, headers=headers, files=files, verify=False)
        response.raise_for_status()

    api_response_data = response.json()
    
    if api_response_data.get("status") == "success":
        # The response key is "recognized_text" according to the docs
        print(f"BACKGROUND TASK: Finished ASR processing for job: {job_id}")
        return api_response_data.get("data", {}).get("recognized_text")
    else:
        error_message = api_response_data.get("message", "Unknown ASR API error")
        raise Exception(f'ASR error: {error_message}')
    
    