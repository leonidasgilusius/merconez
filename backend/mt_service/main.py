import os
import requests

def process_translation_task(text: str, language1: str, language2: str, job_id: str):
    lang1_upper = language1.upper()
    lang2_upper = language2.upper()

    print(f"BACKGROUND TASK: Started translation for job: {job_id}")

    mt_api_url = os.getenv(f"MT_{lang1_upper}_{lang2_upper}_API_URL")
    mt_access_token = os.getenv("BHASHINI_API_KEY")

    # Handle configuration errors
    if not mt_api_url or not mt_access_token:
        raise Exception("Server configuration error: Missing MT API credentials")

    headers = {"access-token": mt_access_token}
    payload = {"input_text": text}

    # Call the external Bhashini MT API
    response = requests.post(mt_api_url, headers=headers, json=payload, verify=False)
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    
    api_response_data = response.json()

    # Check the status within the API response body
    if api_response_data.get("status") == "success":
        print(f"BACKGROUND TASK: Finished MT processing for job: {job_id}")
        return api_response_data["data"]["output_text"]
    else:
        error_message = api_response_data.get("message", "Unknown Bhashini API error")
        raise Exception(f'MT error: {error_message}')
    