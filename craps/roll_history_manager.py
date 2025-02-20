# File: .\craps\roll_history_manager.py

import os
import csv

class RollHistoryManager:
    def __init__(self, output_folder="output", roll_history_file="single_session_roll_history.csv"):
        self.output_folder = output_folder
        self.roll_history_file = os.path.join(output_folder, roll_history_file)

    def ensure_output_folder_exists(self):
        """Ensure the output folder exists. Create it if it doesn't."""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created output folder: {self.output_folder}")

    def delete_roll_history_file(self):
        """Delete the roll history file if it exists."""
        if os.path.exists(self.roll_history_file):
            os.remove(self.roll_history_file)
            print(f"Deleted existing roll history file: {self.roll_history_file}")

    def save_roll_history(self, roll_history):
        """
        Save the roll history to a CSV file.
        
        :param roll_history: A list of dictionaries representing the roll history.
        """
        self.ensure_output_folder_exists()
        with open(self.roll_history_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["shooter_num", "roll_number", "dice", "total", "phase", "point"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the roll history
            for roll in roll_history:
                writer.writerow(roll)

        print(f"Roll history saved to: {self.roll_history_file}")

    def load_roll_history(self):
        """
        Load the roll history from a CSV file.
        
        :return: A list of dictionaries representing the roll history.
        """
        if not os.path.exists(self.roll_history_file):
            raise FileNotFoundError(f"Roll history file '{self.roll_history_file}' not found.")

        roll_history = []
        with open(self.roll_history_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert dice and total to integers
                row["roll_number"] = int(row["roll_number"])
                row["shooter_num"] = int(row["shooter_num"])
                row["dice"] = [int(die) for die in row["dice"].strip('[]').split(', ')]
                row["total"] = int(row["total"])
                roll_history.append(row)

        print(f"Roll history loaded from: {self.roll_history_file}")
        return roll_history

    def prepare_for_session(self, session_mode):
        """
        Prepare for the session based on the session mode.
        
        :param session_mode: The session mode ("live" or "history").
        :raises FileNotFoundError: If the roll history file is missing in history mode.
        """
        self.validate_session_mode(session_mode)
        self.ensure_output_folder_exists()

        if session_mode == "live":
            self.delete_roll_history_file()
            print("Running session in 'live' mode with random rolls.")
        elif session_mode == "history":
            if not os.path.exists(self.roll_history_file):
                raise FileNotFoundError(f"Roll history file '{self.roll_history_file}' not found. Please run in 'live' mode first.")
            print(f"Running session in 'history' mode using roll history from: {self.roll_history_file}")

    def validate_session_mode(self, session_mode):
        """
        Validate the session mode.
        
        :param session_mode: The session mode ("live" or "history").
        :raises ValueError: If the session mode is invalid.
        """
        if session_mode not in ["live", "history"]:
            raise ValueError(f"Invalid SESSION_MODE '{session_mode}'. Must be 'live' or 'history'.")

    def get_roll_history_file(self, session_mode):
        """
        Get the roll history file based on the session mode.
        
        :param session_mode: The session mode ("live" or "history").
        :return: The roll history file path if in "history" mode, otherwise None.
        """
        return self.roll_history_file if session_mode == "history" else None