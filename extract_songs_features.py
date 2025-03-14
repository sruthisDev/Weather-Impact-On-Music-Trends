import os
import pandas as pd
import sqlite3

# Directory containing CSV files
data_folder = "songs_features_data/Spotify_songs_dataset"

# List of CSV files in directory
files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]

# Standard column mapping for `songs_master_table`
column_mapping = {
    "track_id": ["track_id", "id", "track_uri", "track_href", "instance_id"],
    "track_name": ["track_name", "song", "track", "name", "Track Name"],
    "artist_name": ["artist_name", "artist(s)_name", "artists", "track_artist", "Artist"],
    "album_name": ["track_album_name", "album", "album_name"],
    "release_year": ["year", "released_year"],
    "danceability": ["danceability", "danceability_%"],
    "energy": ["energy", "energy_%"],
    "valence": ["valence", "valence_%"],
    "tempo": ["bpm", "tempo"],
    "loudness": ["loudness"],
    "speechiness": ["speechiness", "speechiness_%"],
    "instrumentalness": ["instrumentalness", "instrumentalness_%"],
    "acousticness": ["acousticness", "acousticness_%"],
    "liveness": ["liveness", "liveness_%"],
    "popularity": ["track_popularity", "popularity"],
    "streams": ["streams"],
    "explicit": ["explicit"],
    "mode": ["mode"],
    "key": ["key"],
    "spotify_url": ["spotify_url", "uri", "track_href"],
    "playlist_genre": ["playlist_genre", "playlist_name", "playlist_subgenre"]
}

# Function to standardize column names
def standardize_columns(df):
    df.columns = df.columns.str.lower().str.strip()  # Convert to lowercase & remove spaces
    df = df.loc[:, ~df.columns.duplicated()]  # Remove duplicate columns
    new_columns = {col: std_col for std_col, possible_names in column_mapping.items() for col in possible_names if col in df.columns}
    df = df.rename(columns=new_columns)
    return df

# Process CSV files
merged_data = []

for file in files:
    file_path = os.path.join(data_folder, file)
    df = pd.read_csv(file_path, encoding="ISO-8859-1", low_memory=False)
    
    df = standardize_columns(df)
    df = df.loc[:, ~df.columns.duplicated()]  # Remove duplicate columns
    df = df.reset_index(drop=True)  # Reset index
    merged_data.append(df)

# Concatenate all DataFrames
songs_master_df = pd.concat(merged_data, ignore_index=True)

# Drop duplicate column names (in case of conflicts)
songs_master_df = songs_master_df.loc[:, ~songs_master_df.columns.duplicated()]

# Connect to SQLite database
conn = sqlite3.connect("songs_master.db")
cursor = conn.cursor()

# Drop existing table if it exists to avoid conflicts
cursor.execute("DROP TABLE IF EXISTS songs_master_table")

# Create `songs_master_table`
cursor.execute("""
CREATE TABLE songs_master_table (
    track_id TEXT PRIMARY KEY,
    track_name TEXT,
    artist_name TEXT,
    album_name TEXT,
    release_year INTEGER,
    danceability REAL,
    energy REAL,
    valence REAL,
    tempo REAL,
    loudness REAL,
    speechiness REAL,
    instrumentalness REAL,
    acousticness REAL,
    liveness REAL,
    popularity INTEGER,
    streams INTEGER,
    explicit BOOLEAN,
    mode INTEGER,
    key INTEGER,
    spotify_url TEXT,
    playlist_genre TEXT
);
""")

# Insert cleaned data into SQLite
songs_master_df.to_sql("songs_master_table", conn, if_exists="replace", index=False)

# Close connection
conn.close()

print("✅ Songs master table created successfully in SQLite!")
