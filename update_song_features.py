import sqlite3
import argparse
import logging
from logger_config import get_script_logger

# Parse command line arguments
parser = argparse.ArgumentParser(description='Update song features from master database')
parser.add_argument('--log-level', 
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='WARNING',
                    help='Set the logging level (default: WARNING)')
parser.add_argument('--batch-size', 
                    type=int,
                    default=1000,
                    help='Number of songs to process in each batch (default: 1000)')
args = parser.parse_args()

# Convert string log level to logging constant
log_level = getattr(logging, args.log_level)

# Set up logger with the specified log level
logger = get_script_logger('update_song_features', level=log_level)

# Database connections
SOURCE_DB = "songs_master.db"
TARGET_DB = "music_weather.db"

class Statistics:
    def __init__(self):
        self.total_processed = 0
        self.matches_found = 0
        self.updates_performed = 0
        self.not_found = 0
        self.errors = 0
        
    def print_summary(self):
        logger.warning("=" * 50)
        logger.warning("FINAL STATISTICS:")
        logger.warning(f"Total songs processed: {self.total_processed}")
        logger.warning(f"Matches found: {self.matches_found}")
        logger.warning(f"Updates performed: {self.updates_performed}")
        logger.warning(f"Songs not found: {self.not_found}")
        logger.warning(f"Errors encountered: {self.errors}")
        if self.total_processed > 0:
            match_rate = (self.matches_found / self.total_processed) * 100
            logger.warning(f"Match rate: {match_rate:.2f}%")
        logger.warning("=" * 50)

def update_song_features():
    """Update song features from master database to target database"""
    stats = Statistics()
    
    try:
        # Connect to both databases
        source_conn = sqlite3.connect(SOURCE_DB)
        source_cursor = source_conn.cursor()
        
        target_conn = sqlite3.connect(TARGET_DB)
        target_cursor = target_conn.cursor()
        
        logger.warning(f"Connected to source database: {SOURCE_DB}")
        logger.warning(f"Connected to target database: {TARGET_DB}")
        
        # Get count of songs in target database
        target_cursor.execute("SELECT COUNT(*) FROM songs")
        total_songs = target_cursor.fetchone()[0]
        logger.warning(f"Found {total_songs} songs in the target database")
        
        # Track statistics
        updated_count = 0
        not_found_count = 0
        batch_size = args.batch_size
        
        # Process songs in batches
        for offset in range(0, total_songs, args.batch_size):
            batch_num = offset//args.batch_size + 1
            total_batches = (total_songs + args.batch_size - 1)//args.batch_size
            logger.warning(f"Processing batch {batch_num} of {total_batches}")
            
            # Get a batch of songs from the target database
            target_cursor.execute("SELECT spotify_id, title FROM songs LIMIT ? OFFSET ?", 
                                (args.batch_size, offset))
            target_songs = target_cursor.fetchall()
            
            # Collect updates to perform in bulk
            updates = []
            
            # Process each song from the target database
            for spotify_id, title in target_songs:
                stats.total_processed += 1
                logger.debug(f"Processing: {title}")
                
                try:
                    # Find matching song in source database by title
                    source_cursor.execute("""
                        SELECT danceability, energy, valence 
                        FROM songs_master_table 
                        WHERE track_name = ?
                    """, (title,))
                    result = source_cursor.fetchone()
                    
                    if result:
                        stats.matches_found += 1
                        danceability, energy, valence = result
                        # Add to updates list
                        updates.append((danceability, energy, valence, spotify_id))
                        logger.debug(f"Will update features for: {title}")
                    else:
                        stats.not_found += 1
                        logger.debug(f"Song not found in master database: {title}")
                except Exception as e:
                    stats.errors += 1
                    logger.error(f"Error processing song {title}: {e}")
            
            # Perform bulk update for this batch if there are any updates
            if updates:
                try:
                    target_cursor.executemany("""
                        UPDATE songs 
                        SET danceability = ?, energy = ?, valence = ?
                        WHERE spotify_id = ?
                    """, updates)
                    target_conn.commit()  # Commit after each batch
                    stats.updates_performed += len(updates)
                    logger.warning(f"Batch {batch_num}/{total_batches} update completed. "
                                 f"Progress: {min(offset + args.batch_size, total_songs)}/{total_songs} songs")
                except Exception as e:
                    stats.errors += 1
                    logger.error(f"Error performing batch update: {e}")
            
            # Print intermediate statistics every 5 batches
            if batch_num % 5 == 0:
                stats.print_summary()
        
        # Print final statistics
        stats.print_summary()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        # Close database connections
        if 'source_conn' in locals():
            source_conn.close()
        if 'target_conn' in locals():
            target_conn.close()
        logger.warning("Database connections closed")
        
        # Print final statistics even if there was an error
        stats.print_summary()

if __name__ == "__main__":
    logger.warning("Starting song feature update process")
    update_song_features() 