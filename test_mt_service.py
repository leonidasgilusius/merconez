import requests

# The base URL for the running MT service
BASE_URL = "http://127.0.0.1:5004"

def test_translate_endpoint():
    # The endpoint path
    url = f"{BASE_URL}/api/v1/translate"

    # The data we want to send
    payload = {
        "text": "Hello world"
    }

    # Make the request
    response = requests.post(url, json=payload)

    # Assert that the request was successful
    assert response.status_code == 200

    # Assert that the response format is correct
    response_data = response.json()
    assert "translatedText" in response_data
    print(f"Test passed! Received translation: {response_data['translatedText']}")