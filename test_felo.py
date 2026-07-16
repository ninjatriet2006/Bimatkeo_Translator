import requests
import json

url = "https://openapi.felo.ai/v1/models"
headers = {
    "Authorization": "Bearer fk-BidgKZEAW7Gio1eWVgCRi2TVNvJojavU5NXt8FULqNEoEkfu"
}
response = requests.get(url, headers=headers)
print("Status:", response.status_code)
try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)

