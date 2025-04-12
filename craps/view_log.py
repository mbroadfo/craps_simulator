import subprocess
from abc import ABC, abstractmethod
import os
import sys

class LogViewer(ABC):
    """
    Abstract base class for log viewers.
    """

    @abstractmethod
    def view(self, log_file: str) -> None:
        """
        View the log file.
        
        :param log_file: Path to the log file.
        """
        pass


class InteractiveLogViewer(LogViewer):
    """
    Concrete class for interactive log viewing.
    """

    def view(self, log_file: str) -> None:
        """
        Open the log file interactively.
        
        :param log_file: Path to the log file.
        """
        # Check if the log file exists
        if not os.path.exists(log_file):
            print(f"Log file '{log_file}' not found.")
            return

        # Handle Windows and Unix-like systems differently
        if sys.platform == "win32":
            # Windows: Use Python to print the file contents
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        print(line, end='')
            except Exception as e:
                print(f"An error occurred while trying to view the log file: {e}")
        else:
            # Unix-like systems: Use `less -R`
            try:
                subprocess.run(['less', '-R', log_file])
            except FileNotFoundError:
                print("'less' command not found. Falling back to plain text viewing.")
                self._view_plain_text(log_file)
            except Exception as e:
                print(f"An error occurred while trying to view the log file: {e}")

    def _view_plain_text(self, log_file: str) -> None:
        """
        Fallback method to view the log file as plain text.
        
        :param log_file: Path to the log file.
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    print(line, end='')
        except Exception as e:
            print(f"An error occurred while trying to view the log file: {e}")


class PlainTextLogViewer(LogViewer):
    """
    Concrete class for plain text log viewing.
    """

    def view(self, log_file: str) -> None:
        """
        Print the log file to the console.
        
        :param log_file: Path to the log file.
        """

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    print(line, end='')
        except Exception as e:
            print(f"An error occurred while trying to view the log file: {e}")