import requests

def get_xray_test_details(test_key, token):
    url = f"https://xray.cloud.getxray.app/api/v2/tests/{test_key}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()