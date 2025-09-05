import requests
from django.conf import settings

def get_xray_token():
    url = "https://xray.cloud.getxray.app/api/v2/authenticate"
    payload = {
        "client_id": settings.XRAY_CLIENT_ID,
        "client_secret": settings.XRAY_CLIENT_SECRET
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


