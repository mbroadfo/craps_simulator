# File: .\craps\log_manager.py

import os
import logging

class LogManager:
    def __init__(self, log_file='play_by_play.log'):
        self.log_file = log_file
        self.configure_logging()

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