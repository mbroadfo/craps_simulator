import os
import logging
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from craps.craps_engine import CrapsEngine


class PlayByPlay:
    def __init__(
        self,
        output_folder: str = "output",
        play_by_play_file: str = "play_by_play.txt",
        engine: Optional["CrapsEngine"] = None
    ) -> None:
        """
        Initialize the PlayByPlay writer.

        :param output_folder: The folder where the play-by-play file will be saved.
        :param play_by_play_file: The name of the play-by-play file.
        """
        self.engine = engine
        self.output_folder: str = output_folder
        self.play_by_play_file: str = os.path.join(output_folder, play_by_play_file)
        self.ensure_output_folder_exists()

    def ensure_output_folder_exists(self) -> None:
        """Ensure the output folder exists. Create it if it doesn't."""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created output folder: {self.output_folder}")

    def write(self, message: str) -> None:
        """
        Write a pre-formatted message (with embedded Colorama colors) to the play-by-play file.

        :param message: The message to write.
        """
        if getattr(self.engine, "quiet_mode", False):
            return
        with open(self.play_by_play_file, "a", encoding="utf-8") as file:
            file.write(message + "\n")

    def clear_play_by_play_file(self) -> None:
        """Clear the play-by-play file if it exists."""
        if os.path.exists(self.play_by_play_file):
            # Ensure the file is closed before attempting to delete it
            for handler in logging.root.handlers[:]:
                handler.close()
                logging.root.removeHandler(handler)
            os.remove(self.play_by_play_file)
            print(f"Deleted existing play-by-play file: {self.play_by_play_file}")
