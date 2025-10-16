# Universal Translator

## Overview
This project is a **multilingual, multimodal translation platform** built for **Megathon 2025**.  
It supports translation across multiple languages and input/output modes, allowing users to process text, audio, and images seamlessly.

---

## How to Run the Application

### Hosted Deployment
You can access the live application at:  
**[Hosted Website Link](https://kannappi.netlify.app/)**

### Usage
1. Open the website.
2. Choose the **input type**: `Text`, `Image`, or `Audio`.
3. Choose the **languages**:
   - From: `English`, `Hindi`, `Kannada`, `Malayalam`, `Marathi`
   - To: `English`, `Hindi`, `Kannada`, `Malayalam`, `Marathi`
   - (You can swap source and target languages as needed.)
4. Enter or upload your input (text, image, or audio file).
5. Choose the **output type**: `Text` or `Audio`.
6. Click **"Process Content"** to run the translation pipeline.

---

## Processing Pipelines

| Input Type | Output Type | Pipeline Used |
|-------------|--------------|----------------|
| Text        | Text         | **MT (Machine Translation)** |
| Text        | Audio        | **MT → TTS (Text-to-Speech)** |
| Image       | Text         | **OCR (Optical Character Recognition) → MT** |
| Image       | Audio        | **OCR → MT → TTS** |
| Audio       | Text         | **ASR (Automatic Speech Recognition) → MT** |
| Audio       | Audio        | **ASR → MT → TTS** |

---

## Technical Details

### Backend
- **Framework:** FastAPI  
- **Server:** Uvicorn  
- **Process Manager:** Honcho  
- **Tunneling:** Ngrok  
- Each core service (ASR, MT, OCR, TTS) runs as a **microservice** on separate ports.
- To run the backend, cd to backend/ and run `honcho start` on your terminal.

### Frontend
- **Framework:** Vanilla JavaScript (no libraries, no React)
- **Design:** Simple and clean interface optimized for mobile devices
- **Hosting:** Netlify  
- **Functionality:** The frontend communicates with backend services to perform ASR, MT, OCR, and TTS operations, depending on user input.

---

## Features Implemented
- Multilingual support across English, Hindi, Kannada, Malayalam, and Marathi
- Multi-modal input handling (Text, Image, Audio)
- Output in both text and speech formats
- Modular backend architecture using FastAPI microservices
- Responsive, mobile-friendly frontend
- Fully hosted and accessible online

---

## Future Work
- Real-time speech-to-speech translation using WebSockets
- Improved UI/UX for accessibility and multilingual text rendering
- Integration of caching and history features for past translations
