from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configure the Gemini API client
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    model = None

class SummarizeRequest(BaseModel):
    text: str

class SummarizeResponse(BaseModel):
    summary: str

@app.post("/api/v2/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Gemini API not configured correctly.")

    print("--- Calling Gemini API for summarization ---")

    try:
        # Create a prompt for the LLM
        prompt = f"Please provide a concise summary of the following text:\n\n{request.text}"

        # Call the API
        response = model.generate_content(prompt)

        summary = response.text

    except Exception as e:
        print(f"ERROR: An error occurred calling the Gemini API: {e}")
        raise HTTPException(status_code=503, detail=f"Error communicating with Gemini API: {e}")

    print("--- Successfully received summary from Gemini API ---")

    return SummarizeResponse(summary=summary)