# File: .\craps\log_manager.py

import os
import logging
from colorama import Fore, Style

class LogManager:
    def __init__(self, output_folder="output", log_file='play_by_play.html'):
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
        """Configure logging to write to the HTML log file."""
        # Open the HTML file and write the initial HTML structure
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Craps Play-by-Play Log</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            color: #333;
            padding: 20px;
        }
        .log-entry {
            margin-bottom: 10px;
        }
        .red {
            color: red;
        }
        .green {
            color: green;
        }
        .yellow {
            color: #d4af37;
        }
        .cyan {
            color: cyan;
        }
        .magenta {
            color: magenta;
        }
    </style>
</head>
<body>
    <h1>Craps Play-by-Play Log</h1>
    <div id="log-entries">
""")

        # Configure logging to append to the HTML file
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

    def close_log_file(self):
        """Close the HTML log file and write the closing tags."""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("""
    </div>
</body>
</html>
""")

    @staticmethod
    def format_log_message(message):
        """
        Format the log message with HTML tags for color and symbols.
        
        :param message: The log message to format.
        :return: The formatted log message as HTML.
        """
        # Replace Colorama color codes with HTML tags
        message = message.replace(Fore.RED, '<span class="red">')
        message = message.replace(Fore.GREEN, '<span class="green">')
        message = message.replace(Fore.YELLOW, '<span class="yellow">')
        message = message.replace(Fore.CYAN, '<span class="cyan">')
        message = message.replace(Fore.MAGENTA, '<span class="magenta">')
        message = message.replace(Style.RESET_ALL, '</span>')

        # Wrap the message in a log entry div
        return f'<div class="log-entry">{message}</div>'