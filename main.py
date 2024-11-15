import tkinter as tk
from tkinter import messagebox
from pydub import AudioSegment
from pydub.playback import play
from PIL import Image, ImageTk
import csv
import threading
import os
import pandas as pd

# Function to play audio with a specified volume
def play_audio(file_path, volume):
    audio = AudioSegment.from_file(file_path)
    adjusted_audio = audio + volume  # Adjust the volume
    play(adjusted_audio)

# Main application class
class AudioGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Playback GUI")
        self.current_step = 0
        self.audio_channels = []

        # Load data from CSV file
        csv_file="audio_instructions.csv"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_file)
        self.load_data(filepath)

        # Display initial instructions
        self.display_initial_instructions()

    def load_data(self, csv_file):
        # Load CSV data for instructions, audio paths, volumes, and images
        self.data = []
        try:
            self.data=pd.read_csv(csv_file)
            
            # with open(csv_file, newline='') as file:
                
                # reader = csv.DictReader(file, delimiter=',')
                # for row in reader:
                #     print(row)
                #     print(row['audio_path_1'])  # Access by column header instead of column number
                #     print(row['image_path'])

                # reader = csv.reader(file)
                # print('here')
                # next(reader)
                # for row in reader:
                #     self.data.append({
                #         'instruction': row[0],
                #         'image_path': row[1],
                #         'audio_paths': row[2:8],
                #         'volumes': list(map(int, row[8:14]))
                #     })
        except Exception as e:
            messagebox.showerror("Error", f"Could not read CSV file: {e}")
            self.root.quit()

    def display_initial_instructions(self):
        # Create the initial instruction screen
        instruction_text = "Welcome to the Audio Playback GUI.\nPress 'Start' to begin."
        self.instruction_label = tk.Label(self.root, text=instruction_text, font=("Arial", 16), padx=20, pady=20)
        self.instruction_label.pack()

        # Start button to begin playback steps
        self.start_button = tk.Button(self.root, text="Start", font=("Arial", 14), command=self.next_step)
        self.start_button.pack(pady=10)

    def next_step(self):
        # Advance to the next step
        
        if self.current_step >= len(self.data):
            messagebox.showinfo("End", "All steps are completed.")
            self.root.quit()
            return

        # Clear previous widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Display new instructions, image, and play audio
        step_data = self.data.iloc[self.current_step]
        self.show_instruction(step_data['instruction'])
        self.show_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), step_data['image_path']))
        self.play_audio_channels([step_data[f'audio_path_{i}'] for i in range(6)], [step_data[f'volume_{i}'] for i in range(6)])

        # Next button to proceed to the next step
        self.next_button = tk.Button(self.root, text="Next", font=("Arial", 14), command=self.next_step)
        self.next_button.pack(pady=10)
        self.current_step += 1


    def show_instruction(self, instruction_text):
        # Display the instruction text for the current step
        self.instruction_label = tk.Label(self.root, text=instruction_text, font=("Arial", 16), padx=20, pady=20)
        self.instruction_label.pack()

    def show_image(self, image_path):
        # Display the image for the current step
        try:
            image = Image.open(image_path)
            image = image.resize((300, 300))  # Resize if necessary
            self.photo = ImageTk.PhotoImage(image)
            self.image_label = tk.Label(self.root, image=self.photo)
            self.image_label.pack()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {e}")

    def play_audio_channels(self, audio_paths, volumes):
        # Play audio files on separate threads to allow for simultaneous playback
        self.audio_threads = []
        for i in range(6):  # Assuming 6 channels as per your requirements
            if audio_paths[i]:  # If there's an audio path provided
                thread = threading.Thread(target=play_audio, args=(audio_paths[i], volumes[i]))
                thread.start()
                self.audio_threads.append(thread)

# Create the main application window
root = tk.Tk()
app = AudioGuiApp(root)
root.mainloop()
