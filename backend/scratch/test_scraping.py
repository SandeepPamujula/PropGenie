import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.property_scraper import fetch_url, ALinkExtractor
from urllib.parse import urlparse

url = "https://www.nobroker.in/property/plot/bangalore/Indiranagar?price=10000000,100000000&searchParam=W3sibGF0IjoxMi45NzgzNjkyLCJsb24iOjc3LjY0MDgzNTYsInBsYWNlSWQiOiJDaElKa1FOM0dLUVdyanNSTmhCUUpyaEdEN1UiLCJwbGFjZU5hbWUiOiJJbmRpcmFuYWdhciJ9XQ==&radius=4.0&city=bangalore&locality=Indiranagar"

print(f"Fetching: {url}")
html, err = fetch_url(url)
if err:
    print(f"Error fetching URL: {err}")
    sys.exit(1)

print(f"HTML length: {len(html)}")

parser = ALinkExtractor()
parser.feed(html)

print(f"Total links found: {len(parser.links)}")

print("\n--- Links containing '/property/' or '/detail/' ---")
for link in parser.links:
    if "property" in link or "detail" in link:
        print(link)
