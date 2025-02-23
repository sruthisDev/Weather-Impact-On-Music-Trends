# Weather_Impact_On_Music_Trends

Overview

This project explores the relationship between weather conditions and music trends. By leveraging APIs to collect data from music streaming services and daily charts of various locations, we aim to analyze how factors like temperature, humidity, and precipitation influence music preferences. The project performs exploratory data analysis (EDA) to uncover patterns and insights.

Data Sources

Music Data: Collected from various music streaming services' APIs, focusing on top charts and trending songs in different regions.

Weather Data: Retrieved from OpenWeather API to obtain daily weather conditions for the corresponding locations of the music charts.

Features

Automated data collection from music streaming APIs.

Weather data integration using OpenWeather API.

Exploratory Data Analysis (EDA) to identify correlations between weather conditions and music trends.

Visualization of trends and patterns.

Install dependencies:

pip install -r requirements.txt

Set up API keys:

Obtain API keys from music streaming services and OpenWeather API.

Create a .env file and add:

MUSIC_API_KEY=your_music_api_key
WEATHER_API_KEY=your_weather_api_key

Usage

Run the data collection script:

python collect_data.py

Perform exploratory data analysis:

python analyze_data.py

View the generated visualizations in the output/ directory.

Contributions

Contributions are welcome! Feel free to open issues or submit pull requests.
