import sys
from run_session import run_session

if __name__ == "__main__":
    # Simulate command-line arguments: --auto --history
    sys.argv += ["--auto", "--history"]
    run_session()
