import pandas as pd
import os
import json
import time
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMessageBox, QRadioButton, QButtonGroup, QInputDialog
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtGui import QFont
import soundfile as sf
import sounddevice as sd
import threading
import random
from record_signals import Recorder
import asyncio
from PySide6.QtWidgets import QApplication  # Add this import if not already present
import logging


class TrialDisplayUI(QMainWindow):
    def __init__(self, csv_path, audio_dir, unique_id, data_directory):
        super().__init__()
        self.csv_path = csv_path
        self.audio_dir = audio_dir
        self.trials_data = pd.read_csv(self.csv_path)
        # Ask user for starting trial number
        start_trial, ok = QInputDialog.getInt(
            self, 
            "Start Trial",                     # Dialog title
            "Enter the trial number to start from:",  # Prompt
            1,                                 # Default value
            1,                                 # Minimum value
            len(self.trials_data),            # Maximum value
            1                                  # Step size
        )
        if ok:
            self.current_trial_index = start_trial - 1  # Adjust for 0-based index
        else:
            self.current_trial_index = 0  # Default to trial 1 if user cancels
            
        # self.current_trial_index = 0
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
        # self.device_ids = [0, 1, 3]
        self.device_ids = [
            i for i, device in enumerate(devices) if "Eris 3.5BT" in device['name']
        ]
        self.device_ids = self.device_ids[:3]
        self.device_ids = sorted(self.device_ids, reverse=True)

        # Initialize UI elements
        self.initUI()

    def initUI(self):
        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        

        palette = self.central_widget.palette()
        palette.setColor(QPalette.Window, QColor("#BEDBED"))
        self.central_widget.setAutoFillBackground(True)
        self.central_widget.setPalette(palette)

        self.layout = QVBoxLayout(self.central_widget)

        # Create a layout for the speaker boxes
        self.speaker_layout = QHBoxLayout()

        # Create the speaker boxes with specific colors and labels
        self.speaker_boxes = []
        self.speaker_colors = []
        speaker_info = [("white", "Speaker-1"), ("orange", "Speaker-2"), ("yellow", "Speaker-3"), ("black", "Speaker-4")]
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
            if self.current_trial_index<5:
                self.trial_label.setText(f"<span style='font-weight: bold;'>This is a training trial to make you become familiar with the experiment.</span>")
            else:
                self.trial_label.setText(f"Trial #<span style='font-weight: bold;'>{trial['Trial No.']}</span>")
            # Assume the color mapping for speakers is defined
            color_map = {
                1: "white",
                2: "orange",
                3: "yellow",
                4: "black"
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

    def startExp(self):
        print("Starting Experiment...")  # Debugging
        self.trial_label.setText(f"<span style='font-weight: bold;'>Training session is over. Now you are familiar with the experiment.</span>")
        self.trial_label.show()  # Ensure the label is visible
        self.attended_label.setText("<span style='font-weight:bold;'>The main experiment will start soon.</span>")
        self.attended_label.show()  # Ensure the label is visible
        self.play_button.hide()
        self.question_label.hide()
        for button in self.options_buttons:
            button.hide()
        self.submit_button.hide()

        # Start the exp timer
        self.exp_time_remaining = 30  # 30 seconds
        self.exp_timer = QTimer(self)
        self.exp_timer.timeout.connect(self.updateExpCountdown)
        self.updateExpCountdown()  # Initial update
        self.exp_timer.start(1000)  # Update every second

    def updateExpCountdown(self):
        """Update the experiment countdown timer."""
        if self.exp_time_remaining > 0:
            minutes, seconds = divmod(self.exp_time_remaining, 60)
            # print(f"Exp countdown: {minutes:02d}:{seconds:02d}")  # Debugging
            self.attended_label.setText(
                f"<span style='font-weight:bold;'>The main experiment will start in {minutes:02d}:{seconds:02d}.</span>"
            )
            self.exp_time_remaining -= 1
            QApplication.processEvents()  # Force UI to update
        else:
            self.exp_timer.stop()
            print("Experiment started.")  # Debugging
            self.attended_label.setText("<span style='font-weight: bold;'>Please click 'Next' to start the main experiment. There will be a total of 100 trials.</span>")
            self.showResumeButton()  # Show the resume button

    def startBreak(self):
        """Start a 10-minute break."""
        print("Starting break...")  # Debugging
        self.trial_label.setText("Break")
        self.trial_label.show()  # Ensure the label is visible
        self.attended_label.setText("You have a 10-minute break. Please relax!")
        self.attended_label.show()  # Ensure the label is visible
        self.play_button.hide()
        self.question_label.hide()
        for button in self.options_buttons:
            button.hide()
        self.submit_button.hide()

        # Start the break timer
        self.break_time_remaining = 1*60  # 10 minutes in seconds
        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self.updateBreakCountdown)
        self.updateBreakCountdown()  # Initial update
        self.break_timer.start(1000)  # Update every second

    def updateBreakCountdown(self):
        """Update the break countdown timer."""
        if self.break_time_remaining > 0:
            minutes, seconds = divmod(self.break_time_remaining, 60)
            # print(f"Break countdown: {minutes:02d}:{seconds:02d}")  # Debugging
            self.attended_label.setText(
                f"Break: {minutes:02d}:{seconds:02d} remaining. Please relax!"
            )
            self.break_time_remaining -= 1
            QApplication.processEvents()  # Force UI to update
        else:
            self.break_timer.stop()
            print("Break ended.")  # Debugging
            self.attended_label.setText("Break is over. Please click 'Next' to continue.")
            self.showResumeButton()  # Show the resume button

    def showResumeButton(self):
        """Show a button to resume trials after the break."""
        self.resume_button = QPushButton("Next")
        self.resume_button.setStyleSheet("""
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
        self.resume_button.clicked.connect(self.resumeTrials)
        self.layout.addWidget(self.resume_button)

    def resumeTrials(self):
        """Resume trials after the break."""
        self.layout.removeWidget(self.resume_button)  # Remove the resume button
        self.resume_button.deleteLater()
        self.loadTrial()  # Load the next trial


    def highlightSpeaker(self, speaker_index):
        # Validate speaker index
        if not (0 <= speaker_index < len(self.speaker_boxes)):
            print(f"Invalid speaker index: {speaker_index}")
            return

        # Set the highlighted speaker
        self.highlighted_speaker = speaker_index
        color_map = {
                "white": (255, 255, 255),
                "orange": (255, 121, 0),
                "yellow": (255, 255, 0),
                "black": (0, 0, 0)
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
        if self.current_trial_index<5:
            trial_folder = os.path.join(self.participant_folder, trial['Trial No.'])
        else:
            trial_folder = os.path.join(self.participant_folder, "Eval-"+trial['Trial No.'])
        os.makedirs(trial_folder, exist_ok=True)

        # Initialize the Recorder for the current trial -- EEG Recorder
        self.recorder = Recorder({
            'save_dir': trial_folder,  # Save EEG and gaze data in trial-specific folder
            'sr_eeg': 500,
            'print_every': 1,
            'verbose': True
        })

        audio_files = [trial['Device-1'], trial['Device-2'], trial['Device-3']]

        # Start a thread for recording EEG and gaze -- EEG Recorder
        recording_thread = threading.Thread(target=self.recordData)
        recording_thread.start()

        # Wait for first samples from both EEG and gaze streams
        self.recorder.first_eeg_sample_event.wait()
        self.recorder.first_gaze_sample_event.wait()

        # Play audio on the main thread
        self.playAudio(audio_files)

        # Signal to stop recording once playback is complete -- EEG Recorder
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
        options.append(("I could not pay attention", "No Attention"))

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
            "Trial No.": trial['Trial No.'],
            "Question": trial['Question'],
            "Selected Answer": selected_answer,
            "Correct": is_correct,
        }
        self.append_to_json(answer_data)

        # Move to the next trial
        self.current_trial_index += 1

        if self.current_trial_index == 54:
            self.startBreak()
            return
        elif self.current_trial_index == 5:
            self.startExp()
            return
        else:
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

    # EEG Recorder
    def recordData(self):
        """Runs the Recorder's main function."""
        self.recorder.stop_event.clear()  # Ensure the recorder is ready to record
        asyncio.run(self.recorder.main())  # Run recording asynchronously

    def playAudio(self, audio_files):
        timestamps = []
        
        # Pre-load all audio files into memory to avoid file I/O delays during playback
        audio_data = []
        for audio_file in audio_files:
            file_path = f"{self.audio_dir}/{audio_file}"
            data, samplerate = sf.read(file_path)
            audio_data.append((data, samplerate))

        # Event to trigger all threads to start at the same time
        start_event = threading.Event()

        def play_on_device(audio_data, device_id):
            trial = self.trials_data.iloc[self.current_trial_index]
            if self.current_trial_index<5:
                trial_folder = os.path.join(self.participant_folder, trial['Trial No.'])
            else:
                trial_folder = os.path.join(self.participant_folder, "Eval-"+trial['Trial No.'])
            os.makedirs(trial_folder, exist_ok=True) 
            try:
                data, samplerate = audio_data
                
                # Wait for all threads to be ready to play simultaneously
                # start_event.wait()

                # Capture the time before starting playback
                start_time = time.time()
                # print(f"Audio start time: {start_time:.6f} seconds (device {device_id})")

                # Start playing the audio on the specific device
                sd.play(data, samplerate=samplerate, device=device_id)

                # Capture the time after calling sd.play()
                playback_start_time = time.time()

                # # Calculate and print the startup time (time from calling sd.play to actual start)
                # startup_time = playback_start_time - start_time
                # print(f"Audio startup time: {startup_time:.6f} seconds (device {device_id})")

                # Wait for the playback to finish
                sd.wait()

                # Record the end time after the audio finishes
                end_time = time.time()


                # Store the timestamps for each playback
                timestamps.append({
                    "device_id": device_id,
                    "start_time": start_time,
                    "playback_start_time": playback_start_time,
                    "end_time": end_time
                })

                # print(f"Audio end time: {end_time:.6f} seconds (device {device_id})")

            except Exception as e:
                print(f"Error playing audio on device {device_id}: {e}")

            with open(os.path.join(trial_folder, "audio_timestamps.json"), "w") as json_file:
                json.dump(timestamps, json_file, indent=4)  # indent=4 makes the JSON pretty and readable     

        threads = []

        # Create and start a thread for each audio file
        for idx, audio_file in enumerate(audio_files):
            thread = threading.Thread(target=play_on_device, args=(audio_data[idx], self.device_ids[idx]))
            threads.append(thread)
            # thread.start()

        for thread in threads:
            thread.start()

        # Signal all threads to start playback at the same time
        start_event.set()

        # Wait for all threads to finish before continuing
        for thread in threads:
            thread.join()

        print("All audio playback complete.")



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