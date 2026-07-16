import requests
import json
import base64

url = "https://openapi.felo.ai/v1/chat/completions"
headers = {
    "Authorization": "Bearer fk-BidgKZEAW7Gio1eWVgCRi2TVNvJojavU5NXt8FULqNEoEkfu",
    "Content-Type": "application/json"
}

# 1x1 white pixel in base64
img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="

payload = {
    "model": "felo-search",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)
print("Status:", response.status_code)
try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)

