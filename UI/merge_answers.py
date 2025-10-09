import os
import json

def merge_json_files(directory_path, output_file):
    merged_data = []

    # Loop through all files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    # If the file contains a list, extend the merged_data
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        merged_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"Skipping {filename} due to JSON decode error: {e}")

    # Write the merged data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4)

    print(f"Merged {len(merged_data)} JSON entries into {output_file}")

# Example usage:
subject_folder = 'experiment_data/Subject 15'
merge_json_files(subject_folder, subject_folder+'/answers.json')
