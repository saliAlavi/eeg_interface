from pydub import AudioSegment
import os

# Set the input and output directories
input_directory = "audio_stimuli_data/pairs"
output_directory = "audio_stimuli_data/pairs_new"

# Make sure output directory exists
os.makedirs(output_directory, exist_ok=True)

# Define target duration (30 seconds)
target_duration_ms = 30 * 1000  # 30 seconds in milliseconds

# Process each .flac file in the input directory
for filename in os.listdir(input_directory):
    if filename.endswith(".flac"):
        # Load the audio file
        input_path = os.path.join(input_directory, filename)
        print(input_path)
        audio = AudioSegment.from_file(input_path, format="flac")

        # Adjust the audio length
        if len(audio) < target_duration_ms:
            # Pad with silence if the audio is shorter than 30 seconds
            padding = AudioSegment.silent(duration=target_duration_ms - len(audio))
            audio = audio + padding
        else:
            # Trim the audio if it's longer than 30 seconds
            audio = audio[:target_duration_ms]

        # Export the processed audio file
        output_path = os.path.join(output_directory, filename)
        audio.export(output_path, format="flac")
        print(f"Processed {filename}")
