import pandas as pd
import os
import json
import time
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QRadioButton, QButtonGroup
)
from PySide6.QtGui import QFont
import soundfile as sf
import sounddevice as sd
import threading
import random


class TrialDisplayUI(QMainWindow):
    def __init__(self, csv_path, audio_dir, unique_id, data_directory):
        super().__init__()
        self.csv_path = csv_path
        self.audio_dir = audio_dir
        self.trials_data = pd.read_csv(self.csv_path)
        self.current_trial_index = 0
        self.unique_id = unique_id
        self.data_directory = data_directory

        # Folder for participant data
        self.participant_folder = os.path.join(self.data_directory, self.unique_id)
        os.makedirs(self.participant_folder, exist_ok=True)

        # JSON file to store answers
        self.answer_file = os.path.join(self.participant_folder, "answers.json")
        if not os.path.exists(self.answer_file):
            with open(self.answer_file, "w") as f:
                json.dump([], f)  # Initialize with an empty list

        # Manually specify device IDs for playback
        self.device_ids = [0, 1, 4]  # Replace with the IDs of your audio devices

        # Initialize UI elements
        self.initUI()

    def initUI(self):
        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Trial Info
        self.trial_label = QLabel("Trial No.:")
        self.attended_label = QLabel("Attended Speaker:")
        self.layout.addWidget(self.trial_label)
        self.layout.addWidget(self.attended_label)

        # Play Audio Button
        self.play_button = QPushButton("Play Audio")
        self.play_button.clicked.connect(self.playCurrentAudio)
        self.layout.addWidget(self.play_button)

        # Question and Options (hidden initially)
        self.question_label = QLabel("Question:")
        self.layout.addWidget(self.question_label)
        self.question_label.hide()

        self.options_group = QButtonGroup(self)
        self.options_layout = QVBoxLayout()
        self.options_buttons = []
        for i in range(5):  # 4 randomized options + "I did not pay attention"
            option_button = QRadioButton(f"Option {i+1}")
            self.options_buttons.append(option_button)
            self.options_group.addButton(option_button)
            self.options_layout.addWidget(option_button)
            option_button.hide()  # Hide options initially
        self.layout.addLayout(self.options_layout)

        # Submit Button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.recordAnswer)
        self.layout.addWidget(self.submit_button)
        self.submit_button.hide()  # Hidden initially

        # Load the first trial
        self.loadTrial()

    def loadTrial(self):
        if self.current_trial_index < len(self.trials_data):
            trial = self.trials_data.iloc[self.current_trial_index]
            self.trial_label.setText(f"Trial #{trial['Trial No.']}")
            self.attended_label.setText(f"Please pay attention to Speaker-{trial['Attended Speaker']}")
            self.trial_label.show()
            self.attended_label.show()
            self.play_button.show()
            self.question_label.hide()
            for button in self.options_buttons:
                button.hide()
            self.submit_button.hide()
        else:
            self.trial_label.setText("End of Trials")
            self.attended_label.setText("")
            self.play_button.hide()
            self.question_label.hide()
            for button in self.options_buttons:
                button.hide()
            self.submit_button.hide()

    def playCurrentAudio(self):
        trial = self.trials_data.iloc[self.current_trial_index]
        audio_files = [trial['Device-1'], trial['Device-2'], trial['Device-3']]
        self.playAudio(audio_files)
        self.trial_label.hide()
        self.attended_label.hide()
        self.play_button.hide()
        self.showQuestionAndOptions()

    def showQuestionAndOptions(self):
        trial = self.trials_data.iloc[self.current_trial_index]
        options = [
            (trial['Answer'], "Correct"),
            (trial['Option-1'], "Incorrect 1"),
            (trial['Option-2'], "Incorrect 2"),
            (trial['Option-3'], "Incorrect 3")
        ]
        random.shuffle(options)
        options.append(("I did not pay attention", "No Attention"))

        self.option_roles = {}

        # Reset all radio buttons
        self.options_group.setExclusive(False)  # Allow all buttons to be unchecked
        for button in self.options_buttons:
            button.setChecked(False)  # Uncheck all buttons
        self.options_group.setExclusive(True)  # Restore exclusivity

        # Assign randomized options to buttons
        for i, (option_text, role) in enumerate(options):
            self.options_buttons[i].setText(option_text)
            self.option_roles[self.options_buttons[i]] = role

        # Show question and options
        self.question_label.setText(f"Question: {trial['Question']}")
        self.question_label.show()
        for button in self.options_buttons:
            button.show()
        self.submit_button.show()


    def recordAnswer(self):
        selected_button = self.options_group.checkedButton()
        selected_answer = (
            selected_button.text() if selected_button else "No selection"
        )

        trial = self.trials_data.iloc[self.current_trial_index]
        attended_speaker = int(trial['Attended Speaker'])  # Ensure this is an integer
        is_correct = 0  # Default to incorrect
        attended_to_speaker = None  # Default to None

        # Determine if the answer is correct and calculate "Attended to Speaker"
        if selected_button:
            role = self.option_roles.get(selected_button, None)
            if role == "Correct":
                is_correct = 1
                attended_to_speaker = attended_speaker
                self.showMessage("Correct Answer")
            elif role == "Incorrect 1":
                attended_to_speaker = 1 if attended_speaker == 2 else 2 if attended_speaker == 1 else 1
                self.showMessage("Incorrect Answer. Please listen carefully.")
            elif role == "Incorrect 2":
                attended_to_speaker = 3 if attended_speaker == 2 else 2 if attended_speaker == 1 else 3
                self.showMessage("Incorrect Answer. Please listen carefully.")
            elif role == "Incorrect 3":
                attended_to_speaker = 4 if attended_speaker == 2 else 4 if attended_speaker == 1 else 4
                self.showMessage("Incorrect Answer. Please listen carefully.")
            elif role == "No Attention":
                attended_to_speaker = None  # Do not set a speaker
            else:
                attended_to_speaker = None

        # Add trial data to JSON
        answer_data = {
            "Trial No.": int(trial['Trial No.']),  # Convert to standard int
            "Question": trial['Question'],
            "Selected Answer": selected_answer,
            "Correct": is_correct,
            "Possibility of attending to Speaker": attended_to_speaker,
        }
        self.append_to_json(answer_data)

        self.current_trial_index += 1
        self.loadTrial()


    def showMessage(self, message):
        """Display a message in a message box."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Feedback")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()


    def append_to_json(self, data):
        """Append a new entry to the JSON file."""
        try:
            with open(self.answer_file, "r") as f:
                current_data = json.load(f)
            current_data.append(data)
            with open(self.answer_file, "w") as f:
                json.dump(current_data, f, indent=4)
            print(f"Saved trial data: {data}")
        except Exception as e:
            print(f"Error writing to JSON file: {e}")


    def playAudio(self, audio_files):
        def play_on_device(audio_file, device_id):
            try:
                file_path = f"{self.audio_dir}/{audio_file}"
                data, samplerate = sf.read(file_path)
                sd.play(data, samplerate=samplerate, device=device_id)
                sd.wait()
            except Exception as e:
                print(f"Error playing {audio_file} on device {device_id}: {e}")

        threads = []
        for audio_file, device_id in zip(audio_files, self.device_ids):
            thread = threading.Thread(target=play_on_device, args=(audio_file, device_id))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
