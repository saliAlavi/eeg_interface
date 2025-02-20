import numpy as np
import soundfile as sf

# 🎯 Parameters
duration = 10  # seconds
sample_rate = 48000  # Hz
target_power_db = -10  # Desired power level in dBFS

# 🎵 Generate White Noise
white_noise = np.random.normal(0, 1, int(duration * sample_rate))

# 🔥 Convert dBFS to Linear Power
target_power_linear = 10 ** (target_power_db / 10)

# 🎚️ Normalize to Desired Power
current_power = np.mean(white_noise ** 2)
scaling_factor = np.sqrt(target_power_linear / current_power)
broadband_noise = white_noise * scaling_factor

# 💾 Save as a WAV File for Playback
sf.write('broadband_noise_dbfs.wav', broadband_noise, sample_rate)

print(f"Generated broadband noise with approximately {target_power_db} dBFS power.")

def calculate_audio_power(file_path: str) -> dict:
    # Load audio data from .flac file
    audio_data, samplerate = sf.read(file_path)
    # Calculate the power of each channel in dB
    power = 10 * np.log10(np.mean(audio_data ** 2) + 1e-10)
    return power

print(calculate_audio_power('broadband_noise_dbfs.wav'))





# import numpy as np
# import soundfile as sf
# import matplotlib.pyplot as plt
# from scipy.fft import fft, fftfreq

# # 📂 Load the audio file
# file_path = 'broadband_noise_dbfs.wav'
# audio_data, sample_rate = sf.read(file_path)
# print(sample_rate)

# # ⏲️ Time Axis
# duration = len(audio_data) / sample_rate
# time_axis = np.linspace(0, duration, len(audio_data))

# # 🎶 Fourier Transform
# N = len(audio_data)  # Number of samples
# audio_fft = fft(audio_data)  # Compute FFT
# freqs = fftfreq(N, 1/sample_rate)  # Frequency axis

# # 🎨 Visualization

# # 1. 📈 Time Domain
# plt.figure(figsize=(10, 4))
# plt.plot(time_axis, audio_data, color='blue')
# plt.title('Audio Signal in Time Domain')
# plt.xlabel('Time [s]')
# plt.ylabel('Amplitude')
# plt.grid(True)
# plt.show()

# # 2. 🔊 Frequency Domain
# plt.figure(figsize=(10, 4))
# plt.plot(freqs, np.abs(audio_fft) / N, color='red')
# plt.title('Magnitude Spectrum of the Audio Signal')
# plt.xlabel('Frequency [Hz]')
# plt.ylabel('Amplitude')
# plt.grid(True)
# plt.show()

import soundfile as sf
import sounddevice as sd

# 📂 Load the audio file
file_path = 'broadband_noise_dbfs.wav'  # Replace with your file path
audio_data, sample_rate = sf.read(file_path)


# ✅ Check if the audio is already mono
if audio_data.ndim > 1:
    print("The audio file is already stereo or multi-channel.")
else:
    # 🎧 Create a silent second channel
    silent_channel = np.zeros_like(audio_data)

    # 🎚️ Combine to create a stereo signal
    stereo_audio = np.column_stack((audio_data, silent_channel))

    # 💾 Save the stereo audio file
    output_path = 'broadband_noise_dbfs.wav'
    sf.write(output_path, stereo_audio, sample_rate)
    print(f"Stereo audio file created: {output_path}")

# 🎚️ Check if the audio is stereo
if audio_data.ndim > 1:
    # Extract the first channel (usually the left channel)
    stereo_audio = stereo_audio[:, 0]

# 🎵 Play the audio
print("Playing the first channel...")
sd.play(stereo_audio, sample_rate)
sd.wait()  # Wait until the audio finishes playing
print("Playback finished.")

import numpy as np
import soundfile as sf
from scipy import signal

# 📂 Load the audio file
file_path = 'broadband_noise_dbfs.wav'  # Replace with your audio file path
audio_data, sample_rate = sf.read(file_path)

# 🎚️ Select the first channel if stereo
if audio_data.ndim > 1:
    audio_data = audio_data[:, 0]

# 🎧 Define A-weighting filter coefficients (based on IEC 61672:2003)
def a_weighting_filter(sample_rate):
    # Zeros and poles for A-weighting filter
    f1 = 20.6
    f2 = 107.7
    f3 = 737.9
    f4 = 12194.0

    # Coefficients based on standard (IEC 61672:2003)
    A1000 = 1.9997  # 1 kHz frequency scaling
    numerator = [(2 * np.pi * f4) ** 2 * (10 ** (A1000 / 20)), 0, 0, 0, 0]
    denominator = np.polymul([1, 4 * np.pi * f4, (2 * np.pi * f4) ** 2],
                             [1, 4 * np.pi * f1, (2 * np.pi * f1) ** 2])
    denominator = np.polymul(np.polymul(denominator,
                                        [1, 2 * np.pi * f3]),
                             [1, 2 * np.pi * f2])

    # Digital filter design using bilinear transformation
    b, a = signal.bilinear(numerator, denominator, sample_rate)
    return b, a

# 🎚️ Apply A-weighting filter
b, a = a_weighting_filter(sample_rate)
weighted_audio = signal.lfilter(b, a, audio_data)

# 🔥 Calculate RMS level of the weighted signal
rms = np.sqrt(np.mean(weighted_audio**2))

# 🎯 Convert RMS to dB(A)
dba_level = 20 * np.log10(rms)

print(f"The A-weighted sound level of the broadband noise is approximately {dba_level:.2f} dB(A)")



