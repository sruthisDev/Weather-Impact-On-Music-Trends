import os
import subprocess
import json
from pathlib import Path

def process_audio_files():
    # Create output directory if it doesn't exist
    output_dir = Path("essentia_output_deezer")
    output_dir.mkdir(exist_ok=True)
    
    # Path to input files
    input_dir = Path("deezer_previews")
    
    # Combined output file
    combined_output = output_dir / "combined_analysis.json"
    
    # List to store all analysis results
    all_results = []
    
    # Process each MP3 file
    for audio_file in input_dir.glob("*.mp3"):
        print(f"Processing {audio_file.name}...")
        
        # Create output filename
        output_file = output_dir / f"{audio_file.stem}_analysis.json"
        
        # Construct Docker command
        docker_cmd = [
            "docker", "run", "-ti", "--rm",
            "-v", f"{os.getcwd()}:/essentia",
            "mtgupf/essentia",
            "essentia_streaming_extractor_music",
            f"/essentia/deezer_previews/{audio_file.name}",
            f"/essentia/essentia_output_deezer/{output_file.name}"
        ]
        
        try:
            # Run Docker command
            subprocess.run(docker_cmd, check=True)
            
            # Read the output file and append to results
            with open(output_file, 'r') as f:
                result = json.load(f)
                result['filename'] = audio_file.name
                all_results.append(result)
                
            print(f"Successfully processed {audio_file.name}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error processing {audio_file.name}: {e}")
        except Exception as e:
            print(f"Unexpected error processing {audio_file.name}: {e}")
    
    # Write combined results to file
    with open(combined_output, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nProcessing complete. Combined results saved to {combined_output}")

if __name__ == "__main__":
    process_audio_files() 