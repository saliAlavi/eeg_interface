import numpy as np
import soundfile as sf
import os
import pandas as pd
from scipy import signal

# Directories
INPUT_DIR = "audio_stimuli_data/pairs/"  # Change this to the actual audio directory
OUTPUT_DIR = "audio_stimuli_data/pairs/"  # Directory to save modified audio files
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the updated CSV file
df = pd.read_csv("audio_stimuli_data/trials_updated.csv")

def a_weighting_filter(sample_rate):
    """Returns A-weighting filter coefficients (IEC 61672:2003)"""
    f1, f2, f3, f4 = 20.6, 107.7, 737.9, 12194.0
    A1000 = 1.9997  # 1 kHz frequency scaling
    numerator = [(2 * np.pi * f4) ** 2 * (10 ** (A1000 / 20)), 0, 0, 0, 0]
    denominator = np.polymul([1, 4 * np.pi * f4, (2 * np.pi * f4) ** 2],
                             [1, 4 * np.pi * f1, (2 * np.pi * f1) ** 2])
    denominator = np.polymul(np.polymul(denominator, [1, 2 * np.pi * f3]), [1, 2 * np.pi * f2])
    return signal.bilinear(numerator, denominator, sample_rate)

def calculate_dba(audio_data, sample_rate):
    """Applies A-weighting and calculates dB(A) level"""
    b, a = a_weighting_filter(sample_rate)
    weighted_audio = signal.lfilter(b, a, audio_data)
    rms = np.sqrt(np.mean(weighted_audio ** 2))
    return 20 * np.log10(rms) if rms > 0 else -np.inf

def apply_gain(audio, gain_dba, sample_rate):
    """Applies a relative gain in dB(A)"""
    current_dba = calculate_dba(audio, sample_rate)
    target_dba = current_dba + gain_dba
    gain_factor = 10 ** (gain_dba / 20)
    return np.clip(audio * gain_factor, -1.0, 1.0)

def process_audio_file(filename, gain_left, gain_right):
    """Loads a FLAC file, applies gain to both channels, and saves the output."""
    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        return
    
    # Load audio
    audio_data, sample_rate = sf.read(input_path)
    
    if audio_data.shape[1] != 2:
        print(f"❌ {filename} is not a stereo file. Skipping.")
        return
    
    # Apply gain to both channels
    adjusted_left = apply_gain(audio_data[:, 0], gain_left, sample_rate)
    adjusted_right = apply_gain(audio_data[:, 1], gain_right, sample_rate)
    adjusted_audio = np.column_stack((adjusted_left, adjusted_right))
    
    # Save the modified file
    sf.write(output_path, adjusted_audio, sample_rate)
    print(f"✅ Processed and saved: {output_path}")

# Process each audio file in the CSV
for _, row in df.iterrows():
    for device in ["Device-1", "Device-2"]:
        filename = row[device]
        gain_left, gain_right = map(int, row[f"Gain_{device}"].split('_'))
        process_audio_file(filename, gain_left, gain_right)

print("🎵 All audio files processed and saved!")
