import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GETSONGBPM_API_KEY")

# Base API URL
BASE_URL = "https://api.getsongbpm.com"

# Song to look up
song_name = "Blinding Lights"

# Step 1: Search for the song
search_url = f"{BASE_URL}/search/?api_key={API_KEY}&type=song&lookup={song_name}"
response = requests.get(search_url)

if response.status_code != 200:
    print("❌ Error during search:", response.status_code)
    exit()

search_data = response.json()

# Print raw search JSON
print("\n📦 RAW SEARCH RESPONSE:")
print(json.dumps(search_data, indent=4))

# Show formatted info from search results
print("\n🔍 Search Results Summary:")
results = search_data.get("search", [])
for i, result in enumerate(results, start=1):
    print(f"\nResult {i}:")
    print(f"  ID: {result.get('id')}  → Unique song ID")
    print(f"  Title: {result.get('title')}")
    print(f"  Artist: {result.get('artist')}")
    print(f"  URL: {result.get('url')}")

# Step 2: Get details of first song in results
if results:
    song_id = results[0]["id"]
    detail_url = f"{BASE_URL}/song/?api_key={API_KEY}&id={song_id}"
    detail_response = requests.get(detail_url)

    if detail_response.status_code == 200:
        detail_data = detail_response.json()

        # Print raw detailed JSON
        print("\n📦 RAW SONG DETAILS RESPONSE:")
        print(json.dumps(detail_data, indent=4))

        song_info = detail_data.get("song", {})

        print("\n🧠 Song Feature Summary:")
        print(f"  Title     : {song_info.get('title')}  → Name of the song")
        print(f"  Artist    : {song_info.get('artist')}  → Performer or band")
        print(f"  Tempo     : {song_info.get('tempo')} BPM  → Speed of the song")
        print(f"  Key       : {song_info.get('key')}  → Musical key (e.g., C, F#)")
        print(f"  Mode      : {song_info.get('mode')}  → 0 = Minor, 1 = Major")
        print(f"  Duration  : {song_info.get('duration')} seconds  → Song length")
        print(f"  URL       : {song_info.get('url')}  → Page on GetSongBPM")
    else:
        print("❌ Error retrieving song details.")
else:
    print("❌ No results found.")
