import sqlite3
import os
import requests
import base64
import logging
import argparse
import json
from dotenv import load_dotenv
from logger_config import get_script_logger

# Parse command line arguments
parser = argparse.ArgumentParser(description='Update song information from Spotify API')
parser.add_argument('--log-level', 
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='WARNING',
                    help='Set the logging level (default: WARNING)')
parser.add_argument('--batch-size', type=int, default=50,
                    help='Number of songs to process in each batch (default: 50)')
parser.add_argument('--sample', action='store_true',
                    help='Print sample API responses and exit')
args = parser.parse_args()

# Convert string log level to logging constant
log_level = getattr(logging, args.log_level)

# Load environment variables
load_dotenv()

# Set up logger with the specified log level
logger = get_script_logger('update_song_info', level=log_level)

# Database connection
DB_FILE = "music_weather.db"

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

def print_sample_responses():
    """Print sample API responses for demonstration"""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get Spotify access token
        access_token = get_spotify_access_token()
        
        # Get one song from the database
        cursor.execute("SELECT spotify_id, title, artist FROM songs LIMIT 1")
        song = cursor.fetchone()
        
        if not song:
            print("No songs found in database")
            return
            
        spotify_id, title, artist = song
        print(f"\nSample song: '{title}' by '{artist}' (ID: {spotify_id})")
        
        # Get track info
        url = f"https://api.spotify.com/v1/tracks/{spotify_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            track_data = response.json()
            print("\nTrack API Response:")
            print(json.dumps(track_data, indent=2))
            
            # Get artist info
            artist_id = track_data.get("artists", [{}])[0].get("id")
            if artist_id:
                artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
                artist_response = requests.get(artist_url, headers=headers)
                if artist_response.status_code == 200:
                    artist_data = artist_response.json()
                    print("\nArtist API Response:")
                    print(json.dumps(artist_data, indent=2))
            
            # Get album info
            album_id = track_data.get("album", {}).get("id")
            if album_id:
                album_url = f"https://api.spotify.com/v1/albums/{album_id}"
                album_response = requests.get(album_url, headers=headers)
                if album_response.status_code == 200:
                    album_data = album_response.json()
                    print("\nAlbum API Response:")
                    print(json.dumps(album_data, indent=2))
        else:
            print(f"Error getting track info: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def get_track_info(track_id, access_token):
    """Get track information including album, release date, and genres using Spotify API"""
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Error getting track info for {track_id}: {response.text}")
        return None
    
    track_data = response.json()
    
    # Get basic track info
    track_name = track_data.get("name")
    artist_name = track_data.get("artists", [{}])[0].get("name")
    artist_id = track_data.get("artists", [{}])[0].get("id")
    
    # Get album info
    album_data = track_data.get("album", {})
    album_name = album_data.get("name")
    album_id = album_data.get("id")
    release_date = album_data.get("release_date", "")
    
    # Extract year from release date (format: YYYY-MM-DD or YYYY)
    release_year = int(release_date.split("-")[0]) if release_date else None
    
    # Get genres from artist
    genres = []
    if artist_id:
        artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
        artist_response = requests.get(artist_url, headers=headers)
        if artist_response.status_code == 200:
            artist_data = artist_response.json()
            genres = artist_data.get("genres", [])
    
    return {
        "album": album_name,
        "title": track_name,
        "artist": artist_name,
        "release_year": release_year,
        "genres": genres,
        "album_id": album_id
    }

def get_first_word(text):
    """Get the first word of a text, handling special characters"""
    if not text:
        return ""
    # Split on whitespace and take first word, removing any special characters
    return text.split()[0].lower().strip('.,!?()[]{}')

def is_approximate_match(str1, str2):
    """Check if two strings match approximately by comparing first words"""
    if not str1 or not str2:
        return False
    # Try exact match first
    if str1.lower() == str2.lower():
        return True
    # Try first word match
    return get_first_word(str1) == get_first_word(str2)

def update_song_info():
    """Update song information from Spotify API"""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get Spotify access token
        access_token = get_spotify_access_token()
        
        # Get all songs from the database with their current info
        cursor.execute("SELECT spotify_id, title, artist FROM songs")
        songs = cursor.fetchall()
        
        total_songs = len(songs)
        logger.warning(f"Found {total_songs} songs in the database")
        
        # Track statistics
        updated_count = 0
        error_count = 0
        mismatch_count = 0
        approximate_match_count = 0
        mismatch_details = []  # Store details of mismatches
        
        # Process songs in batches
        batch_size = args.batch_size
        updates = []  # Store all updates
        
        for i in range(0, total_songs, batch_size):
            batch = songs[i:i + batch_size]
            logger.warning(f"Processing batch {i//batch_size + 1}/{(total_songs + batch_size - 1)//batch_size}")
            
            for spotify_id, db_title, db_artist in batch:
                try:
                    # Get track info
                    info = get_track_info(spotify_id, access_token)
                    
                    if info:
                        # Verify that we have the correct song by checking title and artist
                        spotify_title = info["title"]
                        spotify_artist = info["artist"]
                        
                        # Check for exact matches first
                        title_matches = spotify_title.lower() == db_title.lower()
                        artist_matches = spotify_artist.lower() == db_artist.lower()
                        
                        # If no exact match, try approximate match
                        if not (title_matches and artist_matches):
                            title_approx = is_approximate_match(spotify_title, db_title)
                            artist_approx = is_approximate_match(spotify_artist, db_artist)
                            
                            if title_approx and artist_approx:
                                logger.warning(f"\nApproximate match found for ID: {spotify_id}")
                                logger.warning(f"Database: '{db_title}' by '{db_artist}'")
                                logger.warning(f"Spotify:  '{spotify_title}' by '{spotify_artist}'")
                                logger.warning("Using approximate match for update")
                                approximate_match_count += 1
                            else:
                                mismatch_count += 1
                                mismatch_details.append({
                                    'spotify_id': spotify_id,
                                    'db_title': db_title,
                                    'db_artist': db_artist,
                                    'spotify_title': spotify_title,
                                    'spotify_artist': spotify_artist,
                                    'title_diff': not title_matches,
                                    'artist_diff': not artist_matches
                                })
                                
                                logger.warning(f"\nMismatch found for ID: {spotify_id}")
                                logger.warning(f"Database: '{db_title}' by '{db_artist}'")
                                logger.warning(f"Spotify:  '{spotify_title}' by '{spotify_artist}'")
                                if not title_matches:
                                    logger.warning("Title mismatch!")
                                if not artist_matches:
                                    logger.warning("Artist mismatch!")
                                continue
                        
                        # Add to updates list
                        updates.append((
                            info["album"],
                            info["release_year"],
                            ",".join(info["genres"]),
                            spotify_id
                        ))
                        updated_count += 1
                        logger.debug(f"Queued update for '{db_title}' by '{db_artist}'")
                    else:
                        error_count += 1
                        logger.error(f"Failed to get data for track {spotify_id}")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing track {spotify_id}: {e}")
            
            # Perform bulk update after each batch
            if updates:
                cursor.executemany("""
                    UPDATE songs 
                    SET album = ?,
                        release_year = ?,
                        genres = ?
                    WHERE spotify_id = ?
                """, updates)
                conn.commit()
                updates = []  # Clear the updates list
                logger.warning(f"Bulk updated {len(updates)} songs in this batch")
            
            logger.warning(f"Processed {min(i + batch_size, total_songs)}/{total_songs} songs")
        
        # Print detailed mismatch summary
        if mismatch_details:
            logger.warning("\n=== Mismatch Summary ===")
            logger.warning(f"Total mismatches: {mismatch_count} out of {total_songs} songs ({(mismatch_count/total_songs)*100:.2f}%)")
            logger.warning(f"Approximate matches used: {approximate_match_count} ({(approximate_match_count/total_songs)*100:.2f}%)")
            
            title_mismatches = sum(1 for m in mismatch_details if m['title_diff'])
            artist_mismatches = sum(1 for m in mismatch_details if m['artist_diff'])
            
            logger.warning(f"Title mismatches: {title_mismatches} ({(title_mismatches/total_songs)*100:.2f}%)")
            logger.warning(f"Artist mismatches: {artist_mismatches} ({(artist_mismatches/total_songs)*100:.2f}%)")
            
            # Print first 5 mismatches as examples
            logger.warning("\nExample mismatches:")
            for m in mismatch_details[:5]:
                logger.warning(f"\nID: {m['spotify_id']}")
                logger.warning(f"Database: '{m['db_title']}' by '{m['db_artist']}'")
                logger.warning(f"Spotify:  '{m['spotify_title']}' by '{m['spotify_artist']}'")
        
        logger.warning(f"\nUpdate complete. Updated: {updated_count}, Errors: {error_count}, Mismatches: {mismatch_count}, Approximate Matches: {approximate_match_count}")
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def add_new_columns():
    """Add new columns to the songs table if they don't exist"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if album column exists
        cursor.execute("PRAGMA table_info(songs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "album" not in columns:
            cursor.execute("ALTER TABLE songs ADD COLUMN album TEXT")
            logger.info("Added album column to songs table")
        
        # Add genres column if it doesn't exist
        if "genres" not in columns:
            cursor.execute("ALTER TABLE songs ADD COLUMN genres TEXT")
            logger.info("Added genres column to songs table")
        
        conn.commit()
        logger.info("Database schema updated successfully")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("Columns already exist")
        else:
            logger.error(f"Error adding columns: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if args.sample:
        print_sample_responses()
    else:
        add_new_columns()
        update_song_info() 