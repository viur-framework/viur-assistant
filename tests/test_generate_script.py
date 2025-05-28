from pprint import pprint

import requests

from utils import session

BASE_URL = "http://localhost:8080/json/assistant/generate_script"


def print_response_on_error(response: requests.Response):
    if response.status_code >= 400:
        print(f"\n[HTTP ERROR] {response.status_code} {response.reason}")
        try:
            pprint(response.json())
        except ValueError:
            print(f"Response body:\n{response.text}\n")


def test_generate_script_minimal_prompt(session):
    params = {
        "prompt": "Erstelle ein einfaches Python-Skript, das Hallo Welt ausgibt."
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 200
    assert "content" in response.text or "model" in response.text


def test_generate_script_with_modules(session):
    params = {
        "prompt": "Erzeuge ein Skript mit Modulstruktur.",
        "modules_to_include": ["user", "file"],
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 200
    assert "content" in response.text or "model" in response.text


def test_generate_script_with_thinking_and_caching(session):
    params = {
        "prompt": "Erkläre wie Caching funktioniert.",
        "enable_caching": True,
        "max_thinking_tokens": 1024,
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 200
    assert "content" in response.text or "model" in response.text


def test_generate_script_missing_prompt(session):
    params = {
        "enable_caching": True,
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 406  # Not Acceptable
