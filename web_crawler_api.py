import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re
import time
import argparse
import requests
import json

# Configuration for Selenium and API
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
api_key = "a1b3d4bc4b2f7d2e5a29a716a08028eb"

# Create folder for storing CSVs and log files
current_month = datetime.now().strftime("%m")
current_date = datetime.now().strftime("%d")
today_date = datetime.now().strftime("%Y-%m-%d")
folder_name = f"data_{current_month}_{current_date}"
os.makedirs(folder_name, exist_ok=True)

# Log file paths
music_log_file_path = os.path.join( "music_status_log.txt")
weather_log_file_path = os.path.join("weather_status_log.txt")

# Function to parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description="A script to extract the top 25 songs for various cities and save the data into CSV files. "
                    "The script reads URLs from a text file, navigates to the specified city pages, and collects "
                    "information on the songs, including titles, artists, albums, and durations."
    )
    parser.add_argument(
        "url_file", 
        nargs="?", 
        default="urls.txt", 
        help="Text file containing URLs (default: urls.txt)"
    )
    return parser.parse_args()

# Function to read URLs from a text file
def read_urls_from_txt(txt_filename):
    try:
        with open(txt_filename, 'r') as file:
            urls = file.readlines()
        return [url.strip() for url in urls]  # Return a list of URLs, stripped of extra whitespace
    except Exception as e:
        print(f"Error reading {txt_filename}: {e}")
        return []

def print_music_dashboard(status_data):
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    milliseconds = int((elapsed_time % 1) * 1000)
    elapsed_time_str = f"Duration of Script: {minutes}m {seconds}s {milliseconds}ms"
    run_time_str = "Script Run at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(music_log_file_path, 'a') as log_file:
        log_file.write(run_time_str + "\n" + elapsed_time_str + "\n")
        log_file.write(f"STATUS DASHBOARD - {today_date}\n")
        log_file.write(f"|{'-'*64}|\n")
        log_file.write(f"| {'Index':^8} | {'City':^20} | {'Songs Extracted':^15} | {'Status':^10} |\n")
        log_file.write(f"|{'-'*64}|\n")
        for idx, (city, songs) in enumerate(status_data):
            status = "Success" if songs == 25 else "Partial Success" if songs > 0 else "Failure"
            log_file.write(f"| {idx:^8} | {city:^20} | {songs:^15} | {status:^10} |\n")
        log_file.write("|" + "-"*64 + "|\n\n\n" + "~"*100 + "\n\n\n")

def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

def main():
    global start_time
    start_time = time.time()
    
    # Music part
    args = parse_args()
    urls = read_urls_from_txt(args.url_file)
    driver = webdriver.Chrome(options=chrome_options)
    dashboard = []
    for url in urls:
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.songs-list-row")))
            song_rows = driver.find_elements(By.CSS_SELECTOR, "div.songs-list-row")
            data = []
            for row in song_rows:
                try:
                    song_title = row.find_element(By.CSS_SELECTOR, "div.songs-list-row__song-name").text
                    artist_name = row.find_element(By.CSS_SELECTOR, "div.songs-list__col--secondary a").text
                    album_name = row.find_element(By.CSS_SELECTOR, "div.songs-list__song-link-wrapper a").text
                    song_duration = row.find_element(By.CSS_SELECTOR, "time.songs-list-row__length").text
                    data.append([today_date, song_title, artist_name, album_name, song_duration])
                except Exception as e:
                    print(f"Error extracting data for a song in {url}: {e}")
            city_name = re.search(r"top-25-([a-zA-Z-%]+)", url).group(1).replace("-", "_").lower()
            filename = f"{city_name}_{current_month}_{current_date}.csv"
            filepath = os.path.join(folder_name, filename)
            df = pd.DataFrame(data, columns=["Date", "Song Title", "Artist", "Album", "Duration"])
            df.to_csv(filepath, index=False)
            dashboard.append([city_name, len(data)])
        except Exception as e:
            print(f"Error processing {url}: {e}")
            dashboard.append([city_name, 0])
    driver.quit()
    print_music_dashboard(dashboard)

    # Weather part
    cities = [
     {"name": "Accra", "lat": 5.6037, "lon": -0.1870},
    {"name": "Almaty", "lat": 43.2220, "lon": 76.8512},
    {"name": "Auckland", "lat": -36.8485, "lon": 174.7633},
    {"name": "Austin", "lat": 30.2672, "lon": -97.7431},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018},
    {"name": "Barcelona", "lat": 41.3851, "lon": 2.1734},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"name": "Birmingham", "lat": 52.4862, "lon": -1.8904},
    {"name": "Bogotá", "lat": 4.7110, "lon": -74.0721},
    {"name": "Bordeaux", "lat": 44.8378, "lon": -0.5792},
    {"name": "Brisbane", "lat": -27.4698, "lon": 153.0251},
    {"name": "Budapest", "lat": 47.4979, "lon": 19.0402},
    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816},
    {"name": "Busan", "lat": 35.1796, "lon": 129.0756},
    {"name": "Calgary", "lat": 51.0447, "lon": -114.0719},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Ciudad de Mexico", "lat": 19.4326, "lon": -99.1332},
    {"name": "Cologne", "lat": 50.9375, "lon": 6.9603},
    {"name": "Copenhagen", "lat": 55.6761, "lon": 12.5683},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
    {"name": "Detroit", "lat": 42.3314, "lon": -83.0458},
    {"name": "Dubai", "lat": 25.2760, "lon": 55.2962},
    {"name": "Dublin", "lat": 53.3498, "lon": -6.2603},
    {"name": "Durban", "lat": -29.8587, "lon": 31.0218},
    {"name": "Edmonton", "lat": 53.5461, "lon": -113.4938},
    {"name": "Frankfurt", "lat": 50.1109, "lon": 8.6821},
    {"name": "Fukuoka", "lat": 33.5904, "lon": 130.4017},
    {"name": "Glasgow", "lat": 55.8642, "lon": -4.2518},
    {"name": "Guadalajara", "lat": 20.6597, "lon": -103.3496},
    {"name": "Guangzhou", "lat": 23.1291, "lon": 113.2644},
    {"name": "Guatemala City", "lat": 14.6349, "lon": -90.5069},
    {"name": "Hamburg", "lat": 53.5511, "lon": 9.9937},
    {"name": "Honolulu", "lat": 21.3069, "lon": -157.8583},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
    {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784},
    {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456},
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473},
    {"name": "Kingston", "lat": 17.9714, "lon": -76.7936},
    {"name": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869},
    {"name": "Kyiv", "lat": 50.4501, "lon": 30.5234},
    {"name": "Kyoto", "lat": 35.0116, "lon": 135.7681},
    {"name": "Lagos", "lat": 6.5244, "lon": 3.3792},
    {"name": "Lima", "lat": -12.0464, "lon": -77.0428},
    {"name": "Liverpool", "lat": 53.4084, "lon": -2.9916},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Lyon", "lat": 45.7640, "lon": 4.8357},
    {"name": "Madrid", "lat": 40.4168, "lon": -3.7038},
    {"name": "Manchester", "lat": 53.4808, "lon": -2.2426},
    {"name": "Manila", "lat": 14.5995, "lon": 120.9842},
    {"name": "Marseille", "lat": 43.2965, "lon": 5.3698},
    {"name": "Medellin", "lat": 6.2442, "lon": -75.5812},
    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
    {"name": "Milano", "lat": 45.4642, "lon": 9.1900},
    {"name": "Monterrey", "lat": 25.6866, "lon": -100.3161},
    {"name": "Montreal", "lat": 45.5017, "lon": -73.5673},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Munich", "lat": 48.1351, "lon": 11.5820},
    {"name": "Nagoya", "lat": 35.1815, "lon": 136.9066},
    {"name": "Naha", "lat": 26.2124, "lon": 127.6792},
    {"name": "Nairobi", "lat": -1.2864, "lon": 36.8172},
    {"name": "Napoli", "lat": 40.8518, "lon": 14.2681},
    {"name": "Nashville", "lat": 36.1627, "lon": -86.7816},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Osaka", "lat": 34.6937, "lon": 135.5023},
    {"name": "Ottawa", "lat": 45.4215, "lon": -75.6972},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
    {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
    {"name": "Prague", "lat": 50.0755, "lon": 14.4378},
    {"name": "Quebec City", "lat": 46.8139, "lon": -71.2082},
    {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},
    {"name": "Riyadh", "lat": 24.7136, "lon": 46.6753},
    {"name": "Rome", "lat": 41.9028, "lon": 12.4964},
    {"name": "San Diego", "lat": 32.7157, "lon": -117.1611},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "San Jose", "lat": 37.3382, "lon": -121.8863},
    {"name": "San Juan", "lat": 18.4655, "lon": -66.1057},
    {"name": "Santiago", "lat": -33.4489, "lon": -70.6693},
    {"name": "Santo Domingo", "lat": 18.4861, "lon": -69.9312},
    {"name": "Sao Paulo", "lat": -23.5505, "lon": -46.6333},
    {"name": "Sapporo", "lat": 43.0618, "lon": 141.3545},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
    {"name": "Sendai", "lat": 38.2682, "lon": 140.8694},
    {"name": "Seoul", "lat": 37.5665, "lon": 126.9780},
    {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"name": "Taipei", "lat": 25.0330, "lon": 121.5654},
    {"name": "Tel Aviv", "lat": 32.0853, "lon": 34.7818},
    {"name": "Tokyo", "lat": 35.6895, "lon": 139.6917},
    {"name": "Toronto", "lat": 43.6511, "lon": -79.3470},
    {"name": "Vancouver", "lat": 49.2827, "lon": -123.1207},
    {"name": "Vienna", "lat": 48.2082, "lon": 16.3738},
    {"name": "Warsaw", "lat": 52.2298, "lon": 21.0122},
    {"name": "Washington DC", "lat": 38.9072, "lon": -77.0369},
    {"name": "Winnipeg", "lat": 49.8951, "lon": -97.1384},
    {"name": "Zurich", "lat": 47.3769, "lon": 8.5417}
]

    structured_weather_data = []
    status_dashboard = []
    for index, city in enumerate(cities):
        name = city["name"].lower().replace(" ", "_")
        lat = city["lat"]
        lon = city["lon"]
        weather_data = get_weather(lat, lon)
        if weather_data.get("main"):
            structured_weather_data.append({
                "City": name,
                "Temperature (°C)": weather_data["main"].get("temp", "N/A"),
                "Feels Like (°C)": weather_data["main"].get("feels_like", "N/A"),
                "Weather": weather_data["weather"][0].get("main", "N/A"),
                "Description": weather_data["weather"][0].get("description", "N/A"),
                "Humidity (%)": weather_data["main"].get("humidity", "N/A"),
                "Pressure (hPa)": weather_data["main"].get("pressure", "N/A"),
                "Wind Speed (m/s)": weather_data["wind"].get("speed", "N/A")
            })
            status_dashboard.append(f"| {index:<8} | {name:<20} | {len(weather_data):<20} | {'Success':<10} |")
        else:
            status_dashboard.append(f"| {index:<8} | {name:<20} | {0:<20} | {'Failure':<10} |")
    output_file = os.path.join(folder_name, f"weather_{today_date.replace('-', '_')}.csv")
    df = pd.DataFrame(structured_weather_data)
    df.to_csv(output_file, index=False, sep=',')
    with open(weather_log_file_path, "a") as log:
        log.write("\n" + "~" * 100 + "\n")
        log.write("\nScript Run at: " + str(datetime.now()) + "\n")
        log.write("STATUS DASHBOARD\n")
        log.write("|  Index   |         City         | Attributes Extracted |   Status   |\n")
        log.write("|----------------------------------------------------------------|\n")
        for status in status_dashboard:
            log.write(status + "\n")
        log.write("|----------------------------------------------------------------|\n")
        log.write("~" * 100 + "\n")

if __name__ == "__main__":
    main()