1. https://aistudio.google.com/ -> "**Get API key**"
2. ``` .env
   GEMINI_API_KEY="your_new_gemini_api_key_here"
   ```

#### Step 4: Run the Test
This is the moment of truth! This requires two terminals.
1. **Terminal 1: Start the Backend**: In your first terminal, start all the backend services (including your new one!) using `honcho`.
    ```
    honcho start
    ```
    You should see output from all five services (asr, tts, ocr, mt, and intelligence) starting up.
2. **Terminal 2: Run Pytest**: Open a **new terminal window**. Make sure you activate the virtual environment again in this new terminal (`source venv/bin/activate`). Then, run pytest:
    ```
    pytest -v
    ```
You should see output indicating that `tests/test_mt_service.py` was found and that `1 passed`. The `print` statement from your test code should also appear. ✅