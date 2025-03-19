import pandas as pd
import numpy as np

# Load the CSV file
csv_file_path = "audio_stimuli_data/trials_original.csv"  # Change path as needed
df = pd.read_csv(csv_file_path)

# Add a new column "SNR" with random values between 10 and 20 (inclusive)
df["SNR"] = np.random.randint(10, 21, size=len(df))

# Save the modified CSV file
modified_csv_path = "audio_stimuli_data/trials.csv"  # Change path as needed
df.to_csv(modified_csv_path, index=False)

print(f"✅ Modified CSV saved to: {modified_csv_path}")

# Display first few rows for verification
print(df.head())
