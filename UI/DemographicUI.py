from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QRadioButton, QButtonGroup, QCheckBox, QPushButton, QLabel, QGroupBox
)
from PySide6.QtCore import Signal
import os
import uuid
import json
from datetime import datetime


class DemographicUI(QMainWindow):
    submitted = Signal()  # Signal to notify that the demographic form is submitted

    def __init__(self, unique_id, data_directory):
        super().__init__()
        self.setWindowTitle("Demographic Information")
        self.setGeometry(100, 100, 400, 600)

        # Use provided unique ID and data directory
        self.unique_id = unique_id
        self.data_directory = data_directory

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        # Unique ID Display
        self.main_layout.addWidget(QLabel(f"Participant ID: {self.unique_id}"))

        # Form Layout
        self.form_layout = QFormLayout()

        # Gender
        self.gender_group = QButtonGroup(self)
        self.gender_layout = QVBoxLayout()
        self.gender_options = ["Man", "Woman", "Other", "Prefer not to say"]
        self.gender_buttons = [QRadioButton(option) for option in self.gender_options]
        for button in self.gender_buttons:
            self.gender_group.addButton(button)
            self.gender_layout.addWidget(button)
        self.gender_other_input = QLineEdit()
        self.gender_other_input.setPlaceholderText("Specify if Other")
        self.gender_layout.addWidget(self.gender_other_input)
        self.form_layout.addRow("Gender:", self._wrap_in_group("Gender", self.gender_layout))

        # Age
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Enter your age")
        self.form_layout.addRow("Age:", self.age_input)

        # Race and Ethnicity
        self.race_ethnicity_layout = QVBoxLayout()
        self.race_ethnicity_options = [
            "Native American", "Asian", "Black/African American", "Hispanic", 
            "Middle Eastern", "White", "Other", "Prefer not to say"
        ]
        self.race_checkboxes = [QCheckBox(option) for option in self.race_ethnicity_options]
        for checkbox in self.race_checkboxes:
            self.race_ethnicity_layout.addWidget(checkbox)
        self.race_other_input = QLineEdit()
        self.race_other_input.setPlaceholderText("Specify if Other")
        self.race_ethnicity_layout.addWidget(self.race_other_input)
        self.form_layout.addRow("Race & Ethnicity:", self._wrap_in_group("Race & Ethnicity", self.race_ethnicity_layout))

        # Hand Preference
        self.hand_pref_group = QButtonGroup(self)
        self.hand_pref_layout = QVBoxLayout()
        self.hand_pref_options = ["Left", "Right", "Any"]
        self.hand_pref_buttons = [QRadioButton(option) for option in self.hand_pref_options]
        for button in self.hand_pref_buttons:
            self.hand_pref_group.addButton(button)
            self.hand_pref_layout.addWidget(button)
        self.form_layout.addRow("Hand Preference:", self._wrap_in_group("Hand Preference", self.hand_pref_layout))

        # Ear Preference
        self.ear_pref_group = QButtonGroup(self)
        self.ear_pref_layout = QVBoxLayout()
        self.ear_pref_options = ["Left", "Right", "Any"]
        self.ear_pref_buttons = [QRadioButton(option) for option in self.ear_pref_options]
        for button in self.ear_pref_buttons:
            self.ear_pref_group.addButton(button)
            self.ear_pref_layout.addWidget(button)
        self.form_layout.addRow("Ear Preference:", self._wrap_in_group("Ear Preference", self.ear_pref_layout))

        # Submit Button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.save_data)
        self.form_layout.addRow(self.submit_button)

        # Add form layout to the main layout
        self.main_layout.addLayout(self.form_layout)

    def _wrap_in_group(self, title, layout):
        group_box = QGroupBox(title)
        group_box.setLayout(layout)
        return group_box

    def save_data(self):
        """Save demographic data to a JSON file and emit the submitted signal."""
        gender = self.get_selected_button_text(self.gender_group, self.gender_other_input)
        age = self.age_input.text()
        race_ethnicity = self.get_selected_checkboxes(self.race_checkboxes, self.race_other_input)
        hand_pref = self.get_selected_button_text(self.hand_pref_group)
        ear_pref = self.get_selected_button_text(self.ear_pref_group)

        submission_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        demographic_data = {
            "Participant ID": self.unique_id,
            "Submission Time": submission_datetime,
            "Gender": gender,
            "Age": age,
            "Race & Ethnicity": race_ethnicity,
            "Hand Preference": hand_pref,
            "Ear Preference": ear_pref
        }

        participant_folder = os.path.join(self.data_directory, self.unique_id)
        json_file = os.path.join(participant_folder, "demographic.json")
        with open(json_file, "w") as f:
            json.dump(demographic_data, f, indent=4)

        print("Demographic data saved successfully!")
        self.submitted.emit()

    @staticmethod
    def get_selected_button_text(button_group, other_input=None):
        for button in button_group.buttons():
            if button.isChecked():
                if button.text() == "Other" and other_input:
                    return other_input.text()
                return button.text()
        return "Not selected"

    @staticmethod
    def get_selected_checkboxes(checkboxes, other_input=None):
        selected = [cb.text() for cb in checkboxes if cb.isChecked()]
        if "Other" in selected and other_input and other_input.text():
            selected[selected.index("Other")] = other_input.text()
        return selected
