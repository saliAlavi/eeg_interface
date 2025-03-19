import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import pandas as pd

# Load the CSV file
file_path = "audio_stimuli_data/trials.csv"
df = pd.read_csv(file_path)

# # Set target SNR globally
# target_snr_db = 20

# Function to compute gain adjustment for target SNR
def adjust_snr(signal, noise, target_snr_db):
    signal_power = np.mean(signal ** 2)
    noise_power = np.mean(noise ** 2)
    current_snr_db = 10 * np.log10(signal_power / noise_power)
    gain = 10 ** ((target_snr_db - current_snr_db) / 20)
    return gain

# Directory for processed audio
output_dir = "audio_stimuli_data/pairs/"
os.makedirs(output_dir, exist_ok=True)

# Process each trial
for index, row in df.iterrows():
    attended_speaker = row["Attended Speaker"]

    target_snr_db = row["SNR"]


    # Load all three audio files (ensuring each is saved)
    device_files = {
        "Device-1": row["Device-1"],
        "Device-2": row["Device-2"],
        "Device-3": row["Device-3"],
    }

    # Determine which file contains the attended speaker
    attended_file = None
    for key, file_name in device_files.items():
        if attended_speaker in [1, 2] and key == "Device-1":
            attended_file = file_name
        elif attended_speaker in [3, 4] and key == "Device-2":
            attended_file = file_name
        elif attended_speaker in [5, 6] and key == "Device-3":
            attended_file = file_name

    attended_channel = 0 if attended_speaker % 2 == 1 else 1  # Left for odd, Right for even
    
    if attended_file is None:
        print(f"⚠️ Skipping trial {index}: No attended file found for speaker {attended_speaker}.")
        continue

    # Load all audio files
    signals = {}
    sample_rate = None

    for key, file_name in device_files.items():
        file_path = f"audio_stimuli_data/pairs_original/{file_name}"
        if os.path.exists(file_path):
            print(f"✅ Loading: {file_path}")
            y, sr = sf.read(file_path, always_2d=True)  # Read stereo audio
            signals[key] = y.T  # Transpose to (channels, samples)
            sample_rate = sr  # Store sample rate
        else:
            print(f"❌ File Not Found: {file_path}")
            continue

    # Ensure the attended file is loaded
    if attended_file not in device_files.values():
        print(f"🚨 ERROR: Attended file missing: {attended_file}")
        continue

    # Verify stereo format before proceeding
    if signals[key].shape[0] != 2:
        print(f"🚨 ERROR: {file_name} is not stereo! Shape: {signals[key].shape}")
        continue  # Skip this trial

    # Debug: Print signal details
    print(f"🛠️ Processing Trial {index}: Attended Speaker = {attended_speaker}, File = {attended_file}, Channel = {attended_channel}")

    # Get attended signal
    attended_signal = signals[[k for k, v in device_files.items() if v == attended_file][0]][attended_channel]

    # Construct the noise by summing all unattended sources
    noise = np.zeros_like(attended_signal)
    for key, audio in signals.items():
        if device_files[key] != attended_file:
            noise += audio[0] + audio[1]  # Sum both channels for total noise

    # Compute gain for 15 dB SNR
    gain = adjust_snr(attended_signal, noise, target_snr_db)
    print(f"🎚️ Calculated Gain: {gain:.5f}")

    if np.isnan(gain) or np.isinf(gain):
        print("🚨 ERROR: Invalid Gain Calculation! Skipping Trial.")
        continue

    # Apply gain adjustment only to the attended channel
    signals[[k for k, v in device_files.items() if v == attended_file][0]][attended_channel] *= gain

    # Save all processed files (Device-1, Device-2, Device-3)
    for key, file_name in device_files.items():
        if key in signals:  # Ensure the file was successfully loaded
            output_path = os.path.join(output_dir, f"{file_name}")
            sf.write(output_path, signals[key].T, sample_rate, format='FLAC', subtype='PCM_16')
            print(f"✅ Processed and saved: {output_path}")

print("🎉 Audio processing with 15 dB SNR completed.")
