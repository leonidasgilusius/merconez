import os
import requests

def process_tts_task(text: str, gender: str, language:str, job_id: str):
    tts_api_url = os.getenv(f"TTS_{language}_API_URL")
    tts_access_token = os.getenv("BHASHINI_API_KEY")

    if not tts_api_url or not tts_access_token:
        raise Exception("Server configuration error: Missing TTS API credentials")

    print(f"BACKGROUND TASK: Started TTS processing for job: {job_id}")

    headers = {"access-token": tts_access_token}
    
    payload = {
        "text": text,
        "gender": gender
    }

    response = requests.post(tts_api_url, headers=headers, json=payload, verify=False)
    response.raise_for_status()

    api_response_data = response.json()
    
    if api_response_data.get("status") == "success":
        print(f"BACKGROUND TASK: Finished TTS processing for job: {job_id}")
        # The response key is "s3_url" inside the "data" object [cite: 88, 87]
        return api_response_data["data"]["s3_url"]
    else:
        error_message = api_response_data.get("message", "Unknown TTS API error")
        raise Exception(f'TTS error: {error_message}')

    
