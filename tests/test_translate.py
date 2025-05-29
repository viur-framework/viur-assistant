import os
import pytest
import requests

BASE_URL = "http://localhost:8080/json/assistant/translate"

from utils import session

def print_response_on_error(response: requests.Response):
    if response.status_code >= 400:
        print(f"\n[HTTP ERROR] {response.status_code} {response.reason}")
        print(f"Response body:\n{response.text}\n")
    print(f"Response body:\n{response.text}\n")

def test_translate_minimal(session):
    params = {
        "text": "Hallo Welt!",
        "language": "en"
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 200
    assert response.text.strip()  # should contain translation

def test_translate_with_characteristic(session):
    params = {
        "text": "Hallo Welt!",
        "language": "en",
        "characteristic": "formal"
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 200
    assert response.text.strip()

def test_translate_with_simplified(session):
    params = {
        "text": "Hallo Welt!",
        "language": "en",
        "simplified": "true",
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 200
    assert response.text.strip()

def test_translate_conflicting_simplified_and_characteristic(session):
    params = {
        "text": "Hallo Welt!",
        "language": "en",
        "simplified": "true",
        "characteristic": "formal"
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 400  # BadRequest

def test_translate_missing_parameters(session):
    params = {
        "language": "en"
        # missing "text"
    }
    response = session.post(BASE_URL, params=params)
    print_response_on_error(response)
    assert response.status_code == 406  # Not Acceptable, per Vorgabe
