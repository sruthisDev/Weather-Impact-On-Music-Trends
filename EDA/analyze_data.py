import pandas as pd
import matplotlib.pyplot as plt

# Load CSV file
csv_file = "tracks.csv"  # Change to your actual file path
df = pd.read_csv(csv_file)

# Convert Duration (MM:SS) to total seconds
def duration_to_seconds(duration):
    minutes, seconds = map(int, duration.split(':'))
    return minutes * 60 + seconds

df["Duration (s)"] = df["Duration"].apply(duration_to_seconds)

# Plot Histogram of Track Durations
plt.figure(figsize=(10, 6))
plt.hist(df["Duration (s)"], bins=10, color='skyblue', edgecolor='black')
plt.xlabel("Track Length (Seconds)")
plt.ylabel("Number of Songs")
plt.title("Distribution of Track Durations")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.show()
