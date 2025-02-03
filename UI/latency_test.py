import threading
import soundfile as sf
import sounddevice as sd
import time
import numpy as np

class AudioPlayer:
    def __init__(self, audio_dir, device_ids):
        self.audio_dir = audio_dir
        self.device_ids = device_ids

    def playAudio(self, audio_files):
        timestamps = []

        # Pre-load all audio files into memory to avoid file I/O delays during playback
        audio_data = []
        for audio_file in audio_files:
            file_path = f"{self.audio_dir}/{audio_file}"
            data, samplerate = sf.read(file_path)
            data = data.astype(np.float32)
            audio_data.append((data, samplerate))

        # Event to trigger all threads to start at the same time
        start_event = threading.Event()

        def play_on_device(audio_data, device_id):
            try:
                data, samplerate = audio_data

                # Wait for all threads to be ready to play simultaneously
                start_event.wait()

                # Capture the time before starting playback
                start_time = time.time()

                # Start playing the audio on the specific device
                sd.play(data, samplerate=samplerate, device=device_id)

                # Capture the time after calling sd.play()
                playback_start_time = time.time()

                # Calculate and print the startup time (time from calling sd.play to actual start)
                startup_time = playback_start_time - start_time
                print(f"Audio startup time: {startup_time:.6f} seconds (device {device_id})")

                # Wait for the playback to finish
                sd.wait()

                # Record the end time after the audio finishes
                end_time = time.time()

                # Store the timestamps for each playback
                timestamps.append({
                    "device_id": device_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": (end_time - start_time)
                })

            except Exception as e:
                print(f"Error playing audio on device {device_id}: {e}")

        threads = []

        # Create and start a thread for each audio file
        for idx, audio_file in enumerate(audio_files):
            thread = threading.Thread(target=play_on_device, args=(audio_data[idx], self.device_ids[idx]))
            threads.append(thread)
            # thread.start()

        for thread in threads:
            thread.start()

        # Introduce a tiny delay before triggering the start event
        # sd.sleep(10)  # Sleep for 10 milliseconds to allow threads to synchronize more effectively

        # Signal all threads to start playback at the same time
        start_event.set()

        # Wait for all threads to finish before continuing
        for thread in threads:
            thread.join()

        print("All audio playback complete.")
        print("Playback timestamps:", timestamps)

# Example usage
audio_player = AudioPlayer(
    audio_dir="C:/Codes/eeg_interface_naimul/eeg_interface/UI/audio_stimuli_data/pairs/", 
    device_ids=[3, 4, 6]
)
audio_player.playAudio(audio_files=["Practice_17_345.flac", "Practice_278_54.flac", "Practice_Noise_505_527.flac"])
