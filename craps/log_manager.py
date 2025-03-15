import logging
import os

class LogManager:
    """Handles logging for the game."""

    def __init__(self, log_file: str = "output/simulation.log") -> None:
        """Initialize the LogManager with file logging."""
        self.log_file = log_file

        # ✅ Set up logging to append instead of overwrite
        logging.basicConfig(
            filename=self.log_file,  # ✅ Logs to file
            filemode="a",  # ✅ "a" means append instead of delete
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
        )
        self.logger = logging.getLogger("CrapsSim")

    def log(self, message: str) -> None:
        """Log a message to the file and console."""
        self.logger.info(message)

    def delete_log_file(self) -> None:
        """No longer deletes the log file, just a placeholder."""
        pass  # ✅ No deletion, just appends to the existing file
