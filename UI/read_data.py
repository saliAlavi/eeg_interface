import pickle
import os
pickle_file = "experiment_data/7c7c6499/Training-1/gaze_data.p"

with open(pickle_file, 'rb') as f:
    data = pickle.load(f)

last= len(data)-1
print(data[last]['gaze_ts'] - data[1]['gaze_ts'])

pickle_file = "experiment_data/7c7c6499/Training-1/eeg_data.p"


with open(pickle_file, 'rb') as f:
    data = pickle.load(f)


last= len(data)-1
print(data[last]['eeg_ts'] - data[1]['eeg_ts'])

import json

# Load the data from the JSON file
with open('experiment_data/7c7c6499/Training-1/audio_timestamps.json', 'r') as file:
    data = json.load(file)

# Extract playback start times and end times
playback_start_times = [entry['playback_start_time'] for entry in data]
end_times = [entry['end_time'] for entry in data]

# Find the minimum playback start time and maximum end time
min_playback_start_time = min(playback_start_times)
max_end_time = max(end_times)

# Calculate the difference
time_difference = max_end_time - min_playback_start_time

# Print the result
print(f"Minimum playback start time: {min_playback_start_time}")
print(f"Maximum end time: {max_end_time}")
print(f"Difference: {time_difference} seconds")
