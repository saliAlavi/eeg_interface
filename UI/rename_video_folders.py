import os
import re

def natural_key(s):
    # Splits a string into list of strings and numbers for natural sorting
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def rename_folders_numerically(directory_path, start=1, end=70):
    # Get all subfolders
    folders = [
        f for f in os.listdir(directory_path)
        if os.path.isdir(os.path.join(directory_path, f))
    ]

    # Sort naturally (handles both "apple", "2", "10", etc.)
    folders.sort(key=natural_key)

    # Limit to desired range
    folders_to_rename = folders[:end - start + 1]

    for i, folder_name in enumerate(folders_to_rename, start=start):
        old_path = os.path.join(directory_path, folder_name)
        new_folder_name = str(i)
        new_path = os.path.join(directory_path, new_folder_name)

        if os.path.exists(new_path):
            print(f"Skipping '{folder_name}' -> '{new_folder_name}' (target exists)")
            continue

        os.rename(old_path, new_path)
        print(f"Renamed '{folder_name}' -> '{new_folder_name}'")

# Example usage:
video_folder = 'experiment_data/Subject 2/Videos'
rename_folders_numerically(video_folder, start=45, end=85)
