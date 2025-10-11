Bhashini Megathon Challenge: Universal Pipeline Backend1. Project OverviewThis project was created for the Bhashini Megathon Challenge. The primary goal was to build a "universal pipeline" of reusable backend features by leveraging the Bhashini APIs. The entire backend is built with Python and FastAPI, following a modular, multi-service architecture designed to be run locally using honcho and a Procfile.The core concept is to create a system where individual AI services (like ASR, TTS, OCR, MT) can be chained together in flexible ways to create powerful, high-level user features, which we call "Frameworks."2. ArchitectureThe backend is designed with a clean, two-layer architecture to separate concerns and promote reusability.V1 Core Services Layer: This layer consists of simple, standalone FastAPI services that act as direct wrappers around the live Bhashini APIs. Each service is responsible for only one task (e.g., tts_service only handles text-to-speech).V2 Orchestration Layer: This is a high-level service that does not interact with the Bhashini APIs directly. Instead, it combines and orchestrates the V1 services to create end-to-end user features or "pipelines." For example, it can take audio, send it to the V1 ASR service, and then send the resulting text to the V1 MT service.This separation allows for easy maintenance, testing, and scalability of individual components.3. Project StructureThe final project is organized into the following structure within the bhashini_backend root directory:/bhashini_backend
├── backend/
│   ├── asr_service/
│   │   └── main.py
│   ├── mt_service/
│   │   └── main.py
│   ├── ocr_service/
│   │   └── main.py
│   ├── tts_service/
│   │   └── main.py
│   └── v2_services/
│       └── main.py
├── .env
├── index.html
└── Procfile
4. The V1 Core Services LayerThe V1 services are the foundational building blocks of the entire application.4.1. Evolution to an Asynchronous ModelInitially, the V1 services were simple synchronous wrappers. However, to handle potentially long-running AI tasks without blocking the server, a major refactoring effort was undertaken. All V1 services were standardized to follow a robust, asynchronous, job-based polling pattern.This pattern works as follows for every V1 service:A POST request is sent to a /api/v1/{service}/jobs endpoint with the required payload (e.g., text, file path).The service immediately accepts the request, creates a unique jobId, starts the task in the background, and returns the jobId with a 202 Accepted status.The client (in our case, the V2 orchestrator) then repeatedly calls a GET /api/v1/{service}/jobs/{jobId} endpoint to poll for the job's status.The job status will be processing, completed, or failed. Once completed, the response includes the final result.4.2. Dynamic Language SupportAll V1 services support multiple languages dynamically. They construct the necessary environment variable keys at runtime. For example, a request to the MT service with language1: "ENGLISH" and language2: "MALAYALAM" will cause the service to look for MT_ENGLISH_MALAYALAM_API_URL and MT_ENGLISH_MALAYALAM_ACCESS_TOKEN in the .env file.4.3. Service BreakdownASR Service (asr_service):Purpose: Handles Automatic Speech Recognition.Input: Path to an audio file (.wav) and a source language.Output: Transcribed text.TTS Service (tts_service):Purpose: Handles Text-to-Speech synthesis.Input: Text, gender, and a target language.Output: A URL to the generated audio file.OCR Service (ocr_service):Purpose: Handles Optical Character Recognition.Input: Path to an image file and a source language.Output: Extracted text from the image.MT Service (mt_service):Purpose: Handles Machine Translation.Input: Text, a source language, and a target language.Output: Translated text.5. The V2 Orchestration LayerThe v2_services module is the "brain" of the operation. It defines the user-facing pipelines by chaining calls to the V1 services. We have implemented four distinct frameworks.Framework 1: Document TranslationFlow: Malayalam Image → OCR Service → MT Service → English TextEndpoint: POST /api/v2/document-translationInput: { "image_file_path": "path/to/image.png" }Output: Extracted Malayalam text and the translated English text.Framework 2: Speech TranslationFlow: Malayalam Speech → ASR Service → MT Service → English TextEndpoint: POST /api/v2/speech-translationInput: { "audio_file_path": "path/to/audio.wav" }Output: Transcribed Malayalam text and the translated English text.Framework 3: Text-to-Speech SynthesisFlow: English Text → MT Service → TTS Service → Malayalam SpeechEndpoint: POST /api/v2/text-to-speechInput: { "text": "Hello world", "gender": "female" }Output: URL to the generated Malayalam audio file.Framework 4: Speech-to-Speech TranslationFlow: Malayalam Speech → ASR Service → MT Service → TTS Service → English SpeechEndpoint: POST /api/v2/speech-to-speechInput: { "audio_file_path": "path/to/audio.wav", "gender": "female" }Output: URL to the generated English audio file.6. Setup and Running the ProjectPrerequisitesPython 3.9+piphonchoInstallationClone the repository.Navigate to the root bhashini_backend directory.Create and activate a virtual environment:python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install the required packages from requirements.txt.pip install -r requirements.txt
ConfigurationIn the root bhashini_backend directory, create a file named .env.Copy the contents of .env.example into it and fill in the values with your actual Bhashini API URLs and Access Tokens..env.example:# Machine Translation (MT)
MT_ENGLISH_MALAYALAM_API_URL="..."
MT_ENGLISH_MALAYALAM_ACCESS_TOKEN="..."
MT_MALAYALAM_ENGLISH_API_URL="..."
MT_MALAYALAM_ENGLISH_ACCESS_TOKEN="..."

# Text-to-Speech (TTS)
TTS_MALAYALAM_API_URL="..."
TTS_MALAYALAM_ACCESS_TOKEN="..."
TTS_ENGLISH_API_URL="..."
TTS_ENGLISH_ACCESS_TOKEN="..."

# Automatic Speech Recognition (ASR)
ASR_MALAYALAM_API_URL="..."
ASR_MALAYALAM_ACCESS_TOKEN="..."

# Optical Character Recognition (OCR)
OCR_MALAYALAM_API_URL="..."
OCR_MALAYALAM_ACCESS_TOKEN="..."
Running the ServicesMake sure you are in the root bhashini_backend directory.Run honcho to start all services defined in the Procfile.honcho start
All five services (4 for V1, 1 for V2) will start up and run concurrently.7. How to UseOption 1: Interactive API Docs (Swagger UI)The easiest way for developers to test the pipelines is through the auto-generated API documentation.Open your browser and navigate to: http://127.0.0.1:5006/docsYou will see all four frameworks listed. You can expand each one, click "Try it out," fill in the parameters, and execute the requests directly from the browser.Option 2: Web InterfaceA simple user interface is provided in index.html.Make sure all backend services are running via honcho start.Open the index.html file in your web browser.The page provides a simple form for each of the four frameworks. Fill in the required inputs and click "Run Pipeline" to see the results.