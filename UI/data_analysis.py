import os
import json
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import pandas as pd

# Updated base directory
base_dir = 'experiment_data/'

# Initialize plot for incorrect trials by subject
plt.figure(figsize=(12, 6))
markers = ['o', 's', 'x', '^', 'v', 'D', 'P', '*']
subject_idx = 0

# Store incorrect trials across all subjects
all_incorrect_trials = []

# Loop through subject folders
for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and folder.lower().startswith('subject'):
        json_path = os.path.join(folder_path, 'answers.json')
        if os.path.isfile(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Filter out training trials
            real_trials = [entry for entry in data if not entry["Trial No."].startswith("Training")]

            # Get incorrect trial numbers
            incorrect_trials = [int(entry["Trial No."]) for entry in real_trials if entry["Correct"] == 0]
            all_incorrect_trials.extend(incorrect_trials)

            # Count correct answers
            correct_count = sum(entry["Correct"] for entry in real_trials)

            # Plot incorrect trials per subject
            plt.scatter(incorrect_trials, [subject_idx]*len(incorrect_trials),
                        label=f"{folder} (Correct: {correct_count})",
                        marker=markers[subject_idx % len(markers)])
            subject_idx += 1

# Finalize first plot
plt.xlabel("Trial No.")
plt.ylabel("Subjects")
plt.title("Incorrect Trials by Subject")
plt.yticks(range(subject_idx), [f"Subject {i+1}" for i in range(subject_idx)])
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)

# --- NEW FIGURE: Common Incorrect Trials ---
# Count how often each incorrect trial occurred
trial_counts = Counter(all_incorrect_trials)
common_trials = {trial: count for trial, count in trial_counts.items() if count > 1}

# Plot common incorrect answers
plt.figure(figsize=(10, 5))
bars = plt.bar(common_trials.keys(), common_trials.values())

# Set title and labels
plt.title("Common Incorrect Trials Across Subjects")
plt.xlabel("Trial No.")
plt.ylabel("Number of Subjects Incorrect")

# Ensure y-axis has only integer ticks
max_count = max(common_trials.values(), default=1)
plt.yticks(range(1, max_count + 1))

plt.grid(axis='y')
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)


## Incorrect trials for each SNR

# Load trials.csv and extract SNR info
trials_df = pd.read_csv(os.path.join('audio_stimuli_data', 'trials.csv'))
trials_df = trials_df[~trials_df["Trial No."].str.startswith("Training")]
trial_snr_map = dict(zip(trials_df["Trial No."], trials_df["SNR"]))

# Store incorrect answer counts per SNR per subject
subject_incorrect_by_snr = defaultdict(lambda: defaultdict(int))

# Find all subject folders
for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and folder.lower().startswith("subject"):
        json_path = os.path.join(folder_path, 'answers.json')
        if os.path.isfile(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Remove training trials
            real_trials = [entry for entry in data if not entry["Trial No."].startswith("Training")]

            # Count incorrect answers by SNR
            for entry in real_trials:
                trial_no = entry["Trial No."]
                if entry["Correct"] == 0 and trial_no in trial_snr_map:
                    snr = trial_snr_map[trial_no]
                    subject_incorrect_by_snr[folder][snr] += 1

# Prepare data for plotting
all_snrs = sorted(set(trial_snr_map.values()))
subjects = sorted(subject_incorrect_by_snr.keys())

# Create DataFrame
plot_df = pd.DataFrame(index=all_snrs, columns=subjects).fillna(0)
for subject in subjects:
    for snr, count in subject_incorrect_by_snr[subject].items():
        plot_df.at[snr, subject] = count

# Convert to integer for clean plot
plot_df = plot_df.astype(int)

# Plot grouped bar chart
plot_df.plot(kind='bar', figsize=(12, 6))
plt.title("Incorrect Answers by SNR for Each Subject")
plt.xlabel("SNR")
plt.ylabel("Number of Incorrect Answers")
plt.grid(axis='y')
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)


## Total incorrect vs SNR

# Sum incorrect answers across all subjects for each SNR
total_incorrect_by_snr = defaultdict(int)

for subject_data in subject_incorrect_by_snr.values():
    for snr, count in subject_data.items():
        total_incorrect_by_snr[snr] += count

# Convert to sorted list for plotting
snr_list = sorted(total_incorrect_by_snr.keys())
incorrect_counts = [total_incorrect_by_snr[snr] for snr in snr_list]

# Plot total incorrect answers per SNR
plt.figure(figsize=(10, 5))
plt.bar(snr_list, incorrect_counts)
plt.title("Total Incorrect Answers by SNR (All Subjects)")
plt.xlabel("SNR")
plt.ylabel("Total Incorrect Answers")
plt.grid(axis='y')
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)


## Normalized incorrect answers by SNR

# Step 1: Load trials.csv and count total trials per SNR
trials_df = pd.read_csv(os.path.join('audio_stimuli_data', 'trials.csv'))
trials_df = trials_df[~trials_df["Trial No."].str.startswith("Training")]
trial_snr_map = dict(zip(trials_df["Trial No."], trials_df["SNR"]))

# Total number of trials for each SNR
snr_total_counts = trials_df["SNR"].value_counts().to_dict()

# Step 2: Collect incorrect answers per SNR per subject
subject_incorrect_by_snr = defaultdict(lambda: defaultdict(int))

for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and folder.lower().startswith("subject"):
        json_path = os.path.join(folder_path, 'answers.json')
        if os.path.isfile(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)

            real_trials = [entry for entry in data if not entry["Trial No."].startswith("Training")]

            for entry in real_trials:
                trial_no = entry["Trial No."]
                if entry["Correct"] == 0 and trial_no in trial_snr_map:
                    snr = trial_snr_map[trial_no]
                    subject_incorrect_by_snr[folder][snr] += 1

# Step 3: Normalize and prepare DataFrame
all_snrs = sorted(set(trial_snr_map.values()))
subjects = sorted(subject_incorrect_by_snr.keys())

norm_df = pd.DataFrame(index=all_snrs, columns=subjects).fillna(0.0)

for subject in subjects:
    for snr, count in subject_incorrect_by_snr[subject].items():
        total_trials_for_snr = snr_total_counts.get(snr, 1)  # avoid division by zero
        norm_df.at[snr, subject] = count / total_trials_for_snr

# Plot normalized incorrect answers
norm_df = norm_df.astype(float)
norm_df.plot(kind='bar', figsize=(12, 6))
plt.title("Normalized Incorrect Answers by SNR for Each Subject")
plt.xlabel("SNR")
plt.ylabel("Incorrect Answers (Normalized by Trial Count)")
plt.grid(axis='y')
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)


## Normalized total incorrect answers

# Total incorrect answers per SNR across all subjects (already computed)
total_incorrect_by_snr = defaultdict(int)

for subject_data in subject_incorrect_by_snr.values():
    for snr, count in subject_data.items():
        total_incorrect_by_snr[snr] += count

# Normalize using total number of trials per SNR from trials.csv
normalized_incorrect_by_snr = {}
for snr in total_incorrect_by_snr:
    total_trials = snr_total_counts.get(snr, 1)  # avoid division by zero
    normalized_incorrect_by_snr[snr] = total_incorrect_by_snr[snr] / total_trials

# Prepare for plotting
snr_list = sorted(normalized_incorrect_by_snr.keys())
normalized_counts = [normalized_incorrect_by_snr[snr] for snr in snr_list]

# Plot normalized total incorrect answers per SNR
plt.figure(figsize=(10, 5))
plt.bar(snr_list, normalized_counts)
plt.title("Normalized Total Incorrect Answers by SNR (All Subjects)")
plt.xlabel("SNR")
plt.ylabel("Incorrect Answers (Normalized by Trial Count)")
plt.grid(axis='y')
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)



# Could not pay attention

# Store the trial numbers per subject where they said "I could not pay attention"
attention_trials = defaultdict(list)

# Loop through each subject folder
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and folder.lower().startswith("subject"):
        json_path = os.path.join(folder_path, 'answers.json')
        if os.path.isfile(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Collect matching trial numbers
            for entry in data:
                if entry["Selected Answer"].strip().lower() == "i could not pay attention":
                    try:
                        trial_num = int(entry["Trial No."])
                        attention_trials[folder].append(trial_num)
                    except ValueError:
                        continue  # skip non-numeric trial numbers (e.g., training)

# Plot
plt.figure(figsize=(12, 6))
for idx, (subject, trials) in enumerate(attention_trials.items()):
    plt.scatter(trials, [idx]*len(trials), label=subject)

# Formatting
plt.title('"I Could Not Pay Attention" Trials per Subject')
plt.xlabel('Trial No.')
plt.ylabel('Subjects')
plt.yticks(range(len(attention_trials)), list(attention_trials.keys()))
plt.grid(True, axis='x')
plt.legend(title="Subjects", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)


## attended speakers

# Load trials.csv and filter non-training trials
trials_df = pd.read_csv(os.path.join('audio_stimuli_data', 'trials.csv'))
trials_df = trials_df[~trials_df["Trial No."].str.startswith("Training")]
trial_speaker_map = dict(zip(trials_df["Trial No."], trials_df["Attended Speaker"]))

# Dictionary to hold incorrect counts per attended speaker per subject
incorrect_by_speaker = defaultdict(lambda: defaultdict(int))

# Process each subject folder
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and folder.lower().startswith("subject"):
        json_path = os.path.join(folder_path, 'answers.json')
        if os.path.isfile(json_path):
            with open(json_path, 'r') as f:
                answers = json.load(f)

            # Exclude training trials
            real_trials = [a for a in answers if not a["Trial No."].startswith("Training")]

            for entry in real_trials:
                trial_no = entry["Trial No."]
                if entry["Correct"] == 0 and trial_no in trial_speaker_map:
                    speaker = trial_speaker_map[trial_no]
                    incorrect_by_speaker[folder][speaker] += 1

# Convert to DataFrame for plotting
all_speakers = sorted({speaker for subject_data in incorrect_by_speaker.values() for speaker in subject_data})
subjects = sorted(incorrect_by_speaker.keys())

df = pd.DataFrame(index=all_speakers, columns=subjects).fillna(0)

for subject in subjects:
    for speaker, count in incorrect_by_speaker[subject].items():
        df.at[speaker, subject] = count

# Convert to integer type
df = df.astype(int)

# Plot grouped bar chart
df.T.plot(kind='bar', figsize=(12, 6))
plt.title('Incorrect Answers per Attended Speaker by Subject')
plt.xlabel('Subject')
plt.ylabel('Number of Incorrect Answers')
plt.legend(title='Attended Speaker', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid(axis='y')
plt.show(block=False)
plt.pause(0.1)


# Group by Attended Speaker and SNR, count occurrences
snr_counts = trials_df.groupby(['Attended Speaker', 'SNR']).size().unstack(fill_value=0)

# Plot grouped bar chart
snr_counts.T.plot(kind='bar', figsize=(12, 6))
plt.title('Frequency of SNR Values per Attended Speaker')
plt.xlabel('SNR')
plt.ylabel('Number of Occurrences')
plt.legend(title='Attended Speaker', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y')
plt.tight_layout()
plt.show(block=False)
plt.pause(0.1)

## SNR - Attended Speaker - Incorrect Trial

# Create mapping from trial to (SNR, Attended Speaker)
trial_info = trials_df.set_index("Trial No.")[["SNR", "Attended Speaker"]].to_dict("index")

# Counter: {Attended Speaker: {SNR: count}}
snr_by_speaker = defaultdict(lambda: defaultdict(int))

# Loop through each subject folder
for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and folder.lower().startswith("subject"):
        json_path = os.path.join(folder_path, 'answers.json')
        if os.path.isfile(json_path):
            with open(json_path, 'r') as f:
                answers = json.load(f)

            # Remove training trials
            real_trials = [entry for entry in answers if not entry["Trial No."].startswith("Training")]

            for entry in real_trials:
                trial_no = entry["Trial No."]
                if entry["Correct"] == 0 and trial_no in trial_info:
                    snr = trial_info[trial_no]["SNR"]
                    speaker = trial_info[trial_no]["Attended Speaker"]
                    snr_by_speaker[speaker][snr] += 1

# Create DataFrame
all_snrs = sorted({snr for speaker_data in snr_by_speaker.values() for snr in speaker_data})
all_speakers = sorted(snr_by_speaker.keys())

plot_df = pd.DataFrame(index=all_snrs, columns=all_speakers).fillna(0)

for speaker in all_speakers:
    for snr, count in snr_by_speaker[speaker].items():
        plot_df.at[snr, speaker] = count

# Convert to int
plot_df = plot_df.astype(int)

# Plot
plot_df.plot(kind='bar', figsize=(12, 6))
plt.title('Incorrect Trial SNR Counts per Attended Speaker')
plt.xlabel('SNR')
plt.ylabel('Number of Incorrect Trials')
plt.legend(title='Attended Speaker', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y')
plt.tight_layout()
plt.show()