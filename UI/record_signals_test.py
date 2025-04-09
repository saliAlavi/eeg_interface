from record_signals import *

recorder = Recorder({
            'save_dir': trial_folder,  # Save EEG and gaze data in trial-specific folder
            'sr_eeg': 500,
            'print_every': 1,
            'verbose': True
        })
