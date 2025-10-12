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
                        headers: {
                            'ngrok-skip-browser-warning': 'true'
                        }
                    });

                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const data = await response.json();

                    if (data.status === 'completed') {
                        clearInterval(interval);
                        resolve(data.result);
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        reject('Job processing failed.');
                    }
                } catch (error) {
                    clearInterval(interval);
                    reject(error);
                }
            }, 2000);
        });
    };

    processBtn.addEventListener('click', async () => {
        if (state.processing) return;
        
        // 1. Validation
        let validationError = '';
        const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

        switch (state.inputType) {
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
                    // === MODIFIED: More flexible WAV validation ===
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
        let isJsonRequest = false;

        const { inputType, outputType, inputLang, outputLang } = state;

        if (inputType === 'Image' && outputType === 'Text') {
            endpoint = '/api/v2/document-translation';
            jobUrlBase = `${endpoint}/jobs/`;
            requestBody = new FormData();
            requestBody.append('image_file', imageUpload.files[0]);
            requestBody.append('input_language', inputLang.toLowerCase());
            requestBody.append('output_language', outputLang.toLowerCase());
        } else if (inputType === 'Audio' && outputType === 'Text') { 
            endpoint = '/api/v2/speech-translation';
            jobUrlBase = `${endpoint}/jobs/`;
            requestBody = new FormData();
            requestBody.append('audio_file', audioUpload.files[0]);
            requestBody.append('input_language', inputLang.toLowerCase());
            requestBody.append('output_language', outputLang.toLowerCase());
        } else if (inputType === 'Text' && outputType === 'Audio') {
            endpoint = '/api/v2/text-to-speech';
            jobUrlBase = `${endpoint}/jobs/`;
            isJsonRequest = true;
            requestBody = JSON.stringify({
                text: inputText.value,
                gender: "female",
                input_language: inputLang.toLowerCase(),
                output_language: outputLang.toLowerCase()
            });
        } else if (inputType === 'Audio' && outputType === 'Audio') {
            endpoint = '/api/v2/speech-to-speech';
            jobUrlBase = `${endpoint}/jobs/`;
            requestBody = new FormData();
            requestBody.append('audio_file', audioUpload.files[0]);
            requestBody.append('gender', 'female');
            requestBody.append('input_language', inputLang.toLowerCase());
            requestBody.append('output_language', outputLang.toLowerCase());
        } else {
            errorMessage.textContent = `Processing from ${inputType} to ${outputType} is not supported.`;
            state.processing = false;
            processBtn.disabled = false;
            processBtnText.textContent = 'Process Content';
            loadingSpinner.classList.add('hidden');
            return;
        }

        // 4. Make API call
        try {
            const postOptions = {
                method: 'POST',
                body: requestBody,
                headers: {
                    'ngrok-skip-browser-warning': 'true'
                }
            };
            
            if (isJsonRequest) {
                postOptions.headers['Content-Type'] = 'application/json';
            }

            const initialResponse = await fetch(BASE_URL + endpoint, postOptions);
            if (!initialResponse.ok) throw new Error(`Initial request failed: ${initialResponse.statusText}`);
            
            const jobData = await initialResponse.json();
            const { jobId } = jobData;

            processBtnText.textContent = 'Checking status...';
            const jobUrl = BASE_URL + jobUrlBase + jobId;
            const result = await pollJobStatus(jobUrl);

            if (outputType === 'Text') {
                outputText.value = result;
            } else if (outputType === 'Audio') {
                audioDownloadLink.href = result;
                audioResultPlaceholder.classList.add('hidden');
                audioDownloadLink.classList.remove('hidden');
            }

        } catch (error) {
            console.error('API Error:', error);
            errorMessage.textContent = 'An error occurred during processing.';
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

