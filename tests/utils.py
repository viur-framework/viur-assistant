import os

import pytest
import requests

SESSION_COOKIE = os.environ.get("SESSION_COOKIE")
"""
Session cookie for ViUR server running on localhost.

export SESSION_COOKIE="viur_cookie_$project=abc***xyz"
"""


@pytest.fixture
def session():
    assert SESSION_COOKIE, "SESSION_COOKIE not set in environment"
    s = requests.Session()
    name, value = SESSION_COOKIE.split("=")
    s.cookies.set(name, value)
    return s
