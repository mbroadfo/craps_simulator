import os
from craps.single_session import run_single_session

def main():
    # Optional test pattern via environment variable
    pattern_name = None # "point_hit"

    # Run the single session
    stats = run_single_session(pattern_name=pattern_name)

if __name__ == "__main__":
    main()
