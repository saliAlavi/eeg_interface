import sounddevice as sd
import soundfile as sf
import numpy as np

def play_flac(file_path, device_index):
    # Read the FLAC file
    data, samplerate = sf.read(file_path, dtype='float32')
    
    # Print available devices
    # print("Available devices:")
    # print(sd.query_devices())

    # Play the audio file on the specified device
    try:
        sd.play(data, samplerate, device=device_index)
        sd.wait()  # Wait until playback finishes
        print("Playback finished.")
    except Exception as e:
        print(f"Error during playback: {e}")

if __name__ == "__main__":
    # Set your FLAC file path and device index here
    file_path = "C:/Codes/eeg_interface_naimul/eeg_interface/UI/audio_stimuli_data/pairs/30_2127.flac"  # Replace with your FLAC file path

    devices = sd.query_devices()
    print(devices)

    # Find devices with "Eris 3.5BT" in their name
    # self.device_ids = [0, 1, 3]
    device_ids = [
        i for i, device in enumerate(devices) if "Eris 3.5BT" in device['name']
        ]
    
    device_ids = device_ids[:3]
    device_ids = sorted(device_ids, reverse=True)
    
    print(device_ids)
    index = 1  # Replace with your desired device index

    # play_flac(file_path, device_ids[index])
