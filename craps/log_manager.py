# File: .\craps\log_manager.py

import os
import logging

class LogManager:
    def __init__(self, output_folder="output", log_file='play_by_play.log'):
        self.output_folder = output_folder
        self.log_file = os.path.join(output_folder, log_file)
        self.ensure_output_folder_exists()
        self.configure_logging()

    def ensure_output_folder_exists(self):
        """Ensure the output folder exists. Create it if it doesn't."""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created output folder: {self.output_folder}")

    def configure_logging(self):
        """Configure logging to write to the log file."""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(message)s',
            encoding='utf-8'
        )

    def delete_log_file(self):
        """Delete the log file if it exists."""
        if os.path.exists(self.log_file):
            # Close all logging handlers to release the file
            for handler in logging.root.handlers[:]:
                handler.close()
                logging.root.removeHandler(handler)
            os.remove(self.log_file)
            print(f"Deleted existing log file: {self.log_file}")
            # Reconfigure logging after deleting the file
            self.configure_logging()