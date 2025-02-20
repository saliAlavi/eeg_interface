import os
import json
import numpy as np
import soundfile as sf

def calculate_audio_power(file_path: str) -> dict:
    # Load audio data from .flac file
    audio_data, samplerate = sf.read(file_path)
    if audio_data.ndim == 1:
        audio_data = np.column_stack((audio_data, audio_data))  # Make mono files stereo for consistency
    # Calculate the power of each channel in dB
    power_left = 10 * np.log10(np.mean(audio_data[:, 0] ** 2) + 1e-10)
    power_right = 10 * np.log10(np.mean(audio_data[:, 1] ** 2) + 1e-10)
    return {'left_channel_power_dB': power_left, 'right_channel_power_dB': power_right}

def process_directory(directory: str, output_file: str = 'audio_power.json') -> None:
    audio_powers = {}
    # Traverse the directory for .flac files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.flac'):
                file_path = os.path.join(root, file)
                try:
                    channel_ids = file.split('.')[0].split('_')
                    power = calculate_audio_power(file_path)
                    audio_powers[file] = {
                        'channel_1_id': channel_ids[0],
                        'channel_2_id': channel_ids[1],
                        'power': power
                    }
                    print(f'Processed: {file} | Power: {power}')
                except Exception as e:
                    print(f'Error processing {file}: {e}')
    # Save the results to a JSON file
    with open(output_file, 'w') as f:
        json.dump(audio_powers, f, indent=4)
    print(f'Results saved to {output_file}')


def calculate_min_max_power(json_file: str) -> None:
    with open(json_file, 'r') as f:
        data = json.load(f)
    min_power = float('inf')
    max_power = float('-inf')
    min_id = max_id = None
    for file, info in data.items():
        left_power = info['power']['left_channel_power_dB']
        right_power = info['power']['right_channel_power_dB']
        left_id = info['channel_1_id']
        right_id = info['channel_2_id']
        if left_power < min_power:
            min_power = left_power
            min_id = left_id
        if right_power < min_power:
            min_power = right_power
            min_id = right_id
        if left_power > max_power:
            max_power = left_power
            max_id = left_id
        if right_power > max_power:
            max_power = right_power
            max_id = right_id
    print(f'Minimum Power: {min_power:.4f} dB (ID: {min_id})')
    print(f'Maximum Power: {max_power:.4f} dB (ID: {max_id})')

directory = "audio_stimuli_data/pairs"
output_file = "audio_power.json"
process_directory(directory, output_file)
calculate_min_max_power(output_file)
