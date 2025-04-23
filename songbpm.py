import requests
import json
from dotenv import load_dotenv
import os
import urllib.parse

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GETSONGBPM_API_KEY")

if not API_KEY:
    print("❌ Error: GETSONGBPM_API_KEY not found in .env file")
    exit(1)

print(f"Using API Key: {API_KEY[:5]}...{API_KEY[-5:]}")

# Base API URL
BASE_URL = "https://api.getsong.co"

def get_raw_json(song_name, artist_name=None):
    """
    Get raw JSON response from the GetSongBPM API
    """
    # URL encode the song name and artist name
    encoded_song = urllib.parse.quote(song_name)
    
    # Construct the search URL with API key in header
    search_url = f"{BASE_URL}/search/?api_key={API_KEY}&type=song&lookup={encoded_song}"
    
    # Add artist name if provided
    if artist_name:
        encoded_artist = urllib.parse.quote(artist_name)
        search_url = f"{BASE_URL}/search/?api_key={API_KEY}&type=both&lookup=song:{encoded_song} artist:{encoded_artist}"
    
    print(f"\n🔍 Searching for: {song_name}")
    if artist_name:
        print(f"   Artist: {artist_name}")
    print(f"URL: {search_url}")

    try:
        response = requests.get(search_url)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error during search: {response.status_code}")
            print(f"Error Response: {response.text}")
            return None

        # Print raw response
        print("\n📦 RAW API RESPONSE:")
        print(json.dumps(response.json(), indent=4))
        
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return None

def main():
    # Test with a sample song
    song_name = "Blinding Lights"
    artist_name = "The Weeknd"
    get_raw_json(song_name, artist_name)

if __name__ == "__main__":
    main()
