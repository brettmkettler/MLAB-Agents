import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class APIClient:
    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.resource = os.getenv('RESOURCE')
        self.token_url = os.getenv('TOKEN_URL')
        self.api_base_url = os.getenv('API_BASE_URL')
        self.access_token = None

    def get_access_token(self):
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'resource': self.resource
        }
        try:
            response = requests.post(self.token_url, data=payload)
            response.raise_for_status()
            self.access_token = response.json().get('access_token')
            if not self.access_token:
                raise Exception("Access token not found in response")
        except requests.exceptions.RequestException as e:
            print(f"Error obtaining access token: {e}")
            return False
        return True

    def get_station_overview(self):
        if not self.access_token:
            print("No access token. Please authenticate first.")
            return
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        try:
            #response = requests.get(f"{self.api_base_url}/view/station/overview", headers=headers)
            response = requests.get(f"{self.api_base_url}/view/station/0", headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting station overview: {e}")
            return None

if __name__ == "__main__":
    client = APIClient()

    if client.get_access_token():
        station_overview = client.get_station_overview()
        if station_overview:
            print(json.dumps(station_overview, indent=4))
        else:
            print("Failed to retrieve station overview.")
    else:
        print("Failed to authenticate.")
