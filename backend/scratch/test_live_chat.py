import hashlib
import json
import urllib.request


def test_live_chat():
    url = "https://dxrwuyl33cssd.cloudfront.net/api/chat"
    body = {"message": "Looking for a 2 BHK for rent in Indiranagar, Bangalore under 40k"}
    body_bytes = json.dumps(body).encode('utf-8')

    # Calculate body SHA-256 hash
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    print(f"Body hash: {body_hash}")

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "X-Session-ID": "test-live-session-999",
        "x-amz-content-sha256": body_hash,
        "User-Agent": "Python-Client"
    }

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")

    try:
        print("Sending request to live CloudFront endpoint...")
        with urllib.request.urlopen(req) as response:
            print(f"Response Status: {response.status}")
            print(f"Response Headers: {dict(response.headers)}")
            print("\nStreaming response events:")
            for line in response:
                line_decoded = line.decode('utf-8').strip()
                if line_decoded:
                    print(line_decoded)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_live_chat()
