import requests
import os
import json
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("MUSIC_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("MUSIC_CLIENT_SECRET")

# === Helper Functions ===

def get_spotify_token():
    url = 'https://accounts.spotify.com/api/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    r = requests.post(url, headers=headers, data=data)
    r.raise_for_status()
    return r.json()['access_token']

def get_spotify_track_info(track_id, token):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def search_musicbrainz(track_name, artist_name):
    query = f'recording:"{track_name}" AND artist:"{artist_name}"'
    url = f"https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json"
    headers = {'User-Agent': 'MusicMatcher/1.0 ( your_email@example.com )'}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def fetch_acousticbrainz_data(mbid, level="low-level"):
    url = f"http://acousticbrainz.org/{mbid}/{level}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        return {"error": f"No AcousticBrainz {level} data found for this MBID."}

# === Main Script ===

spotify_track_id = "6DwBCjospi1c9WsRVfoCwN"  # Example: Blinding Lights

try:
    print("🔐 Fetching Spotify token...")
    token = get_spotify_token()

    print("🎵 Fetching Spotify track info...")
    track_data = get_spotify_track_info(spotify_track_id, token)
    track_name = track_data['name']
    artist_name = track_data['artists'][0]['name']

    print(f"\n🎯 Track: {track_name} by {artist_name}")

    print("\n🔍 Searching MusicBrainz...")
    mb_results = search_musicbrainz(track_name, artist_name)

    if mb_results['recordings']:
        mbid = mb_results['recordings'][0]['id']
        print(f"\n✅ Found MBID: {mbid}")

        print("\n🎧 Fetching AcousticBrainz low-level features...")
        low_level = fetch_acousticbrainz_data(mbid, level="low-level")

        print("🎼 Fetching AcousticBrainz high-level features...")
        high_level = fetch_acousticbrainz_data(mbid, level="high-level")

        print("\n📦 Low-Level Features:")
        print(json.dumps(low_level, indent=4))

        print("\n📊 High-Level Features:")
        print(json.dumps(high_level, indent=4))

    else:
        print("❌ No MBID found on MusicBrainz.")

except Exception as e:
    print("💥 Error:", e)
