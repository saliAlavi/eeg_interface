import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy import signal

# Fixed Parameters
INPUT_FILE = "C:/Codes/eeg_interface_naimul/eeg_interface/UI/audio_stimuli_data/pairs/98_1046.flac"
GAIN_DBA = 2  # Instead of target dBA, we now specify gain
CHANNEL = "right"  # Change to "left" if needed
DEVICE_INDEX = 3  # Set the desired audio output device index
NOISE_FLOOR_DB = -50  # Avoid amplifying low-level noise

def a_weighting_filter(sample_rate):
    """Returns A-weighting filter coefficients (IEC 61672:2003)"""
    f1 = 20.6
    f2 = 107.7
    f3 = 737.9
    f4 = 12194.0

    A1000 = 1.9997  # 1 kHz frequency scaling
    numerator = [(2 * np.pi * f4) ** 2 * (10 ** (A1000 / 20)), 0, 0, 0, 0]
    denominator = np.polymul([1, 4 * np.pi * f4, (2 * np.pi * f4) ** 2],
                             [1, 4 * np.pi * f1, (2 * np.pi * f1) ** 2])
    denominator = np.polymul(np.polymul(denominator,
                                        [1, 2 * np.pi * f3]),
                             [1, 2 * np.pi * f2])

    # Convert to digital filter using bilinear transformation
    b, a = signal.bilinear(numerator, denominator, sample_rate)
    return b, a

def calculate_dba(audio_data, sample_rate):
    """Applies A-weighting and calculates dB(A) level"""
    b, a = a_weighting_filter(sample_rate)
    weighted_audio = signal.lfilter(b, a, audio_data)
    rms = np.sqrt(np.mean(weighted_audio ** 2))
    dba_level = 20 * np.log10(rms) if rms > 0 else -np.inf
    return dba_level

def apply_gain(audio, gain_dba, sample_rate):
    """Applies a relative gain in dB(A) instead of setting a fixed target dB(A)"""
    current_dba = calculate_dba(audio, sample_rate)
    target_dba = current_dba + gain_dba  # Apply relative gain

    if current_dba < NOISE_FLOOR_DB:
        print("⚠️ Audio is too quiet; preventing unnecessary noise amplification.")
        return audio  # Avoid amplifying low-level noise

    gain_factor = 10 ** (gain_dba / 20)
    adjusted_audio = audio * gain_factor

    # Apply soft limiting to prevent clipping
    return np.clip(adjusted_audio, -1.0, 1.0)

def adjust_and_silence_channel(input_file, gain_dba, channel="left"):
    """Load FLAC file, apply gain to one channel, silence the other"""
    # Load FLAC file
    audio_data, sample_rate = sf.read(input_file)

    if audio_data.shape[1] != 2:
        raise ValueError("The input file must be a stereo (two-channel) FLAC file.")

    # Split left and right channels
    left_channel = audio_data[:, 0]
    right_channel = audio_data[:, 1]

    # Select the channel to adjust and silence the other
    if channel == "left":
        target_channel = left_channel
        silent_channel = np.zeros_like(right_channel)  # Silence the right channel
    else:
        target_channel = right_channel
        silent_channel = np.zeros_like(left_channel)  # Silence the left channel

    # Apply relative gain
    adjusted_channel = apply_gain(target_channel, gain_dba, sample_rate)

    # Merge channels back
    if channel == "left":
        final_audio = np.column_stack((adjusted_channel, silent_channel))
    else:
        final_audio = np.column_stack((silent_channel, adjusted_channel))

    print(f"Applied {gain_dba} dB(A) gain to {channel} channel (Original: {calculate_dba(target_channel, sample_rate):.2f} dB(A), New: {calculate_dba(adjusted_channel, sample_rate):.2f} dB(A)) and silenced the other.")
    return final_audio, sample_rate

def play_audio(audio_data, sample_rate, device_index):
    """Play modified audio on a specific device"""
    print(f"Playing on device index: {device_index}")
    
    # Play the sound on the selected device
    sd.play(audio_data, samplerate=sample_rate, device=device_index)
    sd.wait()

def list_audio_devices():
    """List available audio devices"""
    print(sd.query_devices())

if __name__ == "__main__":
    print("Processing audio file...")

    # Adjust and silence the channel
    modified_audio, sample_rate = adjust_and_silence_channel(INPUT_FILE, GAIN_DBA, CHANNEL)

    # Play the modified audio on the selected device
    play_audio(modified_audio, sample_rate, DEVICE_INDEX)