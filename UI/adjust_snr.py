import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import pandas as pd

# Load the CSV file
file_path = "audio_stimuli_data/trials_with_audio_power.csv"
new_file_path = "audio_stimuli_data/trials_with_audio_power_new.csv"
df = pd.read_csv(file_path)

# Function to compute gain adjustment for target SNR
def adjust_snr(signal_power, noise_power, target_snr_db):
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

    device_files = {
        "Device-1": row["Device-1"],
        "Device-2": row["Device-2"],
        "Device-3": row["Device-3"],
    }

    attended_file = None
    for key, file_name in device_files.items():
        if attended_speaker in [1, 2] and key == "Device-1":
            attended_file = file_name
        elif attended_speaker in [3, 4] and key == "Device-2":
            attended_file = file_name
        elif attended_speaker in [5, 6] and key == "Device-3":
            attended_file = file_name

    attended_channel = 0 if attended_speaker % 2 == 1 else 1

    if attended_file is None:
        print(f"⚠️ Skipping trial {index}: No attended file found for speaker {attended_speaker}.")
        continue

    signals = {}
    sample_rate = None

    # Load audio files
    for key, file_name in device_files.items():
        file_path = f"audio_stimuli_data/pairs_original/{file_name}"
        if os.path.exists(file_path):
            print(f"✅ Loading: {file_path}")
            y, sr = sf.read(file_path, always_2d=True)
            signals[key] = y.T
            sample_rate = sr
        else:
            print(f"❌ File Not Found: {file_path}")
            continue

    # Check stereo format
    for key, audio in signals.items():
        if audio.shape[0] != 2:
            print(f"🚨 ERROR: {device_files[key]} is not stereo! Shape: {audio.shape}")
            continue

    # Identify attended signal
    attended_key = [k for k, v in device_files.items() if v == attended_file][0]
    attended_signal = signals[attended_key][attended_channel]

    # Calculate signal power
    signal_power = np.mean(attended_signal ** 2)

    # Calculate total noise power from unattended channels
    total_noise_power = 0
    for key, audio in signals.items():
        if key != attended_key:
            total_noise_power += np.mean(audio[0] ** 2) + np.mean(audio[1] ** 2)

    # Compute gain adjustment for target SNR
    gain = adjust_snr(signal_power, total_noise_power, target_snr_db)
    print(f"🎚️ Trial {index} | Gain: {gain:.5f}")

    if np.isnan(gain) or np.isinf(gain):
        print("🚨 ERROR: Invalid Gain Calculation! Skipping Trial.")
        continue

    # Apply gain only to attended channel
    signals[attended_key][attended_channel] *= gain

    # Update power values in DataFrame after applying gain
    for key, audio in signals.items():
        df.at[index, f"{key} Left Power"] = np.mean(audio[0] ** 2)
        df.at[index, f"{key} Right Power"] = np.mean(audio[1] ** 2)

    # Save processed files
    for key, file_name in device_files.items():
        if key in signals:
            output_path = os.path.join(output_dir, file_name)
            sf.write(output_path, signals[key].T, sample_rate, format='FLAC', subtype='PCM_16')
            print(f"✅ Saved: {output_path}")

# Save updated CSV with new power values
df.to_csv(new_file_path, index=False)

print("🎉 Audio processing and power update completed successfully.")