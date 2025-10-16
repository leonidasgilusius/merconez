import os
import requests

def process_ocr_task(file_path: str, language: str, job_id: str):
    language = language.upper()

    ocr_api_url = os.getenv(f"OCR_{language}_API_URL")
    ocr_access_token = os.getenv("BHASHINI_API_KEY")

    if not ocr_api_url or not ocr_access_token:
        raise Exception("Server configuration error: Missing OCR API credentials")
    
    print(f"BACKGROUND TASK: Started OCR processing for job: {job_id}")

    headers = {"access-token": ocr_access_token}

    with open(file_path, "rb") as image_file:
        files = {
            "file": (os.path.basename(file_path), image_file, "image/jpeg")
        }
        response = requests.post(ocr_api_url, headers=headers, files=files, verify=False)
        response.raise_for_status()

    api_response_data = response.json()
    
    if api_response_data.get("status") == "success":
        print(f"BACKGROUND TASK: Finished OCR processing for job: {job_id}")
        return api_response_data["data"]["decoded_text"]
    else:
        error_message = api_response_data.get("message", "Unknown OCR API error")
        raise Exception(f'OCR error: {error_message}')