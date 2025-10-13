document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURATION ---
    const BASE_URL = 'https://tressie-phosphorescent-greyly.ngrok-free.dev';

    // --- STATE MANAGEMENT ---
    let state = {
        inputType: 'Text',
        outputType: 'Text',
        inputLang: 'English',
        outputLang: 'Malayalam',
        processing: false,
    };

    // --- DOM ELEMENT REFERENCES (Assumed to exist in your HTML) ---
    const inputTypeSelector = document.getElementById('inputTypeSelector');
    const outputTypeSelector = document.getElementById('outputTypeSelector');
    const processBtn = document.getElementById('processBtn');
    const processBtnText = document.getElementById('processBtnText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const swapLangBtn = document.getElementById('swapLangBtn');
    
    // Dropdowns
    const inputLangBtn = document.getElementById('inputLangBtn');
    const inputLangValue = document.getElementById('inputLangValue');
    const inputLangChevron = document.getElementById('inputLangChevron');
    const inputLangMenu = document.getElementById('inputLangMenu');
    const outputLangBtn = document.getElementById('outputLangBtn');
    const outputLangValue = document.getElementById('outputLangValue');
    const outputLangChevron = document.getElementById('outputLangChevron');
    const outputLangMenu = document.getElementById('outputLangMenu');

    // Inputs
    const textInputContainer = document.getElementById('textInputContainer');
    const imageInputContainer = document.getElementById('imageInputContainer');
    const audioInputContainer = document.getElementById('audioInputContainer');
    const inputText = document.getElementById('inputText');
    const imageUpload = document.getElementById('imageUpload');
    const imageFileName = document.getElementById('imageFileName');
    const audioUpload = document.getElementById('audioUpload');
    const audioFileName = document.getElementById('audioFileName');
    
    // Outputs
    const textOutputContainer = document.getElementById('textOutputContainer');
    const audioOutputContainer = document.getElementById('audioOutputContainer');
    const outputText = document.getElementById('outputText');
    const audioResultPlaceholder = document.getElementById('audioResultPlaceholder');
    const audioDownloadLink = document.getElementById('audioDownloadLink');

    const errorMessage = document.getElementById('errorMessage');

    // --- HELPER FUNCTIONS ---

    const updateInputView = () => {
        textInputContainer.classList.add('hidden');
        imageInputContainer.classList.add('hidden');
        audioInputContainer.classList.add('hidden');
        switch (state.inputType) {
            case 'Text': textInputContainer.classList.remove('hidden'); break;
            case 'Image': imageInputContainer.classList.remove('hidden'); break;
            case 'Audio': audioInputContainer.classList.remove('hidden'); break;
        }
    };

    const updateOutputView = () => {
        textOutputContainer.classList.add('hidden');
        audioOutputContainer.classList.add('hidden');
        switch(state.outputType) {
            case 'Text': textOutputContainer.classList.remove('hidden'); break;
            case 'Audio': audioOutputContainer.classList.remove('hidden'); break;
        }
    };

    // --- FILE UPLOAD HELPER (STEP 1: Uploads file to server disk) ---
    const uploadFileAndGetPath = async (fileType, fileElement) => {
        const file = fileElement.files[0];
        const uploadEndpoint = fileType === 'Image' ? '/api/v2/file-upload/image' : '/api/v2/file-upload/audio';

        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(BASE_URL + uploadEndpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'ngrok-skip-browser-warning': 'true' 
            }
        });

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({}));
            throw new Error(`File upload failed: ${response.statusText} - ${JSON.stringify(errorBody.detail || errorBody)}`);
        }

        const data = await response.json();
        return data.file_path;
    };

    // --- POLLING LOGIC (For asynchronous jobs F1, F2, F3, F4) ---
    const pollJobStatus = (jobUrl) => {
        return new Promise((resolve, reject) => {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(jobUrl, {
                        headers: {
                            'ngrok-skip-browser-warning': 'true' 
                        }
                    });

                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    
                    // Safely read the response text first to handle empty/invalid JSON
                    const text = await response.text();
                    if (!text) {
                        console.log('Polling received empty response, waiting...');
                        return; 
                    }
                    
                    const data = JSON.parse(text); // Use JSON.parse on the read text

                    if (data.status === 'completed') {
                        clearInterval(interval);
                        resolve(data.result);
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        const errorDetails = typeof data.result === 'object' && data.result !== null ? JSON.stringify(data.result) : data.result;
                        reject(`Job failed: ${errorDetails}`);
                    }
                } catch (error) {
                    clearInterval(interval);
                    reject(error);
                }
            }, 2000); 
        });
    };

    // --- Boilerplate UI Functions (kept for context) ---
    const handleToggleButtonGroup = (selector, stateKey, callback) => {
        selector.addEventListener('click', (e) => {
            const button = e.target.closest('button');
            if (!button) return;
            state[stateKey] = button.dataset.value;
            selector.querySelectorAll('button').forEach(btn => {
                btn.classList.remove('active', 'bg-indigo-600', 'text-white');
                btn.classList.add('bg-slate-700', 'hover:bg-slate-600', 'text-slate-300');
            });
            button.classList.add('active', 'bg-indigo-600', 'text-white');
            button.classList.remove('bg-slate-700', 'hover:bg-slate-600', 'text-slate-300');
            if (callback) callback();
        });
    };
    const setupDropdown = (btn, menu, valueEl, chevron, stateKey) => {
        btn.addEventListener('click', () => {
            const isHidden = menu.classList.contains('hidden');
            if (isHidden) {
                menu.classList.remove('hidden');
                setTimeout(() => { menu.classList.remove('opacity-0', 'scale-95'); chevron.style.transform = 'rotate(180deg)'; }, 10);
            } else {
                menu.classList.add('opacity-0', 'scale-95');
                chevron.style.transform = 'rotate(0deg)';
                setTimeout(() => menu.classList.add('hidden'), 200);
            }
        });
        menu.addEventListener('click', (e) => {
            e.preventDefault();
            if (e.target.tagName === 'A') {
                valueEl.textContent = e.target.dataset.value;
                state[stateKey] = e.target.dataset.value;
                btn.click();
            }
        });
    };
    document.addEventListener('click', (e) => {
        if (!inputLangBtn.contains(e.target) && !inputLangMenu.contains(e.target) && !inputLangMenu.classList.contains('hidden')) inputLangBtn.click();
        if (!outputLangBtn.contains(e.target) && !outputLangMenu.contains(e.target) && !outputLangMenu.classList.contains('hidden')) outputLangBtn.click();
    });
    // --- EVENT LISTENERS ---
    handleToggleButtonGroup(inputTypeSelector, 'inputType', updateInputView);
    handleToggleButtonGroup(outputTypeSelector, 'outputType', updateOutputView);
    setupDropdown(inputLangBtn, inputLangMenu, inputLangValue, inputLangChevron, 'inputLang');
    setupDropdown(outputLangBtn, outputLangMenu, outputLangValue, outputLangChevron, 'outputLang');
    swapLangBtn.addEventListener('click', () => {
        [state.inputLang, state.outputLang] = [state.outputLang, state.inputLang];
        inputLangValue.textContent = state.inputLang;
        outputLangValue.textContent = state.outputLang;
    });
    imageUpload.addEventListener('change', (e) => { imageFileName.textContent = e.target.files.length > 0 ? e.target.files[0].name : 'JPG or PNG, max 5MB'; });
    audioUpload.addEventListener('change', (e) => { audioFileName.textContent = e.target.files.length > 0 ? e.target.files[0].name : 'WAV, max 5MB, ~20 seconds'; });


    // --- MAIN PROCESSING LOGIC (STEP 2: Starts the pipeline) ---
    processBtn.addEventListener('click', async () => {
        if (state.processing) return;
        
        // 1. Validation (omitted for brevity, assume your robust validation code is here)
        let validationError = '';
        const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
        const { inputType, outputType, inputLang, outputLang } = state;

        switch (inputType) {
            case 'Text':
                const wordCount = inputText.value.trim().split(/\s+/).filter(Boolean).length;
                if (wordCount === 0) validationError = 'Please enter some text.';
                else if (wordCount > 50) validationError = 'Text must not exceed 50 words.';
                break;
            case 'Image':
                const imageFile = imageUpload.files[0];
                if (!imageFile) validationError = 'Please select an image file.';
                else if (imageFile.size > MAX_FILE_SIZE) validationError = 'Image file size must be less than 5MB.';
                else if (!['image/jpeg', 'image/png'].includes(imageFile.type)) validationError = 'Only JPG or PNG images are allowed.';
                break;
            case 'Audio':
                const audioFile = audioUpload.files[0];
                if (!audioFile) {
                    validationError = 'Please select an audio file.';
                } else if (audioFile.size > MAX_FILE_SIZE) {
                    validationError = 'Audio file size must be less than 5MB.';
                } else {
                    const ALLOWED_AUDIO_TYPES = ['audio/wav', 'audio/wave', 'audio/x-wav', 'audio/vnd.wave'];
                    const isAllowedMimeType = ALLOWED_AUDIO_TYPES.includes(audioFile.type);
                    const isWavExtension = audioFile.name.toLowerCase().endsWith('.wav');
                    if (!isAllowedMimeType && !isWavExtension) {
                         validationError = 'Only WAV audio files are allowed.';
                    }
                }
                break;
        }

        errorMessage.textContent = validationError;
        if (validationError) return;

        // 2. Set UI to processing state
        state.processing = true;
        processBtn.disabled = true;
        processBtnText.textContent = 'Processing...';
        loadingSpinner.classList.remove('hidden');
        outputText.value = '';
        audioDownloadLink.classList.add('hidden');
        audioResultPlaceholder.classList.remove('hidden');

        // 3. Determine API endpoint and prepare data
        let endpoint = '';
        let requestBody;
        let jobUrlBase = '';
        let filePath = null; 
        let isLiveTurn = false; 

        try {
            // --- STEP 3A: HANDLE FILE UPLOADS FIRST (if necessary) ---
            if (inputType === 'Image') {
                filePath = await uploadFileAndGetPath('Image', imageUpload);
            } else if (inputType === 'Audio') {
                filePath = await uploadFileAndGetPath('Audio', audioUpload);
            }
            
            // --- STEP 3B: DETERMINE FINAL API CALL (JSON Body) ---
            if (inputType === 'Image' && outputType === 'Text') {
                // F1: Document Translation
                endpoint = '/api/v2/document-translation';
                jobUrlBase = `${endpoint}/jobs/`;
                requestBody = JSON.stringify({
                    image_file_path: filePath, // Sent as string via JSON
                    input_language: inputLang.toUpperCase(),
                    output_language: outputLang.toUpperCase()
                });
            } 
            else if (inputType === 'Image' && outputType === 'Audio') {
                // F6: Image to Audio (New Pipeline)
                endpoint = '/api/v2/image-to-audio';
                jobUrlBase = `${endpoint}/jobs/`;
                requestBody = JSON.stringify({
                    image_file_path: filePath, 
                    input_language: inputLang.toUpperCase(),
                    output_language: outputLang.toUpperCase()
                });
            } 
            else if (inputType === 'Audio' && outputType === 'Text') {
                // F2: Speech Translation
                endpoint = '/api/v2/speech-translation';
                jobUrlBase = `${endpoint}/jobs/`;
                requestBody = JSON.stringify({
                    audio_file_path: filePath, // Sent as string via JSON
                    input_language: inputLang.toUpperCase(),
                    output_language: outputLang.toUpperCase()
                });
            } else if (inputType === 'Text' && outputType === 'Audio') {
                // F3: Text-to-Speech (Text-only)
                endpoint = '/api/v2/text-to-speech';
                jobUrlBase = `${endpoint}/jobs/`;
                requestBody = JSON.stringify({
                    text: inputText.value,
                    gender: "female",
                    input_language: inputLang.toUpperCase(),
                    output_language: outputLang.toUpperCase()
                });
            } else if (inputType === 'Audio' && outputType === 'Audio') {
                // F5: Pseudo-Live Translation (Synchronous)
                endpoint = '/api/v2/live-turn'; 
                isLiveTurn = true;
                requestBody = JSON.stringify({
                    speaker: "User A", 
                    audio_file_path: filePath, // Sent as string via JSON
                    gender: 'female',
                    input_language: inputLang.toUpperCase(),
                    output_language: outputLang.toUpperCase()
                });
             } 
            else if (inputType === 'Text' && outputType === 'Text') {
                // F5: Text-to-Text
                endpoint = '/api/v2/text-to-text'; // <-- Correct endpoint
                jobUrlBase = `${endpoint}/jobs/`;
                requestBody = JSON.stringify({
                    text: inputText.value,
                    input_language: inputLang.toUpperCase(),
                    output_language: outputLang.toUpperCase()
                });
            } else if (inputType === 'Text' && outputType === 'Audio') {
                // F3: Text-to-Speech
                endpoint = '/api/v2/text-to-speech'; // <-- Correct endpoint
                // ... (rest of T2S logic) ...
            }
                else {
                throw new Error(`Processing from ${inputType} to ${outputType} is not supported.`);
            }

            // 4. Execute API Call (Always JSON for Step 2)
            const postOptions = {
                method: 'POST',
                body: requestBody, // This MUST be the JSON string
                headers: {
                    'ngrok-skip-browser-warning': 'true',
                    'Content-Type': 'application/json' // CRITICAL: Ensures FastAPI reads JSON
                }
            };

            const initialResponse = await fetch(BASE_URL + endpoint, postOptions);
            if (!initialResponse.ok) {
                const errorBody = await initialResponse.json().catch(() => ({}));
                throw new Error(`Initial request failed: ${initialResponse.statusText} - ${JSON.stringify(errorBody.detail || errorBody)}`);
            }
            
            let result;

            if (isLiveTurn) {
                // Direct synchronous response from /api/v2/live-turn
                result = await initialResponse.json(); 
            } else {
                // Asynchronous Job Polling for F1, F2, F3
                const jobData = await initialResponse.json();
                const { jobId } = jobData;
                processBtnText.textContent = 'Checking status...';
                const jobUrl = BASE_URL + jobUrlBase + jobId;
                result = await pollJobStatus(jobUrl);
            }

            // 5. Display Result
            if (outputType === 'Text') {
                const textResult = isLiveTurn ? result.translated_text : result; 
                outputText.value = textResult; 
            } else if (outputType === 'Audio') {
                const audioUrl = isLiveTurn ? result.output_audio_url : result;
                
                audioDownloadLink.href = audioUrl;
                audioResultPlaceholder.classList.add('hidden');
                audioDownloadLink.classList.remove('hidden');
            }

        } catch (error) {
            console.error('API Error:', error);
            errorMessage.textContent = `An error occurred during processing: ${error.message}`;
        } finally {
            state.processing = false;
            processBtn.disabled = false;
            processBtnText.textContent = 'Process Content';
            loadingSpinner.classList.add('hidden');
        }
    });

    // --- INITIALIZATION ---
    updateInputView();
    updateOutputView();
});