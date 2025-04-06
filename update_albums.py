import sqlite3
import os
import requests
import base64
import logging
import argparse
from dotenv import load_dotenv
from logger_config import get_script_logger

# Parse command line arguments
parser = argparse.ArgumentParser(description='Update album information from Spotify API')
parser.add_argument('--log-level', 
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='WARNING',
                    help='Set the logging level (default: WARNING)')
args = parser.parse_args()

# Convert string log level to logging constant
log_level = getattr(logging, args.log_level)

# Load environment variables
load_dotenv()

# Set up logger with the specified log level
logger = get_script_logger('update_albums', level=log_level)

# Database connection
DB_FILE = "music_weather.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

def get_spotify_access_token():
    """Get Spotify API access token using client credentials flow"""
    client_id = os.getenv("MUSIC_CLIENT_ID")
    client_secret = os.getenv("MUSIC_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise Exception("Missing Spotify API credentials in .env file")
    
    auth_url = "https://accounts.spotify.com/api/token"
    auth_headers = {
        "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
    }
    auth_data = {"grant_type": "client_credentials"}
    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)
    
    if auth_response.status_code != 200:
        raise Exception(f"Failed to get access token: {auth_response.text}")
    
    return auth_response.json().get("access_token")

def get_track_info(track_id, access_token):
    """Get track information including album, title, and artist using Spotify API"""
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Error getting track info for {track_id}: {response.text}")
        return None
    
    track_data = response.json()
    album_name = track_data.get("album", {}).get("name")
    track_name = track_data.get("name")
    artist_name = track_data.get("artists", [{}])[0].get("name")
    
    return {
        "album": album_name,
        "title": track_name,
        "artist": artist_name
    }

def update_albums():
    """Check all songs and update album information if it differs from Spotify data"""
    # Get Spotify access token
    access_token = get_spotify_access_token()
    
    # Get all songs from the database
    cursor.execute("SELECT spotify_id, title, artist, album FROM songs")
    songs = cursor.fetchall()
    
    logger.warning(f"Found {len(songs)} songs in the database")
    logger.warning("=" * 50)  # Add a separator line
    
    # Track statistics
    updated_count = 0
    unchanged_count = 0
    error_count = 0
    mismatch_count = 0
    
    # Collect updates to perform in bulk
    updates = []
    
    # Update each song
    for spotify_id, title, artist, current_album in songs:
        # Use debug level for processing messages to filter them out
        logger.debug(f"Processing: {title} by {artist}")
        
        spotify_info = get_track_info(spotify_id, access_token)
        
        if spotify_info:
            spotify_title = spotify_info["title"]
            spotify_artist = spotify_info["artist"]
            spotify_album = spotify_info["album"]
            
            # Check if title and artist match
            if spotify_title.lower() != title.lower() or spotify_artist.lower() != artist.lower():
                logger.warning(f"Spotify data mismatch for {spotify_id}")
                logger.warning(f"  Database: '{title}' by '{artist}'")
                logger.warning(f"  Spotify:  '{spotify_title}' by '{spotify_artist}'")
                mismatch_count += 1
            else:
                # If title and artist match, check album
                if spotify_album != current_album:
                    # Add to updates list instead of executing immediately
                    updates.append((spotify_album, spotify_id))
                    logger.warning(f"Will update album from '{current_album}' to '{spotify_album}'")
                    updated_count += 1
                else:
                    logger.debug(f"Album information is already correct: '{current_album}'")
                    unchanged_count += 1
        else:
            logger.error(f"Could not find track information for {title}")
            error_count += 1
        
        # Add a separator between songs
        logger.debug("-" * 50)
    
    # Perform bulk update if there are any updates
    if updates:
        logger.warning(f"Performing bulk update for {len(updates)} songs")
        cursor.executemany("""
            UPDATE songs 
            SET album = ? 
            WHERE spotify_id = ?
        """, updates)
        logger.warning("Bulk update completed")
    
    # Commit all changes at once
    conn.commit()
    logger.warning("=" * 50)  # Add a separator line
    logger.warning(f"Album update complete. Updated: {updated_count}, Unchanged: {unchanged_count}, Errors: {error_count}, Mismatches: {mismatch_count}")

if __name__ == "__main__":
    try:
        logger.warning("Starting album update process")
        update_albums()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        conn.close()
        logger.warning("Database connection closed") 