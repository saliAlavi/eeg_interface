import pandas as pd
import numpy as np

# # Load the CSV file
# csv_file_path = "audio_stimuli_data/trials_original.csv"  # Change path as needed
# df = pd.read_csv(csv_file_path)

# # Generate SNR values using normal distribution, mean=15, std=3 (adjustable)
# snr_values = np.random.normal(loc=15, scale=3, size=len(df))

# # Clip values to the range [0, 20]
# snr_values = np.clip(snr_values, 0, 20)

# # Round to integer if needed
# df["SNR"] = snr_values.round().astype(int)

# # Save the modified CSV file
# modified_csv_path = "audio_stimuli_data/trials.csv"  # Change path as needed
# df.to_csv(modified_csv_path, index=False)

# print(f"✅ Modified CSV saved to: {modified_csv_path}")

# # Display first few rows for verification
# print(df.head())


import matplotlib.pyplot as plt
import seaborn as sns


# Load the CSV file
csv_file_path = "audio_stimuli_data/trials.csv"  # Change path as needed
df = pd.read_csv(csv_file_path)

# Plot the distribution of SNR values
plt.figure(figsize=(8, 5))
sns.histplot(df["SNR"], bins=21, kde=True)

plt.title("Distribution of SNR Values")
plt.xlabel("SNR")
plt.ylabel("Frequency")
plt.grid(True)
plt.tight_layout()
plt.show()
