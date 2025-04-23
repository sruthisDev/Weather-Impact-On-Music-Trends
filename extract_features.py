import json
import os
import pandas as pd
from pathlib import Path

def extract_features(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract basic information
    filename = os.path.basename(json_file).replace('_analysis.json', '')
    
    # Extract rhythm features
    tempo = data.get('rhythm', {}).get('bpm', None)
    
    # Extract energy and dynamics
    energy = data.get('lowlevel', {}).get('average_loudness', None)
    brightness = data.get('lowlevel', {}).get('spectral_centroid', {}).get('mean', None)
    
    # Extract musical properties
    key = data.get('tonal', {}).get('key_edma', None)
    scale = data.get('tonal', {}).get('scale', None)
    
    # Extract mood/texture indicators
    dissonance = data.get('lowlevel', {}).get('dissonance', {}).get('mean', None)
    entropy = data.get('lowlevel', {}).get('spectral_entropy', {}).get('mean', None)
    
    # Extract additional features
    danceability = data.get('rhythm', {}).get('danceability', None)
    chord_strength = data.get('tonal', {}).get('chords_strength', {}).get('mean', None)
    bpm = data.get('rhythm', {}).get('bpm', None)
    
    return {
        'filename': filename,
        'tempo': tempo,
        'energy': energy,
        'brightness': brightness,
        'key': key,
        'scale': scale,
        'dissonance': dissonance,
        'entropy': entropy,
        'danceability': danceability,
        'chord_strength': chord_strength,
        'bpm': bpm
    }

def main():
    # Directory containing the analysis files
    analysis_dir = Path('essentia_output_deezer')
    
    # List to store all features
    all_features = []
    
    # Process each JSON file
    for json_file in analysis_dir.glob('*_analysis.json'):
        # Skip the combined analysis file
        if json_file.name == 'combined_analysis.json':
            continue
            
        try:
            features = extract_features(json_file)
            all_features.append(features)
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(all_features)
    df.to_csv('audio_features.csv', index=False)
    print(f"Successfully extracted features from {len(all_features)} files")

if __name__ == '__main__':
    main() 