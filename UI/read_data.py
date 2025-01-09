import pickle
import os
pickle_file = "experiment_data/a2ac2ce3/Trial_1/gaze_data.p"

print(os.path.getsize(pickle_file))

with open(pickle_file, 'rb') as f:
    data = pickle.load(f)


print(len(data))