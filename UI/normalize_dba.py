import numpy as np
import soundfile as sf
import os
import shutil
from scipy import signal

# 📂 Input & Output Directories
INPUT_DIR = "C:/Codes/eeg_interface_naimul/eeg_interface/UI/audio_stimuli_data/pairs_original/"  # Change this
OUTPUT_DIR = "C:/Codes/eeg_interface_naimul/eeg_interface/UI/audio_stimuli_data/pairs/"  # Change this
NOISE_FLOOR_DB = -50  # Prevents boosting low-level noise

def a_weighting_filter(sample_rate):
    """Returns A-weighting filter coefficients (IEC 61672:2003)"""
    f1, f2, f3, f4 = 20.6, 107.7, 737.9, 12194.0
    A1000 = 1.9997  # 1 kHz reference scaling
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

def find_min_dba(input_dir):
    """Finds the minimum dB(A) across non-"noise" files"""
    min_dba = float("inf")

    for file in os.listdir(input_dir):
        if file.endswith(".flac") and "noise" not in file.lower():  # Exclude "noise" files
            file_path = os.path.join(input_dir, file)
            audio_data, sample_rate = sf.read(file_path)

            if audio_data.shape[1] != 2:
                continue  # Skip non-stereo files

            left_dba = calculate_dba(audio_data[:, 0], sample_rate)
            right_dba = calculate_dba(audio_data[:, 1], sample_rate)
            file_min_dba = min(left_dba, right_dba)

            print(f"📄 File: {file}, Left dB(A): {left_dba:.2f}, Right dB(A): {right_dba:.2f}, Min dB(A): {file_min_dba:.2f}")
            min_dba = min(min_dba, file_min_dba)

    return min_dba if min_dba != float("inf") else None  # Return None if no valid files found

def apply_gain(audio, target_dba, sample_rate):
    """Applies gain to match the target dB(A)"""
    current_dba = calculate_dba(audio, sample_rate)
    gain_db = target_dba - current_dba

    if current_dba < NOISE_FLOOR_DB:
        print("⚠️ Audio is too quiet; preventing unnecessary noise amplification.")
        return audio  # Avoid boosting noise

    gain_factor = 10 ** (gain_db / 20)
    adjusted_audio = np.clip(audio * gain_factor, -1.0, 1.0)
    return adjusted_audio

def process_files(input_dir, output_dir, target_dba):
    """Processes valid FLAC files, adjusts dB(A) for non-"noise" files, and copies or adjusts "noise" files"""
    os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist

    for file in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir, file)

        if file.endswith(".flac"):
            audio_data, sample_rate = sf.read(file_path)

            if audio_data.shape[1] != 2:
                print(f"⏩ Skipping {file}: Not a stereo file")
                continue

            left_dba = calculate_dba(audio_data[:, 0], sample_rate)
            right_dba = calculate_dba(audio_data[:, 1], sample_rate)
            file_max_dba = max(left_dba, right_dba)

            if "noise" in file.lower():
                # If "noise" file has dB(A) > min regular dB(A), adjust it
                if file_max_dba > target_dba:
                    print(f"⚠️ Adjusting {file} (Noise dB(A): {file_max_dba:.2f} > Min Regular dB(A): {target_dba:.2f})")

                    adjusted_left = apply_gain(audio_data[:, 0], target_dba, sample_rate)
                    adjusted_right = apply_gain(audio_data[:, 1], target_dba, sample_rate)
                    adjusted_audio = np.column_stack((adjusted_left, adjusted_right))

                    sf.write(output_path, adjusted_audio, sample_rate)
                    print(f"✅ Adjusted Noise File: {file}")
                else:
                    shutil.copy2(file_path, output_path)
                    print(f"📂 Copied {file} (Unchanged, dB(A) <= Min Regular dB(A))")

            else:
                # Adjust non-"noise" files
                adjusted_left = apply_gain(audio_data[:, 0], target_dba, sample_rate)
                adjusted_right = apply_gain(audio_data[:, 1], target_dba, sample_rate)
                adjusted_audio = np.column_stack((adjusted_left, adjusted_right))

                sf.write(output_path, adjusted_audio, sample_rate)
                print(f"✅ Adjusted {file}")

if __name__ == "__main__":
    print("🔍 Finding minimum dB(A) value across valid files (excluding 'noise' files)...")
    min_dba = find_min_dba(INPUT_DIR)

    if min_dba is None:
        print("❌ No valid FLAC files found. Exiting.")
    else:
        print(f"✅ Minimum dB(A) found: {min_dba:.2f}. Adjusting all files to match this level.")
        process_files(INPUT_DIR, OUTPUT_DIR, min_dba)
        print("🎵 Processing complete! All files saved with adjusted dB(A).")
