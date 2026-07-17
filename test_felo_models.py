import requests

key = "fk-BidgKZEAW7Gio1eWVgCRi2TVNvJojavU5NXt8FULqNEoEkfu"
headers = {"Authorization": f"Bearer {key}"}

urls_to_test = [
    "https://openapi.felo.ai/v1/models",
    "https://openapi.felo.ai/v2/models",
    "https://openapi.felo.ai/models"
]

for url in urls_to_test:
    print(f"Testing {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Response: {r.json()}")
            break
        else:
            print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
