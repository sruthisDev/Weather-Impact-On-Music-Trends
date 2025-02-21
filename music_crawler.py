import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime
import re

# List of 35 URLs
urls = [
    "https://music.apple.com/us/playlist/top-25-new-york-city/pl.a88b5c26caea48a59484370b6f79c9df",
    "https://music.apple.com/us/playlist/top-25-los-angeles/pl.a42d6fd3917f4445b18468109d27f201",
    "https://music.apple.com/us/playlist/top-25-nashville/pl.b575f5d5635a4c64982a658f8ae5ec2a",
    "https://music.apple.com/us/playlist/top-25-austin/pl.8446e04ee80c4ff79f3631bfd9d5c405",
    "https://music.apple.com/us/playlist/top-25-san-francisco/pl.0f2ba910f3a64209933184678f99d6cd",
    "https://music.apple.com/us/playlist/top-25-accra/pl.07ee0d128ca94d1986b3f753003db642",
    "https://music.apple.com/us/playlist/top-25-auckland/pl.e263fe03552d4eb4aa790195b4bf95a5",
    "https://music.apple.com/us/playlist/top-25-bangkok/pl.59fb2f733b5f4312821f8d7d83f934e1",
    "https://music.apple.com/us/playlist/top-25-barcelona/pl.d6db0bf788df4d1c9b6059800769b473",
    "https://music.apple.com/us/playlist/top-25-bengaluru/pl.d77516976c03485186561deba65ef931",
    "https://music.apple.com/us/playlist/top-25-bogot%C3%A1/pl.da9bcdcf4bbf46b09307106ed0b053a2",
    "https://music.apple.com/us/playlist/top-25-brisbane/pl.5651c46f467049928c40ce5962628882",
    "https://music.apple.com/us/playlist/top-25-buenos-aires/pl.2c8d727a51474f14b10ca3753354a4c9",
    "https://music.apple.com/us/playlist/top-25-cape-town/pl.e9d4d8feae3e45889e0992b305d369a0",
    "https://music.apple.com/us/playlist/top-25-delhi/pl.8f35027eb4f5434691799f18390d885f",
    "https://music.apple.com/us/playlist/top-25-dubai/pl.279924c10b4d47a9babe425ee0aa01ca",
    "https://music.apple.com/us/playlist/top-25-honolulu/pl.1f48d456fa8746b8b52a7cb276f2a166",
    "https://music.apple.com/us/playlist/top-25-istanbul/pl.d083a9d82deb4057b7e4be20921f7e0a",
    "https://music.apple.com/us/playlist/top-25-jakarta/pl.7e6336e0dc274436a4403699c39ecea8",
    "https://music.apple.com/us/playlist/top-25-kyoto/pl.f716bbb2513545b4863434013f887471",
    "https://music.apple.com/us/playlist/top-25-lagos/pl.cc32def4ec1349e8ba011c9c357d40ed",
    "https://music.apple.com/us/playlist/top-25-london/pl.d50f89dc1bbe47eba03caec1fe6280db",
    "https://music.apple.com/us/playlist/top-25-melbourne/pl.9dac7c2d37d846f0a1c60cb3b9c3707b",
    "https://music.apple.com/us/playlist/top-25-mexico-city/pl.9d34e8222dd34766804d5b3e4f329f04",
    "https://music.apple.com/us/playlist/top-25-nairobi/pl.5d6f621aee9b420887ee2c5cdf0bbbeb",
    "https://music.apple.com/us/playlist/top-25-paris/pl.ab3e1b83c13744aa958ba2b334ba0e6d",
    "https://music.apple.com/us/playlist/top-25-osaka/pl.3f22ec9c90ce447d87c61762c9876726",
    "https://music.apple.com/us/playlist/top-25-rome/pl.d27acd4d4be440a1a2a5de5893765aa7",
    "https://music.apple.com/us/playlist/top-25-san-diego/pl.5f853ea66be94055a9d03637c1675a01",
    "https://music.apple.com/us/playlist/top-25-seoul/pl.d6f003a501da4b3c9d33b0c7b8cfa0ae",
    "https://music.apple.com/us/playlist/top-25-shanghai/pl.4cc86bb8172b45f4a2f4aec473176320",
    "https://music.apple.com/us/playlist/top-25-sydney/pl.3a862f5540f44d6baa96db6b2888c751",
    "https://music.apple.com/us/playlist/top-25-toronto/pl.14144d2c98604927ac05f222f8bafeb1",
    "https://music.apple.com/us/playlist/top-25-warsaw/pl.35b707db95154ba08be6bcb68772d213",
    "https://music.apple.com/us/playlist/top-25-z%C3%BCrich/pl.5c4bce317a8c4483a12c62bff03c3ba0"
]

# Create folder name as month_date
current_month = datetime.now().strftime("%m")
current_date = datetime.now().strftime("%d")
folder_name = f"{current_month}_{current_date}"
os.makedirs(folder_name, exist_ok=True)

# Configure Selenium to use Chrome in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Initialize the Chrome driver
driver = webdriver.Chrome(options=chrome_options)

# Loop through each URL
for url in urls:
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.songs-list-row"))
        )

        song_rows = driver.find_elements(By.CSS_SELECTOR, "div.songs-list-row")
        data = []

        for row in song_rows:
            song_title = row.find_element(By.CSS_SELECTOR, "div.songs-list-row__song-name").text
            artist_name = row.find_element(By.CSS_SELECTOR, "div.songs-list__col--secondary a").text
            album_name = row.find_element(By.CSS_SELECTOR, "div.songs-list__song-link-wrapper a").text
            song_duration = row.find_element(By.CSS_SELECTOR, "time.songs-list-row__length").text
            data.append([datetime.now().strftime("%Y-%m-%d"), song_title, artist_name, album_name, song_duration])

    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        continue

    city_name = re.search(r"top-25-([a-zA-Z-%]+)", url).group(1).replace("-", "_").lower()
    filename = f"{city_name}_{current_month}_{current_date}.csv"
    filename = re.sub(r'[^\w-]', '', filename)  
    filepath = os.path.join(folder_name, filename)
    df = pd.DataFrame(data, columns=["Date", "Song Title", "Artist", "Album", "Duration"])
    df.to_csv(filepath, index=False)

    print(f"Data saved to {filepath}")

driver.quit()
