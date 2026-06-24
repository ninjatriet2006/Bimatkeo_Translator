import json
import urllib.request
import urllib.error

endpoint = "https://openapi.felo.ai/v2/chat"
key = "fk-ENEZHiJE8D6gQqLESiho3f9ArcZVeFDllOL4wdX6S49pVMkH"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {key}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

query = "Test translation prompt:\n\nPlease strictly follow the instruction and translate the following lines:\nLine 1: Hello world"
data = {
    "query": query
}

req = urllib.request.Request(
    endpoint, 
    data=json.dumps(data).encode('utf-8'),
    headers=headers,
    method="POST"
)

try:
    print("Sending request to Felo API...")
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("Success!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
except urllib.error.URLError as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
