import pickle
import os
pickle_file = "experiment_data/6e149c40/Training-1/gaze_time_data.p"

with open(pickle_file, 'rb') as f:
    data = pickle.load(f)

print(data)

pickle_file = "experiment_data/6e149c40/Training-1/eeg_time_data.p"


with open(pickle_file, 'rb') as f:
    data = pickle.load(f)


print(data)