import pandas as pd
import os
import json
import time
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMessageBox, QRadioButton, QButtonGroup, QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont
import soundfile as sf
import sounddevice as sd
import threading
import random
from record_signals import Recorder
import asyncio


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

        # Currently highlighted speaker
        self.highlighted_speaker = None

        # Show the window maximized
        self.showMaximized()
       
        # Retrieve all audio devices
        devices = sd.query_devices()
        print(devices)

        # Find devices with "Eris 3.5BT" in their name
        self.device_ids = [3, 1, 4]
        # self.device_ids = [
            # i for i, device in enumerate(devices) if "Eris 3.5BT" in device['name']
        # ]

        # Initialize UI elements
        self.initUI()

    def initUI(self):
        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create a layout for the speaker boxes
        self.speaker_layout = QHBoxLayout()

        # Create the speaker boxes with specific colors and labels
        self.speaker_boxes = []
        self.speaker_colors = []
        speaker_info = [("red", "Speaker-1"), ("blue", "Speaker-2"), ("green", "Speaker-3"), ("purple", "Speaker-4")]
        for color, text in speaker_info:
            # Store the color
            self.speaker_colors.append(color)

            # Create a vertical layout for each speaker
            speaker_layout = QVBoxLayout()

            # Create the label for the speaker
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(f"color: {color}; font-weight: bold;")  # Set text color and style
            speaker_layout.addWidget(label)

            # Create the colored box
            box = QWidget()
            box.setFixedSize(50, 50)  # Set the size of each box
            box.setStyleSheet(f"background-color: {color}; border: 1px solid black;")  # Set color and border
            speaker_layout.addWidget(box)

            # Add the speaker layout to the main speaker layout
            self.speaker_layout.addLayout(speaker_layout)
            self.speaker_boxes.append(box)

        # Add the speaker layout above the trial number
        self.layout.addLayout(self.speaker_layout)

        # Trial Info
        self.trial_label = QLabel("Trial No.:")
        self.trial_label.setAlignment(Qt.AlignCenter)
        self.attended_label = QLabel("Attended Speaker:")
        self.attended_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.trial_label)
        self.layout.addWidget(self.attended_label)

        # Play Audio Button
        self.play_button = QPushButton("Play Audio")
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #198c87;
                color: white;
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #f96905;
            }
            QPushButton:pressed {
                background-color: #f95a05;
            }
        """)
        self.play_button.clicked.connect(self.playCurrentAudio)
        self.layout.addWidget(self.play_button)

        # Question and Options (hidden initially)
        self.question_label = QLabel("Question:")
        self.question_label.setAlignment(Qt.AlignCenter)
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
        self.layout.setAlignment(Qt.AlignCenter)

        # Submit Button
        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #198c87;
                color: white;
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #f96905;
            }
            QPushButton:pressed {
                background-color: #f95a05;
            }
        """)
        self.submit_button.clicked.connect(self.recordAnswer)
        self.layout.addWidget(self.submit_button)
        self.submit_button.hide()  # Hidden initially

        # Load the first trial
        self.loadTrial()

    def loadTrial(self):
        if self.current_trial_index < len(self.trials_data):
            trial = self.trials_data.iloc[self.current_trial_index]
            self.trial_label.setText(f"Trial #{trial['Trial No.']}")
            # Assume the color mapping for speakers is defined
            color_map = {
                1: "red",
                2: "blue",
                3: "green",
                4: "purple"
            }

            # Get the attended speaker and its color
            attended_speaker = trial['Attended Speaker']
            color = color_map.get(attended_speaker, "black")  # Default to black if no mapping

            # Set the label with HTML formatting
            self.attended_label.setText(
                f"Please pay attention to <span style='color: {color}; font-weight: bold;'>Speaker-{attended_speaker}</span>"
            )
            self.trial_label.show()
            self.attended_label.show()
            self.play_button.show()
            self.question_label.hide()
            for button in self.options_buttons:
                button.hide()
            self.submit_button.hide()
            attended_speaker = trial['Attended Speaker']
            # print(f"Attended Speaker from data: {attended_speaker}")
            self.highlightSpeaker(int(attended_speaker)-1)  # Highlight the attended speaker
        else:
            self.trial_label.setText("End of Trials")
            self.attended_label.setText("")
            self.play_button.hide()
            self.question_label.hide()
            for button in self.options_buttons:
                button.hide()
            self.submit_button.hide()


    def highlightSpeaker(self, speaker_index):
        # Validate speaker index
        if not (0 <= speaker_index < len(self.speaker_boxes)):
            print(f"Invalid speaker index: {speaker_index}")
            return

        # Set the highlighted speaker
        self.highlighted_speaker = speaker_index
        color_map = {
                "red": (255, 0, 0),
                "blue": (0, 0, 255),
                "green": (34, 139, 34),
                "purple": (128, 0, 128)
            }

        for i, box in enumerate(self.speaker_boxes):

            color = self.speaker_colors[i]
            x, y, z = color_map.get(color, (0, 0, 0))  # Default to black if color not found


            if i == speaker_index:
                # Highlighted box: full opacity
                box.setStyleSheet(f"background-color: rgba({x},{y},{z}, 255); border: 2px solid black;")
            else:
                # Dimmed boxes: reduced opacity
                box.setStyleSheet(f"background-color: rgba({x},{y},{z}, 0); border: 1px solid black;")



    def playCurrentAudio(self):
        trial = self.trials_data.iloc[self.current_trial_index]
        trial_no = int(trial['Trial No.'])  # Ensure it's an integer

        # Create a directory for the current trial
        trial_folder = os.path.join(self.participant_folder, f"Trial_{trial_no}")
        os.makedirs(trial_folder, exist_ok=True)

        # Initialize the Recorder for the current trial
        self.recorder = Recorder({
            'save_dir': trial_folder,  # Save EEG and gaze data in trial-specific folder
            'sr_eeg': 512,
            'print_every': 100,
            'verbose': True
        })

        audio_files = [trial['Device-1'], trial['Device-2'], trial['Device-3']]
        # Start a thread for recording EEG and gaze
        recording_thread = threading.Thread(target=self.recordData)
        recording_thread.start()

        # Play audio on the main thread
        self.playAudio(audio_files)

        # Signal to stop recording once playback is complete
        self.recorder.stop_event.set()
        recording_thread.join()  # Wait for the recording thread to finish

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
        # Get the selected button
        selected_button = self.options_group.checkedButton()

        # Validate if a choice has been made
        if not selected_button:
            self.showMessage("Please select an option before submitting.")
            return  # Exit the function without proceeding

        # Proceed with processing the answer if validation passes
        selected_answer = selected_button.text()

        trial = self.trials_data.iloc[self.current_trial_index]
        is_correct = 0  # Default to incorrect

        # Determine if the answer is correct
        role = self.option_roles.get(selected_button, None)
        if role == "Correct":
            is_correct = 1
            # self.showMessage("Correct Answer")
        elif role == "No Attention":
            self.showMessage("Please listen carefully.")
        else:
            self.showMessage("Incorrect Answer. Please listen carefully.")

        # Add trial data to JSON
        answer_data = {
            "Trial No.": int(trial['Trial No.']),  # Convert to standard int
            "Question": trial['Question'],
            "Selected Answer": selected_answer,
            "Correct": is_correct,
        }
        self.append_to_json(answer_data)

        # Move to the next trial
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

    def recordData(self):
        """Runs the Recorder's main function."""
        self.recorder.stop_event.clear()  # Ensure the recorder is ready to record
        asyncio.run(self.recorder.main())  # Run recording asynchronously


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

    def resizeEvent(self, event):
        # Dynamically adjust font size based on the window's width
        window_width = self.width()
        font_size = max(10, window_width // 70)  # Example scaling factor
        font = QFont()
        font.setPointSize(font_size)

        # Apply font to all widgets
        self.applyFontToAllWidgets(self, font)

        # Call the base class implementation
        super().resizeEvent(event)

    def applyFontToAllWidgets(self, widget, font):
        """Recursively apply the font to the widget and all its children."""
        widget.setFont(font)
        for child in widget.findChildren(QWidget):
            child.setFont(font)
