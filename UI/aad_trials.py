import pandas as pd

# Load the CSV file
file_path = "audio_stimuli_data/trials.csv"
df = pd.read_csv(file_path)

# Function to split stereo file names into two mono file names
def split_stereo_filename(filename):
    if isinstance(filename, str) and "_" in filename:
        parts = filename.rsplit("_", 2)
        if len(parts) == 2 and parts[1].endswith(".flac"):
            left_file = f"{parts[0]}.flac"
            right_file = f"{parts[1]}"
        if len(parts) == 3 and parts[2].endswith(".flac"):
            left_file = f"{parts[0]}_{parts[1]}.flac"
            right_file = f"{parts[0]}_{parts[2]}"
    return left_file, right_file

# Creating new columns for left and right channels
df["Device-1 Left"], df["Device-1 Right"] = zip(*df["Device-1"].apply(split_stereo_filename))
df["Device-2 Left"], df["Device-2 Right"] = zip(*df["Device-2"].apply(split_stereo_filename))
df["Device-3 Left"], df["Device-3 Right"] = zip(*df["Device-3"].apply(split_stereo_filename))

# Dropping original stereo columns
df.drop(columns=["Device-1", "Device-2", "Device-3"], inplace=True)

# Rename the columns based on their angle positions
column_mapping = {
    "Device-1 Left": "-67.5 Stimuli",
    "Device-1 Right": "-22.5 Stimuli",
    "Device-2 Left": "22.5 Stimuli",
    "Device-2 Right": "67.5 Stimuli",
    "Device-3 Left": "-135 Stimuli",
    "Device-3 Right": "135 Stimuli",
    "Device-1 Left Power": "-67.5 Power",
    "Device-1 Right Power": "-22.5 Power",
    "Device-2 Left Power": "22.5 Power",
    "Device-2 Right Power": "67.5 Power",
    "Device-3 Left Power": "-135 Power",
    "Device-3 Right Power": "135 Power"
}

df.rename(columns=column_mapping, inplace=True)

# Mapping of Attended Speaker values to corresponding angles
attended_speaker_mapping = {
    1: -67.5,
    2: -22.5,
    3: 22.5,
    4: 67.5
}

# Replace Attended Speaker values with their corresponding angles
df["Attended Speaker"] = df["Attended Speaker"].map(attended_speaker_mapping)

# Reordering the columns
ordered_columns = [
    "Trial No.", "Attended Speaker",
    "-67.5 Stimuli", "-22.5 Stimuli", "22.5 Stimuli", "67.5 Stimuli", "-135 Stimuli", "135 Stimuli",  # Stimuli columns
    "-67.5 Power", "-22.5 Power", "22.5 Power", "67.5 Power", "-135 Power", "135 Power",  # Power columns
    "SNR", "Question", "Answer", "Option-1", "Option-2", "Option-3"  # Remaining columns
]

df = df[ordered_columns]

# Save or display the modified dataframe
df.to_csv("audio_stimuli_data/aad_trials.csv", index=False)

# Display the first few rows
print(df.head())
