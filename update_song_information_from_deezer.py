import sqlite3
import os
import requests
import json
import logging
import argparse
from datetime import datetime
from logger_config import get_script_logger
import re
import time
from tqdm import tqdm

# Parse command line arguments
parser = argparse.ArgumentParser(description='Update song information from Deezer API')
parser.add_argument('--log-level', 
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='WARNING',
                    help='Set the logging level (default: WARNING)')
parser.add_argument('--batch-size', type=int, default=50,
                    help='Number of songs to process in each batch (default: 50)')
parser.add_argument('--limit', type=int, default=0,
                    help='Limit the number of songs to process (default: 0, meaning no limit)')
parser.add_argument('--force-download', action='store_true',
                    help='Force download of previews even if they already exist')
parser.add_argument('--delay', type=float, default=1.0,
                    help='Delay between API calls in seconds (default: 1.0)')
parser.add_argument('--resume', action='store_true',
                    help='Resume from last processed song')
args = parser.parse_args()

# Convert string log level to logging constant
log_level = getattr(logging, args.log_level)

# Set up logger
logger = get_script_logger('update_song_info_deezer', level=log_level)

# Database connection
DB_FILE = "music_weather.db"

# Create output directories
OUTPUT_DIR = "deezer_data"
AUDIO_DIR = "deezer_previews"
PROGRESS_FILE = "deezer_progress.json"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

def load_progress():
    """Load progress from file if it exists"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'last_processed': None, 'processed_ids': []}
    return {'last_processed': None, 'processed_ids': []}

def save_progress(spotify_id):
    """Save progress to file"""
    progress = load_progress()
    progress['last_processed'] = spotify_id
    progress['processed_ids'].append(spotify_id)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def add_preview_column():
    """
    Add preview_available column to songs table if it doesn't exist
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(songs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "preview_available" not in columns:
            cursor.execute("ALTER TABLE songs ADD COLUMN preview_available BOOLEAN DEFAULT 0")
            conn.commit()
            logger.info("Added preview_available column to songs table")
        else:
            logger.debug("preview_available column already exists")
            
    except sqlite3.Error as e:
        logger.error(f"Error adding preview_available column: {e}")
    finally:
        if conn:
            conn.close()

def update_preview_status(spotify_id, has_preview):
    """
    Update the preview_available status for a song in the database
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE songs 
            SET preview_available = ? 
            WHERE spotify_id = ?
        """, (1 if has_preview else 0, spotify_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating preview status: {e}")
        return False
    finally:
        if conn:
            conn.close()

def sanitize_filename(filename):
    """
    Sanitize the filename by removing invalid characters
    """
    # Remove invalid characters and replace spaces with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    sanitized = sanitized.replace(' ', '_')
    return sanitized

def download_preview(preview_url, track_name, artist_name, spotify_id):
    """
    Download the preview audio file from Deezer
    Returns True if successful, False otherwise
    """
    try:
        if not preview_url:
            logger.warning(f"No preview URL available for '{track_name}' by '{artist_name}'")
            update_preview_status(spotify_id, False)
            return False
            
        # Create sanitized filename
        filename = f"{sanitize_filename(track_name)}_{sanitize_filename(artist_name)}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Check if file already exists and we're not forcing download
        if os.path.exists(filepath) and not args.force_download:
            logger.info(f"Preview already exists for '{track_name}' by '{artist_name}'")
            update_preview_status(spotify_id, True)
            return True
        
        # Download the file
        response = requests.get(preview_url, stream=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info(f"✅ Downloaded preview for '{track_name}' by '{artist_name}'")
            update_preview_status(spotify_id, True)
            return True
        else:
            logger.error(f"Failed to download preview for '{track_name}' by '{artist_name}': {response.status_code}")
            update_preview_status(spotify_id, False)
            return False
            
    except Exception as e:
        logger.error(f"Error downloading preview for '{track_name}' by '{artist_name}': {e}")
        update_preview_status(spotify_id, False)
        return False

def search_deezer_track(title, artist):
    """
    Search for a track on Deezer API
    Returns the first matching track or None if no match found
    """
    try:
        # Format the search query
        query = f"{title} artist:'{artist}'"
        encoded_query = requests.utils.quote(query)
        
        # Make the API request
        url = f"https://api.deezer.com/search?q={encoded_query}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]  # Return first match
            else:
                logger.warning(f"No results found for '{title}' by '{artist}'")
                return None
        else:
            logger.error(f"Error searching Deezer API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error searching Deezer API: {e}")
        return None

def update_song_info_from_deezer():
    """
    Update song information from Deezer API and save to JSON files
    """
    try:
        # Add preview_available column if it doesn't exist
        add_preview_column()
        
        # Connect to the database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all songs from the database
        cursor.execute("SELECT spotify_id, title, artist FROM songs")
        songs = cursor.fetchall()
        
        # Load progress
        progress = load_progress()
        processed_ids = set(progress['processed_ids'])
        
        # Filter out already processed songs unless force download is enabled
        if not args.force_download:
            songs = [song for song in songs if song[0] not in processed_ids]
        
        # Apply limit if specified
        if args.limit > 0 and args.limit < len(songs):
            songs = songs[:args.limit]
            logger.warning(f"Limited to {args.limit} songs")
        
        total_songs = len(songs)
        logger.warning(f"Found {total_songs} songs to process")
        
        # Track statistics
        processed_count = 0
        success_count = 0
        error_count = 0
        download_count = 0
        skipped_count = 0
        
        # Process songs with progress bar
        with tqdm(total=total_songs, desc="Processing songs") as pbar:
            for spotify_id, title, artist in songs:
                try:
                    logger.debug(f"Searching for: {title} by {artist}")
                    
                    # Search Deezer API
                    track_info = search_deezer_track(title, artist)
                    
                    if track_info:
                        # Save the raw response to a JSON file
                        output_file = os.path.join(OUTPUT_DIR, f"{spotify_id}.json")
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(track_info, f, indent=2, ensure_ascii=False)
                        
                        # Download preview if available
                        if track_info.get('preview'):
                            if download_preview(track_info['preview'], title, artist, spotify_id):
                                download_count += 1
                            else:
                                skipped_count += 1
                        
                        success_count += 1
                        logger.info(f"✅ Found and saved data for '{title}' by '{artist}'")
                    else:
                        error_count += 1
                        logger.warning(f"❌ No results found for '{title}' by '{artist}'")
                        update_preview_status(spotify_id, False)
                    
                    processed_count += 1
                    save_progress(spotify_id)
                    
                    # Rate limiting delay
                    time.sleep(args.delay)
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing '{title}' by '{artist}': {e}")
                    update_preview_status(spotify_id, False)
                
                pbar.update(1)
        
        logger.warning(f"\nUpdate complete. Processed: {processed_count}, Success: {success_count}, Errors: {error_count}, Downloads: {download_count}, Skipped: {skipped_count}")
        logger.warning(f"Results saved to {OUTPUT_DIR}/")
        logger.warning(f"Audio previews saved to {AUDIO_DIR}/")
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_song_info_from_deezer() 