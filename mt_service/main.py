from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ... (Pydantic models are the same) ...
class TranslationRequest(BaseModel):
    text: str
    language1: str
    language2: str

class TranslationResponse(BaseModel):
    translatedText: str

@app.post("/api/v1/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    language1 = request.language1.upper()
    language2 = request.language2.upper()
    
    mt_api_url = os.getenv(f"MT_{language1}_{language2}_API_URL")
    mt_access_token = os.getenv(f"MT_{language1}_{language2}_ACCESS_TOKEN")
    
    if not mt_api_url or not mt_access_token:
        raise HTTPException(status_code=500, detail="Server configuration error: Missing API URL or Token")

    print(f"--- Calling Live Bhashini MT API: {mt_api_url} ---")
    
    headers = {"access-token": mt_access_token}
    payload = {"input_text": request.text}

    try:
        # THE ONLY CHANGE IS ADDING `verify=False` TO THIS LINE
        response = requests.post(mt_api_url, headers=headers, json=payload, verify=False)

        response.raise_for_status()
        api_response_data = response.json()
        
        if api_response_data.get("status") == "success":
            final_translation = api_response_data["data"]["output_text"]
        else:
            error_message = api_response_data.get("message", "Unknown error from Bhashini API")
            print(f"ERROR: Bhashini API returned a non-success status: {error_message}")
            raise HTTPException(status_code=500, detail=f"Bhashini API Error: {error_message}")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: An error occurred calling the Bhashini API: {e}")
        raise HTTPException(status_code=502, detail=f"Error communicating with Bhashini API: {e}")
    except KeyError:
        print("ERROR: Could not parse the Bhashini API response. 'data' or 'output_text' key might be missing.")
        raise HTTPException(status_code=500, detail="Invalid response format from Bhashini API")

    print("--- Successfully received and parsed response from Bhashini API ---")

    return TranslationResponse(translatedText=final_translation)