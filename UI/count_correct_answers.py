import json

# Load the JSON file
participant = "Subject 7"
with open('experiment_data/' + participant+ '/answers.json', 'r') as file:
    data = json.load(file)

# List of training trials to exclude
training_trials = {f"Training-{i}" for i in range(1, 6)}

# Count correct answers excluding training trials
correct_count = sum(
    1 for answer in data
    if answer.get("Correct") == 1 and answer.get("Trial No.") not in training_trials
)

print(f"Number of correct answers (excluding training): {correct_count}")
