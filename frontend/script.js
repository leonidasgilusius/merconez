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

    // --- DOM ELEMENT REFERENCES ---
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

    // --- NEW HELPER FUNCTION FOR FILE UPLOAD ---

const uploadFileAndGetPath = async (fileType, fileElement) => {
    const file = fileElement.files[0];
    const uploadEndpoint = fileType === 'Image' ? '/api/v2/file-upload/image' : '/api/v2/file-upload/audio';

    const formData = new FormData();
    formData.append('file', file);
    
    // The comments regarding language passing can now be removed/simplified.

    const response = await fetch(BASE_URL + uploadEndpoint, {
        method: 'POST',
        body: formData,
        headers: {
            'ngrok-skip-browser-warning': 'true'
        }
    });

    if (!response.ok) {
        throw new Error(`File upload failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.file_path;
};

    const updateOutputView = () => {
        textOutputContainer.classList.add('hidden');
        audioOutputContainer.classList.add('hidden');
        switch(state.outputType) {
            case 'Text': textOutputContainer.classList.remove('hidden'); break;
            case 'Audio': audioOutputContainer.classList.remove('hidden'); break;
        }
    };
    
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
    
    // Close dropdowns when clicking outside
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

    // --- API & PROCESSING LOGIC ---

    const pollJobStatus = (jobUrl) => {
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(jobUrl, {
                    // Always include the ngrok header in case the server needs it
                    headers: { 'ngrok-skip-browser-warning': 'true' } 
                });

                if (!response.ok) {
                    // Safely attempt to read any error detail
                    const errorDetails = await response.text().catch(() => response.statusText);
                    throw new Error(`HTTP error! Status: ${response.status}. Details: ${errorDetails}`);
                }

                // --- CRITICAL FIX START ---
                // Safely read the response text first
                const text = await response.text();
                if (!text) {
                    // The server returned 200 OK but an empty body. Wait and try again.
                    console.log('Polling received empty response, waiting...');
                    return; 
                }

                // Attempt to parse the valid JSON text
                const data = JSON.parse(text);
                // --- CRITICAL FIX END ---
                
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
        }, 2000); // Poll every 2 seconds
    });
};
    // --- API & PROCESSING LOGIC (MODIFIED) ---
// ... (keep pollJobStatus function above this) ...

processBtn.addEventListener('click', async () => {
    if (state.processing) return;
    
    // 1. Validation (KEEP YOUR EXISTING VALIDATION LOGIC)
    let validationError = '';
    // ... (Your existing validation code for Text, Image, Audio) ...
    
    // Skip if validation fails
    errorMessage.textContent = validationError;
    if (validationError) return;

    // 2. Set UI to processing state (KEEP EXISTING UI UPDATE)
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
    let isJsonRequest = false;
    let filePath = null; // To hold the uploaded path
    let isLiveTurn = false; // Flag for synchronous turn

    const { inputType, outputType, inputLang, outputLang } = state;

    try {
        // --- STEP 3A: HANDLE FILE UPLOADS FIRST (if necessary) ---
        if (inputType === 'Image') {
            filePath = await uploadFileAndGetPath('Image', imageUpload); 
        } else if (inputType === 'Audio') {
            // Live Interpreter check: If Audio -> Audio (F4 S2S), we use the batch polling job
            // For live-like turn, we'll assume a separate UI element/mode, but for now, we'll
            // check for the S2S mode. If you intend a true live-turn, you'd add a separate button.
            
            // For batch/pipeline translation (F2 & F4), we upload the file first.
            filePath = await uploadFileAndGetPath('Audio', audioUpload);
        }
        
        // --- STEP 3B: DETERMINE FINAL API CALL ---
        if (inputType === 'Image' && outputType === 'Text') {
            // F1: Document Translation (Uses uploaded file path)
            endpoint = '/api/v2/document-translation';
            jobUrlBase = `${endpoint}/jobs/`;
            isJsonRequest = true;
            requestBody = JSON.stringify({
                image_file_path: filePath,
                input_language: inputLang.toUpperCase(),
                output_language: outputLang.toUpperCase()
            });
        } else if (inputType === 'Audio' && outputType === 'Text') {
            // F2: Speech Translation (Uses uploaded file path)
            endpoint = '/api/v2/speech-translation';
            jobUrlBase = `${endpoint}/jobs/`;
            isJsonRequest = true;
            requestBody = JSON.stringify({
                audio_file_path: filePath,
                input_language: inputLang.toUpperCase(),
                output_language: outputLang.toUpperCase()
            });
        } else if (inputType === 'Text' && outputType === 'Audio') {
            // F3: Text-to-Speech (Text-only, no upload needed)
            endpoint = '/api/v2/text-to-speech';
            jobUrlBase = `${endpoint}/jobs/`;
            isJsonRequest = true;
            requestBody = JSON.stringify({
                text: inputText.value,
                gender: "female",
                input_language: inputLang.toUpperCase(),
                output_language: outputLang.toUpperCase()
            });
        } else if (inputType === 'Audio' && outputType === 'Audio') {
            // F4: Speech-to-Speech (Uses uploaded file path)
            
            // **PSEUDO-LIVE IMPLEMENTATION**
            // For the pseudo-live feel, we will assume "Audio to Audio" is the *single-turn* live mode.
            // This bypasses the long job polling.
            
            endpoint = '/api/v2/live-turn'; // <--- NEW SYNCHRONOUS ENDPOINT
            isLiveTurn = true;
            isJsonRequest = true;
            requestBody = JSON.stringify({
                speaker: "User A", // Assuming User A for simplicity in FE
                audio_file_path: filePath,
                gender: 'female',
                input_language: inputLang.toUpperCase(),
                output_language: outputLang.toUpperCase()
            });
            
            // Note: If you wanted the *batch* S2S (F4), you'd use:
            /*
            // endpoint = '/api/v2/speech-to-speech';
            // jobUrlBase = `${endpoint}/jobs/`;
            // isJsonRequest = true;
            // requestBody = JSON.stringify({ audio_file_path: filePath, ... })
            */

        } else {
            // ... (Error handling for unsupported types) ...
            throw new Error(`Processing from ${inputType} to ${outputType} is not supported.`);
        }

        // 4. Make API call
        const postOptions = {
            method: 'POST',
            body: isJsonRequest ? requestBody : requestBody, // FormData is sent without Content-Type header
            headers: {
                'ngrok-skip-browser-warning': 'true',
                ...(isJsonRequest && {'Content-Type': 'application/json'})
            }
        };

        const initialResponse = await fetch(BASE_URL + endpoint, postOptions);
        if (!initialResponse.ok) {
            const errorBody = await initialResponse.json().catch(() => ({}));
            throw new Error(`Request failed: ${initialResponse.statusText} - ${JSON.stringify(errorBody)}`);
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
            outputText.value = isLiveTurn ? result.translated_text : result; // Live turn returns object, others return string
        } else if (outputType === 'Audio') {
            // Both live-turn and F3 (TTS) return a URL/object containing a URL
            const audioUrl = isLiveTurn ? result.output_audio_url : result;
            
            audioDownloadLink.href = audioUrl;
            audioResultPlaceholder.classList.add('hidden');
            audioDownloadLink.classList.remove('hidden');
            
            // OPTIONAL: Auto-play the audio result
            // const audio = new Audio(audioUrl);
            // audio.play().catch(e => console.error("Auto-play failed:", e));
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

