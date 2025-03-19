import numpy as np
import pandas as pd
import random
import shutil
from scipy import signal

# Load the CSV file
df = pd.read_csv("audio_stimuli_data/trials_original.csv")

# Define possible gain levels
gain_levels = [1, 2, 3, 4]

def assign_fully_unique_gains(trial_count):
    """Generate unique gain pairs ensuring no overlap within a trial."""
    available_pairs = [(a, b) for a in gain_levels for b in gain_levels if a != b]
    random.shuffle(available_pairs)

    assigned_gains = []
    while len(assigned_gains) < trial_count:
        for pair1 in available_pairs:
            for pair2 in available_pairs:
                if pair1 != pair2 and not (set(pair1) & set(pair2)):  # Ensure uniqueness
                    assigned_gains.append((pair1, pair2))
                    if len(assigned_gains) == trial_count:
                        return assigned_gains
    return assigned_gains[:trial_count]  # Trim excess just in case

# Separate practice trials and main trials
practice_trials = df[df["Trial No."].str.startswith("Training")]
main_trials = df[~df["Trial No."].str.startswith("Training")]

# Generate unique gain assignments for 100 main trials
unique_gain_pairs_main = assign_fully_unique_gains(100)
device1_gains_main, device2_gains_main = zip(*unique_gain_pairs_main)

# Generate unique gain assignments for training trials
unique_gain_pairs_train = assign_fully_unique_gains(len(practice_trials))
device1_gains_train, device2_gains_train = zip(*unique_gain_pairs_train)

# Assign values to the dataframe
main_trials.loc[:, "Gain_Device-1"] = [f"{a}_{b}" for a, b in device1_gains_main]
main_trials.loc[:, "Gain_Device-2"] = [f"{a}_{b}" for a, b in device2_gains_main]

practice_trials.loc[:, "Gain_Device-1"] = [f"{a}_{b}" for a, b in device1_gains_train]
practice_trials.loc[:, "Gain_Device-2"] = [f"{a}_{b}" for a, b in device2_gains_train]

# Combine back the dataset
df_updated = pd.concat([practice_trials, main_trials]).sort_index()

# Save the updated dataframe
df_updated.to_csv("audio_stimuli_data/trials.csv", index=False)

print("Updated trials data with fully unique gains saved successfully.")