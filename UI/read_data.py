import pickle
import os
pickle_file = "experiment_data/a6a3ac5b/Training-1/gaze_data.p"

print(os.path.getsize(pickle_file))

with open(pickle_file, 'rb') as f:
    data = pickle.load(f)

print(data)
print(len(data))

pickle_file = "experiment_data/a6a3ac5b/Training-1/eeg_data.p"

print(os.path.getsize(pickle_file))

with open(pickle_file, 'rb') as f:
    data = pickle.load(f)


# print(data)
print(len(data))