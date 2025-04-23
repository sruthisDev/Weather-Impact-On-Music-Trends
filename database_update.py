import sqlite3
import csv
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import requests
import base64
import logging
import argparse
from logger_config import get_script_logger

# Parse command line arguments
parser = argparse.ArgumentParser(description='Update database with weather and music data')
parser.add_argument('--log-level', 
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='WARNING',
                    help='Set the logging level (default: WARNING)')
args = parser.parse_args()

# Convert string log level to logging constant
log_level = getattr(logging, args.log_level)

# Set up logger
logger = get_script_logger('database_update', level=log_level)

DB_FILE = "music_weather.db"

con = sqlite3.connect(DB_FILE)
cursor = con.cursor()

data_base_folder = "Data"

weatherFileNamePrefix = "weather_"

current_year = datetime.now().year



def CreateSongTable():
    """
    Creates the 'songs' table in the SQLite database if it does not already exist.
    """
    cursor.execute("""
		CREATE TABLE IF NOT EXISTS songs (
			spotify_id TEXT UNIQUE PRIMARY KEY,
			title TEXT NOT NULL,
			artist TEXT NOT NULL,
			album TEXT,
			duration_sec INTEGER,
			danceability FLOAT,
			bpm INTEGER,
			energy FLOAT,
			valence FLOAT)
		""")
    logger.info("Songs table created or already exists")



def CreateChartsTable():
	"""
    Creates the 'charts' table in the SQLite database if it does not already exist.
    The table includes columns for song ranking in a specific city and date, with references to the song's Spotify ID.
    """
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS charts (
			spotify_id TEXT NOT NULL,
			city TEXT NOT NULL,
			date TEXT NOT NULL,
			rank INTEGER NOT NULL,
			PRIMARY KEY (city, date, rank))
		""")
    logger.info("Charts table created or already exists")



def CreateWeatherTable():
	"""
    Creates the 'weather' table in the SQLite database if it does not already exist.
    """
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS weather(
			weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
			city TEXT NOT NULL,
			date DATE NOT NULL,
			temperature REAL NOT NULL,
			weather TEXT NOT NULL,
			weatherCondition TEXT NOT NULL,
			humidity REAL NOT NULL,
			pressure REAL,
			wind_speed REAL,
			precipitation REAL,
			UNIQUE(city,date)
			)
		""")
    logger.info("Weather table created or already exists")


def CreateTables():
	"""
    Calls the individual table creation functions to create 'songs', 'charts', and 'weather' tables in the database.
    """
	CreateSongTable()
	CreateChartsTable()
	CreateWeatherTable()
    logger.info("All tables created successfully")


def getTrackID(song_name, artist_name):
    """
    Retrieves the Spotify ID of a song based on the song's name and artist using Spotify's API.
    """
    # Load environment variables
    load_dotenv()
    
    # Get client_id and client_secret from environment variables
    client_id = os.getenv("MUSIC_CLIENT_ID")
    client_secret = os.getenv("MUSIC_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.error("Missing client ID or client secret in .env file")
        raise Exception("Missing client ID or client secret in .env file")
    
    # Obtain access token
    auth_url = "https://accounts.spotify.com/api/token"
    auth_headers = {
        "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
    }
    auth_data = {"grant_type": "client_credentials"}
    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)
    access_token = auth_response.json().get("access_token")
    
    if not access_token:
        logger.error("Failed to obtain access token")
        raise Exception("Failed to obtain access token")
    
    # Search for track
    query = f"track:{song_name} artist:{artist_name}"
    search_url = f"https://api.spotify.com/v1/search?q={requests.utils.quote(query)}&type=track&limit=1"
    search_headers = {"Authorization": f"Bearer {access_token}"}
    search_response = requests.get(search_url, headers=search_headers)
    data = search_response.json()
    
    results = data.get("tracks", {}).get("items", [])
    if results:
        logger.debug(f"Found Spotify ID for '{song_name}' by '{artist_name}': {results[0]['id']}")
        return results[0]["id"]
    else:
        logger.warning(f"No Spotify ID found for '{song_name}' by '{artist_name}'")
        return None


def insertWeather(city, date, temperature, weather, weather_condition, humidity, pressure, wind_speed, precipitation):
    """
    Inserts weather data into the 'weather' table for a specific city and date.
    Ensures that duplicate entries for the same city and date are avoided.
    """
    try:
        cursor.execute("""
            SELECT COUNT(1) FROM weather WHERE city = ? AND date = ?
        """, (city, date))
        
        if cursor.fetchone()[0] == 0:  # If no data exists, insert new data
            cursor.execute("""
                INSERT INTO weather (city, date, temperature, weather, weatherCondition, humidity, pressure, wind_speed, precipitation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (city, date, temperature, weather, weather_condition, humidity, pressure, wind_speed, precipitation))
            logger.info(f"Weather data for {city} on {date} inserted")
        else:
            logger.debug(f"Weather data for {city} on {date} already exists")
    except sqlite3.Error as e:
        logger.error(f"Error inserting weather data for {city} on {date}: {e}")



# Function to Parse Weather CSV and Insert Data
def parseWeatherCSV(file_path, dateString):
    """
    Parses a weather CSV file and inserts weather data into the database.
    """
    if not os.path.exists(file_path):
        logger.error(f"Error: The file {file_path} was not found")
        return  # Exit the function if the file doesn't exist
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    # Generalize the approach: Check each field and handle missing ones

                    # Map the CSV fields to the expected columns
                    city = row['City']  # Map 'City' directly
                    date = dateString  # Assuming the date is correctly formatted
                    temperature = float(row['Temperature (°C)']) if 'Temperature (°C)' in row else None
                    weather = row['Weather'] if 'Weather' in row else None
                    weather_condition = row['Description'] if 'Description' in row else None
                    humidity = float(row['Humidity (%)']) if 'Humidity (%)' in row else None
                    pressure = float(row['Pressure (hPa)']) if 'Pressure (hPa)' in row else None
                    wind_speed = float(row['Wind Speed (m/s)']) if 'Wind Speed (m/s)' in row else None
                    precipitation = float(row['precipitation']) if 'precipitation' in row else None

                    # Insert weather data into the table
                    insertWeather(
                        city, date, 
                        temperature, weather, weather_condition,
                        humidity, pressure, wind_speed, 
                        precipitation
                    )
                except Exception as e:
                    logger.error(f"Error processing row for {row['City']} on {row['Date']}: {e}")
                    
    except Exception as e:
        logger.error(f"Error reading the file {file_path}: {e}")



def PopulateWeather():
	"""
    Populates the 'weather' table by processing weather data files stored in the 'Data' folder.
    Iterates through each folder and CSV file in the directory, parsing and inserting weather data for each city and date.
    """
	for folder_name in os.listdir(data_base_folder):
		folder_path = os.path.join(data_base_folder, folder_name)

		if(os.path.isdir(folder_path)):
			logger.info(f"Processing folder: {folder_name}")

			month, day = folder_name.split('_')[1], folder_name.split('_')[2]
			dateString = str(current_year) + "-" + month + "-" + day
			weatherFileName = weatherFileNamePrefix + str(current_year) + "_" + month + "_" + day + ".csv"
			weatherFilePath = os.path.join(folder_path, weatherFileName)

			parseWeatherCSV(weatherFilePath, dateString)


def insertChart(spotify_id, city, date, songTitle, rank):
    """
    Inserts a song's chart ranking into the 'charts' table for a specific city and date.
    Ensures that duplicate chart entries for the same city, date, and rank are avoided.
    """
    try:
        # Retrieve the song_id based on the spotify_id
        cursor.execute("SELECT spotify_id FROM songs WHERE spotify_id = ?", (spotify_id,))
        result = cursor.fetchone()
        
        if result is None:
            logger.error(f"Error: Song with spotify_id '{spotify_id}' not found in the songs table")
            return 
        
        spotify_id = result[0]  # Extract song_id from the query result

        # Check if the chart entry already exists
        cursor.execute("""
            SELECT COUNT(1) FROM charts WHERE city = ? AND date = ? AND rank = ?
        """, (city, date, rank))

        if cursor.fetchone()[0] == 0:  # If no entry exists, insert new ranking
            cursor.execute("""
                INSERT INTO charts (spotify_id, city, date, rank)
                VALUES (?, ?, ?, ?)
            """, (spotify_id, city, date, rank))
            logger.info(f"Chart entry for {songTitle} in {city} on {date} ranked {rank} inserted")
        else:
            logger.debug(f"Chart entry for {songTitle} in {city} on {date} already exists")
    except sqlite3.Error as e:
        logger.error(f"Error inserting chart entry for {songTitle} in {city} on {date}: {e}")


def insertSong(spotify_id, title, artist, album, duration):
    """
    Inserts a song's details into the 'songs' table. Ensures that duplicate songs (based on Spotify ID) are avoided.
    """
    try:
        # Check for duplicates using spotify_id
        cursor.execute("""
            SELECT COUNT(1) FROM songs WHERE spotify_id = ?
        """, (spotify_id,))

        if cursor.fetchone()[0] == 0:  # If no data exists, insert new song data
            cursor.execute("""
                INSERT INTO songs (spotify_id, title, artist, album, duration_sec)
                VALUES (?, ?, ?, ?, ?)
            """, (spotify_id, title, artist, album, duration))
            logger.info(f"Song '{title}' by {artist} inserted")
        else:
            logger.debug(f"Song '{title}' by {artist} already exists")
    except sqlite3.Error as e:
        logger.error(f"Error inserting song '{title}' by {artist}: {e}")



def parseChartCsv(file_path, dateString, cityName):
    """
    Parses a chart CSV file and inserts chart ranking data for songs into the database.
    """
    if not os.path.exists(file_path):
        logger.error(f"Error: The file {file_path} was not found")
        return  # Exit the function if the file doesn't exist

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            rank = 1
            for row in reader:
                try:
                    city = cityName
                    date = dateString
                    songTitle = row['Song Title']
                    artist = row.get('Artist', None)
                    album = row.get('Album', None)

                    duration_str = row.get('Duration', None)
                    if duration_str:
                        try:
                            minutes, seconds = map(int, duration_str.split(':'))
                            duration = (minutes * 60) + seconds
                        except ValueError:
                            logger.error(f"Error: Invalid duration format for song {songTitle}. Skipping.")
                            duration = None
                    else:
                        duration = None

                    spotify_id = getTrackID(songTitle, artist)
                    if spotify_id:
                        insertSong(spotify_id, songTitle, artist, album, duration)
                        insertChart(spotify_id, cityName, dateString, songTitle, rank)

                    rank += 1  # Incrementing rank for the next song
                except Exception as e:
                    logger.error(f"Error processing row: {e}")

    except Exception as e:
        logger.error(f"Error reading the file {file_path}: {e}")

def PopulateCharts():
	"""
    Populates the 'charts' table by processing chart ranking data files stored in the 'Data' folder.
    Iterates through each folder and CSV file in the directory, parsing and inserting chart data for each city and date.
    """
	for folder_name in os.listdir(data_base_folder):
		folder_path = os.path.join(data_base_folder, folder_name)

		if(os.path.isdir(folder_path)):
			logger.info(f"Processing folder: {folder_name}")

		month, day = folder_name.split('_')[1], folder_name.split('_')[2]

		for fileName in os.listdir(folder_path):
			
			if not fileName.startswith("weather"):

				logger.info(f"Processing fileName: {fileName}")

				pattern = r"^([a-zA-Z_]+(?:_[a-zA-Z_]+)*)_(\d{2})_(\d{2})\.csv$"

				match = re.match(pattern, fileName)

				if match:
				    cityName = match.group(1)  # Add check that city is valid
				    date = f"{match.group(2)}_{match.group(3)}" 

				    if month == match.group(2) and day == match.group(3):
				    	filePath = os.path.join(folder_path, fileName)
				    	dateString = str(current_year) + "-" + month + "-" + day
				    	parseChartCsv(filePath, dateString, cityName)
				    
				    else:
				    	logger.error("Issue with fileName and folder")
				    	assert False, "Issue with fileName and folder"

				    logger.debug(f"City: {cityName}, Date: {date}")
				else:
				    logger.warning("Filename does not match expected format")


def PopulateData():
	"""
    Populates the database with both weather and chart data by calling the PopulateWeather() and PopulateCharts() functions.
    """
	PopulateWeather()
	PopulateCharts()
    logger.info("Data population completed")


if __name__ == "__main__":
	CreateTables()
	PopulateData()
	con.commit()
	con.close()
    logger.info("Database update completed successfully")