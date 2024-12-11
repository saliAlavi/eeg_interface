from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QLineEdit,
    QRadioButton, QButtonGroup, QCheckBox, QPushButton, QLabel, QGroupBox, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
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

        # Show the window maximized
        self.showMaximized()

        # Unique ID Display
        self.main_layout.addWidget(QLabel(f"Participant ID: {self.unique_id}"))

        # Grid Layout for Two Columns
        self.grid_layout = QGridLayout()

        # Gender (Left Column)
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
        self.grid_layout.addWidget(QLabel("Gender:"), 0, 0)
        self.grid_layout.addWidget(self._wrap_in_group("Gender", self.gender_layout), 0, 1)

        # Age (Left Column)
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Enter your age")
        self.grid_layout.addWidget(QLabel("Age:"), 1, 0)
        self.grid_layout.addWidget(self.age_input, 1, 1)

        # Race and Ethnicity (Right Column)
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
        self.grid_layout.addWidget(QLabel("Race & Ethnicity:"), 0, 2)
        self.grid_layout.addWidget(self._wrap_in_group("Race & Ethnicity", self.race_ethnicity_layout), 0, 3)

        # Hand Preference (Right Column)
        self.hand_pref_group = QButtonGroup(self)
        self.hand_pref_layout = QVBoxLayout()
        self.hand_pref_options = ["Left", "Right", "Any"]
        self.hand_pref_buttons = [QRadioButton(option) for option in self.hand_pref_options]
        for button in self.hand_pref_buttons:
            self.hand_pref_group.addButton(button)
            self.hand_pref_layout.addWidget(button)
        self.grid_layout.addWidget(QLabel("Hand Preference:"), 1, 2)
        self.grid_layout.addWidget(self._wrap_in_group("Hand Preference", self.hand_pref_layout), 1, 3)

        # Ear Preference (Left Column)
        self.ear_pref_group = QButtonGroup(self)
        self.ear_pref_layout = QVBoxLayout()
        self.ear_pref_options = ["Left", "Right", "Any"]
        self.ear_pref_buttons = [QRadioButton(option) for option in self.ear_pref_options]
        for button in self.ear_pref_buttons:
            self.ear_pref_group.addButton(button)
            self.ear_pref_layout.addWidget(button)
        self.grid_layout.addWidget(QLabel("Ear Preference:"), 2, 0)
        self.grid_layout.addWidget(self._wrap_in_group("Ear Preference", self.ear_pref_layout), 2, 1)

        # Submit Button (Spanning Both Columns)
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
        self.submit_button.clicked.connect(self.save_data)
        self.grid_layout.addWidget(self.submit_button, 3, 0, 1, 4, alignment=Qt.AlignCenter)

        # Add grid layout to the main layout
        self.main_layout.addLayout(self.grid_layout)

    def _wrap_in_group(self, title, layout):
        group_box = QGroupBox(title)
        group_box.setLayout(layout)
        return group_box

    def save_data(self):
        """Validate and save demographic data to a JSON file."""
        # Validate gender
        gender = self.get_selected_button_text(self.gender_group, self.gender_other_input)
        if gender == "Not selected":
            self.show_error_message("Please select your gender.")
            return

        # Validate age
        age = self.age_input.text().strip()
        if not age.isdigit() or int(age) <= 0:
            self.show_error_message("Please enter a valid age.")
            return

        # Validate race and ethnicity
        race_ethnicity = self.get_selected_checkboxes(self.race_checkboxes, self.race_other_input)
        if not race_ethnicity:
            self.show_error_message("Please select at least one option for race and ethnicity.")
            return

        # Validate hand preference
        hand_pref = self.get_selected_button_text(self.hand_pref_group)
        if hand_pref == "Not selected":
            self.show_error_message("Please select your hand preference.")
            return

        # Validate ear preference
        ear_pref = self.get_selected_button_text(self.ear_pref_group)
        if ear_pref == "Not selected":
            self.show_error_message("Please select your ear preference.")
            return

        # If all validations pass, save the data
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
        os.makedirs(participant_folder, exist_ok=True)
        json_file = os.path.join(participant_folder, "demographic.json")
        with open(json_file, "w") as f:
            json.dump(demographic_data, f, indent=4)

        print("Demographic data saved successfully!")
        self.submitted.emit()

    def show_error_message(self, message):
        """Show an error message in a message box."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.exec()

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
