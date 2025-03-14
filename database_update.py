import sqlite3
import csv
import os
import re
from datetime import datetime

DB_FILE = "music_weather.db"

con = sqlite3.connect(DB_FILE)
cursor = con.cursor()

data_base_folder = "Data"

weatherFileNamePrefix = "weather_"

current_year = datetime.now().year

def CreateSongTable():
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS songs (
			song_id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT NOT NULL,
			artist TEXT NOT NULL,
			album TEXT,
			duration_sec INTEGER,
			danceability FLOAT,
			bpm INTEGER,
			energy FLOAT,
			valence FLOAT,
			spotify_id TEXT UNIQUE)
		""")

def CreateChartsTable():
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS charts (
			song_id INTEGER NOT NULL,
			city TEXT NOT NULL,
			date TEXT NOT NULL,
			rank INTEGER NOT NULL,
			PRIMARY KEY (city, date, rank))
		""")

def CreateWeatherTable():
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

def CreateTables():
	CreateSongTable()
	CreateChartsTable()
	CreateWeatherTable()

# Function to Insert Weather Data
def insertWeather(city, date, temperature, weather, weather_condition, humidity, pressure, wind_speed, precipitation):
    try:
        cursor.execute("""
            SELECT COUNT(1) FROM weather WHERE city = ? AND date = ?
        """, (city, date))
        
        if cursor.fetchone()[0] == 0:  # If no data exists, insert new data
            cursor.execute("""
                INSERT INTO weather (city, date, temperature, weather, weatherCondition, humidity, pressure, wind_speed, precipitation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (city, date, temperature, weather, weather_condition, humidity, pressure, wind_speed, precipitation))
            print(f"Weather data for {city} on {date} inserted.")
        else:
            print(f"Weather data for {city} on {date} already exists.")
    except sqlite3.Error as e:
        print(f"Error inserting weather data for {city} on {date}: {e}")

# Function to Parse Weather CSV and Insert Data
def parseWeatherCSV(file_path, dateString):
    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} was not found.")
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
                    print(f"Error processing row for {row['City']} on {row['Date']}: {e}")
                    
    except Exception as e:
        print(f"Error reading the file {file_path}: {e}")


def PopulateWeather():
	
	for folder_name in os.listdir(data_base_folder):
		folder_path = os.path.join(data_base_folder, folder_name)

		if(os.path.isdir(folder_path)):
			print(f"Processing folder: {folder_name}")

			month, day = folder_name.split('_')[1], folder_name.split('_')[2]
			dateString = str(current_year) + "-" + month + "-" + day
			weatherFileName = weatherFileNamePrefix + str(current_year) + "_" + month + "_" + day + ".csv"
			weatherFilePath = os.path.join(folder_path, weatherFileName)

			parseWeatherCSV(weatherFilePath, dateString)

def insertChart(city, date, songTitle, rank):
    try:
        # Retrieve the song_id based on the title
        cursor.execute("SELECT song_id FROM songs WHERE title = ?", (songTitle,))
        result = cursor.fetchone()
        
        if result is None:
            print(f"Error: Song '{songTitle}' not found in the songs table.")
            return  # Skip inserting this entry since song_id is missing
        
        song_id = result[0]  # Extract song_id from the query result

        # Check if the chart entry already exists
        cursor.execute("""
            SELECT COUNT(1) FROM charts WHERE city = ? AND date = ? AND rank = ?
        """, (city, date, rank))

        if cursor.fetchone()[0] == 0:  # If no entry exists, insert new ranking
            cursor.execute("""
                INSERT INTO charts (song_id, city, date, rank)
                VALUES (?, ?, ?, ?)
            """, (song_id, city, date, rank))
            print(f"Chart entry for {songTitle} in {city} on {date} ranked {rank} inserted.")
        else:
            print(f"Chart entry for {songTitle} in {city} on {date} already exists.")

    except sqlite3.Error as e:
        print(f"Error inserting chart entry for {songTitle} in {city} on {date}: {e}")

def insertSong(title, artist, album, duration):
    try:
        cursor.execute("""
            SELECT COUNT(1) FROM songs WHERE spotify_id = ?
        """, (title,))  # We use song title or spotify_id to check for duplicates

        if cursor.fetchone()[0] == 0:  # If no data exists, insert new song data
            cursor.execute("""
                INSERT INTO songs (title, artist, album, duration_sec)
                VALUES (?, ?, ?, ?)
            """, (title, artist, album, duration))
            print(f"Song '{title}' by {artist} inserted.")
        else:
            print(f"Song '{title}' by {artist} already exists.")
    except sqlite3.Error as e:
        print(f"Error inserting song '{title}' by {artist}: {e}")

def parseChartCsv(file_path, dateString, cityName):
    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} was not found.")
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
                            print(f"Error: Invalid duration format for song {songTitle}. Skipping.")
                            duration = None
                    else:
                        duration = None

                    insertSong(songTitle, artist, album, duration)
                    insertChart(cityName, dateString, songTitle, rank)

                    rank += 1  # Incrementing rank for the next song
                except Exception as e:
                    print(f"Error processing row: {e}")

    except Exception as e:
        print(f"Error reading the file {file_path}: {e}")


def PopulateCharts():

	for folder_name in os.listdir(data_base_folder):
		folder_path = os.path.join(data_base_folder, folder_name)

		if(os.path.isdir(folder_path)):
			print(f"Processing folder: {folder_name}")

		month, day = folder_name.split('_')[1], folder_name.split('_')[2]

		for fileName in os.listdir(folder_path):
			
			if not fileName.startswith("weather"):

				print (f"Processing fileName: {fileName}")

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
				    	assert False, "Issue with fileName and folder"

				    print(f"City: {cityName}, Date: {date}")
				else:
				    print("Filename does not match expected format.")


def PopulateData():
	PopulateWeather()
	PopulateCharts()


if __name__ == "__main__":
	CreateTables()
	PopulateData()
	con.commit()
	con.close()