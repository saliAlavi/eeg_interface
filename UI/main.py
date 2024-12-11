import sys
from PySide6.QtWidgets import QApplication
from DemographicUI import DemographicUI
from TrialDisplayUI import TrialDisplayUI
import os
import uuid


def main():
    app = QApplication(sys.argv)

    # Define paths for CSV, audio files, and JSON stimuli files
    csv_path = "audio_stimuli_data/trials.csv"  # Path to the updated trials.csv file
    audio_directory = "audio_stimuli_data/pairs"  # Replace with the directory containing audio files

    # Generate unique ID and folder
    unique_id = str(uuid.uuid4())[:8]
    data_directory = "./experiment_data"
    participant_folder = os.path.join(data_directory, unique_id)
    os.makedirs(participant_folder, exist_ok=True)

    # Initialize DemographicUI
    demographic_ui = DemographicUI(unique_id, data_directory)

    # Create a container for the TrialDisplayUI reference
    trial_display_ui_container = {"window": None}

    def open_trial_display():
        # Close the demographic UI
        demographic_ui.close()
        print("DemographicUI closed. Opening TrialDisplayUI...")

        try:
            # Initialize and keep a reference to TrialDisplayUI
            trial_display_ui = TrialDisplayUI(csv_path, audio_directory, unique_id, data_directory)
            trial_display_ui_container["window"] = trial_display_ui
            trial_display_ui.show()
            print("TrialDisplayUI opened successfully!")
        except Exception as e:
            print(f"Error opening TrialDisplayUI: {e}")

    # Connect the DemographicUI submission signal to open the TrialDisplayUI
    demographic_ui.submitted.connect(open_trial_display)

    # Show the DemographicUI
    demographic_ui.show()

    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
