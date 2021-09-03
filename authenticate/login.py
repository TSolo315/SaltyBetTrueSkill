import requests
import os
import json
from pathlib import Path


URL_SIGNIN = 'https://www.saltybet.com/authenticate?signin=1'

env_login_data = False

if not env_login_data:
    with open(Path(__file__).resolve(strict=True).parent / "auth.json", "r") as read_file:
        auth_data = json.load(read_file)

    EKEY = auth_data["ekey"]
    PKEY = auth_data["pkey"]


def login():
    """
    Authenticate SaltBot on the SaltyBet website.

    Login to SaltyBet by using the EMAIL and PASSWORD stored in the auth.json file or .env
    file. Successfully logging in returns session and request objects/

    If using a json file name file auth.json. Place in same directory as this file (authenticate.)
    .json Format:

    {
    "ekey": "example@example.com",
    "pkey": "examplePassword123"
    }

    Else set env_login_data to True and use env variables:

    .env Format:
        EMAIL = "example@example.com"
        PASSWORD = "examplePassword123"

    Args:
        None

    Returns:
        session (session): A requests library session.
        request (request): A requests library request.

    """
    session = requests.session()

    # This is the form data that the page sends when logging in

    if not env_login_data:
        login_data = {
            'email': EKEY,
            'pword': PKEY,
            'authenticate': 'signin'
        }
    else:
        login_data = {
            'email': os.environ.get('SALTBOT_EMAIL'),
            'pword': os.environ.get('SALTBOT_PASSWORD'),
            'authenticate': 'signin'
        }

    # Authenticate
    request = session.post(URL_SIGNIN, data=login_data)

    # Check for successful login & redirect
    if (request.url != "https://www.saltybet.com/" and request.url !=
            "http://www.saltybet.com/"):
        raise RuntimeError("Error: Wrong URL: " + request.url)

    return session, request
