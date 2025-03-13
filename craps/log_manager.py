import os
import logging

class LogManager:
    """Handles log file management."""

    def __init__(self, output_folder: str = "output", log_file: str = "simulation.log") -> None:
        """
        Initialize the LogManager.

        :param output_folder: The directory where log files will be stored.
        :param log_file: The name of the log file.
        """
        self.output_folder: str = output_folder
        self.log_file: str = os.path.join(output_folder, log_file)
        self.ensure_output_folder_exists()
        self.configure_logging()

    def ensure_output_folder_exists(self) -> None:
        """Ensure the output folder exists. Create it if it doesn't."""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created output folder: {self.output_folder}")

    def configure_logging(self) -> None:
        """Set up logging to write to the log file."""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def delete_log_file(self) -> None:
        """Delete the log file if it exists."""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
