import sqlite3
import csv
import os
import re
import logging
import argparse
from logger_config import get_script_logger

# Parse command line arguments
parser = argparse.ArgumentParser(description='Parse CSV files for song information and update database')
parser.add_argument('--csv-file', type=str, required=True,
                    help='Path to the CSV file to parse')
parser.add_argument('--log-level', 
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='WARNING',
                    help='Set the logging level (default: WARNING)')
parser.add_argument('--batch-size', type=int, default=50,
                    help='Number of records to process in each batch (default: 50)')
parser.add_argument('--non-interactive', action='store_true',
                    help='Run in non-interactive mode (not recommended)')
args = parser.parse_args()

# Convert string log level to logging constant
log_level = getattr(logging, args.log_level)

# Set up logger
logger = get_script_logger('csv_parsing_songs_update', level=log_level)

# Database connection
DB_FILE = "music_weather.db"

def get_database_schema():
    """
    Get the schema of the songs table from the database.
    Returns a dictionary with column names and their types.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(songs)")
        columns = cursor.fetchall()
        
        schema = {}
        for col in columns:
            # col[1] is the column name, col[2] is the data type
            schema[col[1]] = col[2]
        
        return schema
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def read_csv_header(csv_file_path):
    """
    Read the header row of the CSV file.
    Returns a list of column names.
    """
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            header = next(reader, None)
            return header
    except Exception as e:
        logger.error(f"Error reading CSV header: {e}")
        return []

def interactive_column_matching(csv_columns, db_columns):
    """
    Interactive mode to match CSV columns with database columns.
    Returns two dictionaries:
    1. Matching columns (for finding songs in the database)
    2. Update columns (for updating song information)
    """
    print("\n=== Interactive Column Matching ===")
    print("CSV Columns:")
    for i, col in enumerate(csv_columns):
        print(f"  {i+1}. {col}")
    
    print("\nDatabase Columns:")
    for i, col in enumerate(db_columns):
        print(f"  {i+1}. {col}")
    
    print("\n=== STEP 1: MATCHING COLUMNS ===")
    print("Select columns to use for matching songs in the database.")
    
    matching_columns = {}
    
    # First, ask for title column
    print("\nWhich CSV column contains the song title?")
    title_col = input("Enter column name or number (or 'skip' to skip): ")
    
    if title_col.lower() != 'skip':
        # Try to find the column by number
        try:
            idx = int(title_col) - 1
            if 0 <= idx < len(csv_columns):
                title_col = csv_columns[idx]
            else:
                print(f"Invalid column number. Please enter a number between 1 and {len(csv_columns)}")
                title_col = None
        except ValueError:
            # Try to find the column by name
            if title_col not in csv_columns:
                print(f"Column '{title_col}' not found in CSV. Skipping title matching.")
                title_col = None
        
        if title_col:
            matching_columns[title_col] = 'title'
            print(f"Mapped '{title_col}' to 'title' for matching")
    
    # Next, ask for artist column
    print("\nWhich CSV column contains the artist name?")
    artist_col = input("Enter column name or number (or 'skip' to skip): ")
    
    if artist_col.lower() != 'skip':
        # Try to find the column by number
        try:
            idx = int(artist_col) - 1
            if 0 <= idx < len(csv_columns):
                artist_col = csv_columns[idx]
            else:
                print(f"Invalid column number. Please enter a number between 1 and {len(csv_columns)}")
                artist_col = None
        except ValueError:
            # Try to find the column by name
            if artist_col not in csv_columns:
                print(f"Column '{artist_col}' not found in CSV. Skipping artist matching.")
                artist_col = None
        
        if artist_col:
            matching_columns[artist_col] = 'artist'
            print(f"Mapped '{artist_col}' to 'artist' for matching")
    
    # Check if we have at least one matching column
    if not matching_columns:
        print("\nYou must select at least one column for matching (title and/or artist).")
        print("Please try again.")
        return interactive_column_matching(csv_columns, db_columns)
    
    # Ask if user wants to add more matching columns
    while True:
        print("\nCurrent matching columns:")
        for csv_col, db_col in matching_columns.items():
            print(f"  CSV: '{csv_col}' -> DB: '{db_col}'")
        
        add_more = input("\nDo you want to add more matching columns? (yes/no): ")
        if add_more.lower() != 'yes':
            break
        
        print("\nWhich CSV column do you want to add for matching?")
        csv_col = input("Enter column name or number: ")
        
        # Try to find the column by number
        try:
            idx = int(csv_col) - 1
            if 0 <= idx < len(csv_columns):
                csv_col = csv_columns[idx]
            else:
                print(f"Invalid column number. Please enter a number between 1 and {len(csv_columns)}")
                continue
        except ValueError:
            # Try to find the column by name
            if csv_col not in csv_columns:
                print(f"Column '{csv_col}' not found in CSV. Please try again.")
                continue
        
        print("\nWhich database column should this match to?")
        db_col = input("Enter column name or number: ")
        
        # Try to find the column by number
        try:
            idx = int(db_col) - 1
            if 0 <= idx < len(db_columns):
                db_col = db_columns[idx]
            else:
                print(f"Invalid column number. Please enter a number between 1 and {len(db_columns)}")
                continue
        except ValueError:
            # Try to find the column by name
            if db_col not in db_columns:
                print(f"Column '{db_col}' not found in database. Please try again.")
                continue
        
        matching_columns[csv_col] = db_col
        print(f"Mapped '{csv_col}' to '{db_col}' for matching")
    
    print("\n=== STEP 2: UPDATE COLUMNS ===")
    print("Select columns to update in the database when a match is found.")
    print("You can skip this step by entering 'skip'.")
    
    update_columns = {}
    while True:
        print("\nCurrent update columns:")
        if not update_columns:
            print("  None selected yet")
        else:
            for csv_col, db_col in update_columns.items():
                print(f"  CSV: '{csv_col}' -> DB: '{db_col}'")
        
        action = input("\nEnter 'add' to add an update column, 'remove' to remove one, or 'done' when finished: ")
        
        if action.lower() == 'done':
            break
        
        elif action.lower() == 'skip':
            print("Skipping update columns selection")
            break
        
        elif action.lower() == 'add':
            csv_col = input("Enter CSV column name or number: ")
            
            # Try to find the column by number
            try:
                idx = int(csv_col) - 1
                if 0 <= idx < len(csv_columns):
                    csv_col = csv_columns[idx]
                else:
                    print(f"Invalid column number. Please enter a number between 1 and {len(csv_columns)}")
                    continue
            except ValueError:
                # Try to find the column by name
                if csv_col not in csv_columns:
                    print(f"Column '{csv_col}' not found in CSV. Please try again.")
                    continue
            
            # Skip if this column is already used for matching
            if csv_col in matching_columns:
                print(f"Column '{csv_col}' is already used for matching. Skipping.")
                continue
            
            db_col = input(f"Enter database column for '{csv_col}' (number or name): ")
            
            # Try to find the column by number
            try:
                idx = int(db_col) - 1
                if 0 <= idx < len(db_columns):
                    db_col = db_columns[idx]
                else:
                    print(f"Invalid column number. Please enter a number between 1 and {len(db_columns)}")
                    continue
            except ValueError:
                # Try to find the column by name
                if db_col not in db_columns:
                    print(f"Column '{db_col}' not found in database. Please try again.")
                    continue
            
            update_columns[csv_col] = db_col
            print(f"Mapped '{csv_col}' to '{db_col}' for updating")
        
        elif action.lower() == 'remove':
            if not update_columns:
                print("No update columns to remove")
                continue
            
            print("Current update columns:")
            for i, (csv_col, db_col) in enumerate(update_columns.items()):
                print(f"  {i+1}. CSV: '{csv_col}' -> DB: '{db_col}'")
            
            try:
                idx = int(input("Enter the number of the mapping to remove (0 to cancel): ")) - 1
                if idx == -1:
                    continue
                if 0 <= idx < len(update_columns):
                    csv_col = list(update_columns.keys())[idx]
                    del update_columns[csv_col]
                    print(f"Removed mapping for '{csv_col}'")
                else:
                    print("Invalid selection")
            except ValueError:
                print("Please enter a valid number")
    
    return matching_columns, update_columns

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

def update_song_info(spotify_id, updates):
    """
    Update song information in the database, but only for fields that don't already have values.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # First, get the current values for this song
        cursor.execute("SELECT * FROM songs WHERE spotify_id = ?", (spotify_id,))
        current_values = cursor.fetchone()
        
        if not current_values:
            logger.warning(f"No song found with ID {spotify_id}")
            return False
        
        # Get column names
        cursor.execute("PRAGMA table_info(songs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Create a dictionary of current values
        current_data = {}
        for i, col in enumerate(columns):
            current_data[col] = current_values[i]
        
        # Build the update query dynamically based on available data
        update_fields = []
        params = []
        
        for field, value in updates.items():
            # Only update if the current value is None or empty
            if value is not None and (current_data.get(field) is None or current_data.get(field) == ''):
                update_fields.append(f"{field} = ?")
                params.append(value)
                logger.debug(f"Will update {field} from empty to '{value}'")
            else:
                logger.debug(f"Skipping update for {field} as it already has a value: '{current_data.get(field)}'")
        
        if not update_fields:
            logger.info(f"No fields to update for song with ID {spotify_id} (all fields already have values)")
            return False
        
        # Add the spotify_id to the parameters
        params.append(spotify_id)
        
        # Execute the update query
        query = f"""
            UPDATE songs 
            SET {', '.join(update_fields)}
            WHERE spotify_id = ?
        """
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Updated song with ID {spotify_id}")
            return True
        else:
            logger.warning(f"No song found with ID {spotify_id}")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def process_csv_file(csv_file_path, matching_columns, update_columns):
    """
    Process the CSV file and update song information in the database.
    """
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all songs from the database
        cursor.execute("SELECT spotify_id, title, artist FROM songs")
        songs = cursor.fetchall()
        
        if not songs:
            logger.warning("No songs found in the database")
            return
        
        total_songs = len(songs)
        logger.info(f"Found {total_songs} songs in the database")
        
        # Open and read the CSV file
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            header = reader.fieldnames
            
            if not header:
                logger.error("CSV file has no headers")
                return
            
            # Log the column mappings
            logger.info("Matching columns:")
            for csv_col, db_col in matching_columns.items():
                logger.info(f"  CSV: '{csv_col}' -> DB: '{db_col}'")
            
            logger.info("Update columns:")
            for csv_col, db_col in update_columns.items():
                logger.info(f"  CSV: '{csv_col}' -> DB: '{db_col}'")
            
            # Process each row in the CSV
            updates = 0
            matches = 0
            approximate_matches = 0
            no_matches = 0
            
            for row in reader:
                # Get values for matching
                match_values = {}
                for csv_col, db_col in matching_columns.items():
                    value = row.get(csv_col, '').strip()
                    if value:
                        match_values[db_col] = value
                
                # Skip if we don't have enough values to match
                if not match_values:
                    logger.warning("Skipping row with no matching values")
                    continue
                
                # Get values for updating
                update_values = {}
                for csv_col, db_col in update_columns.items():
                    value = row.get(csv_col, '').strip()
                    if value:
                        update_values[db_col] = value
                
                # Try to find a match in the database
                match_found = False
                for spotify_id, db_title, db_artist in songs:
                    # Check for exact match
                    exact_match = True
                    for db_col, value in match_values.items():
                        db_value = None
                        if db_col == 'title':
                            db_value = db_title
                        elif db_col == 'artist':
                            db_value = db_artist
                        else:
                            # For other columns, we need to query the database
                            cursor.execute(f"SELECT {db_col} FROM songs WHERE spotify_id = ?", (spotify_id,))
                            result = cursor.fetchone()
                            if result:
                                db_value = result[0]
                        
                        if db_value is None or value.lower() != db_value.lower():
                            exact_match = False
                            break
                    
                    if exact_match:
                        logger.debug(f"Exact match found for: {match_values}")
                        match_found = True
                        matches += 1
                        
                        # Update the song information
                        if update_song_info(spotify_id, update_values):
                            updates += 1
                        break
                    
                    # Check for approximate match
                    approx_match = True
                    for db_col, value in match_values.items():
                        db_value = None
                        if db_col == 'title':
                            db_value = db_title
                        elif db_col == 'artist':
                            db_value = db_artist
                        else:
                            # For other columns, we need to query the database
                            cursor.execute(f"SELECT {db_col} FROM songs WHERE spotify_id = ?", (spotify_id,))
                            result = cursor.fetchone()
                            if result:
                                db_value = result[0]
                        
                        if db_value is None or not is_approximate_match(value, db_value):
                            approx_match = False
                            break
                    
                    if approx_match:
                        logger.debug(f"Approximate match found for: {match_values}")
                        match_found = True
                        approximate_matches += 1
                        
                        # Update the song information
                        if update_song_info(spotify_id, update_values):
                            updates += 1
                        break
                
                if not match_found:
                    logger.debug(f"No match found for: {match_values}")
                    no_matches += 1
            
            # Log summary
            logger.info(f"CSV processing complete:")
            logger.info(f"  Total rows processed: {matches + approximate_matches + no_matches}")
            logger.info(f"  Exact matches: {matches}")
            logger.info(f"  Approximate matches: {approximate_matches}")
            logger.info(f"  No matches: {no_matches}")
            logger.info(f"  Updates performed: {updates}")
    
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info(f"Processing CSV file: {args.csv_file}")
    
    # Get database schema
    db_schema = get_database_schema()
    db_columns = list(db_schema.keys())
    
    # Read CSV header
    csv_columns = read_csv_header(args.csv_file)
    
    if not csv_columns:
        logger.error("Failed to read CSV header")
        exit(1)
    
    # Default to interactive mode unless explicitly disabled
    if not args.non_interactive:
        matching_columns, update_columns = interactive_column_matching(csv_columns, db_columns)
        
        # Process the CSV file with the user-defined mappings
        process_csv_file(args.csv_file, matching_columns, update_columns)
    else:
        logger.warning("Running in non-interactive mode (not recommended)")
        
        # Try to automatically match columns
        matching_columns = {}
        update_columns = {}
        
        # Find title and artist columns for matching
        for col in csv_columns:
            col_lower = col.lower()
            if 'title' in col_lower or 'song' in col_lower or 'track' in col_lower or 'name' in col_lower:
                matching_columns[col] = 'title'
            elif 'artist' in col_lower or 'performer' in col_lower or 'singer' in col_lower or 'band' in col_lower:
                matching_columns[col] = 'artist'
        
        # Find other columns for updating
        for col in csv_columns:
            if col not in matching_columns:
                col_lower = col.lower()
                if 'album' in col_lower or 'record' in col_lower:
                    update_columns[col] = 'album'
                elif 'year' in col_lower or 'release' in col_lower or 'date' in col_lower:
                    update_columns[col] = 'release_year'
                elif 'genre' in col_lower or 'style' in col_lower or 'category' in col_lower:
                    update_columns[col] = 'genres'
        
        # Process the CSV file with the automatically determined mappings
        process_csv_file(args.csv_file, matching_columns, update_columns)
    
    logger.info("CSV processing completed") 