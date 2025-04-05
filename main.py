from colorama import init
from craps.single_session import run_single_session
from craps.view_log import InteractiveLogViewer
from craps.visualizer import Visualizer

def main():
    init()  # Initialize colorama for colored text

    # Run the single session and get the statistics
    stats, play_by_play = run_single_session()

    # Display statistics
    stats.print_statistics()
    stats.print_shooter_report()
    stats.print_player_statistics()

    # View the play-by-play log
    log_viewer = InteractiveLogViewer()
    log_viewer.view(play_by_play.play_by_play_file)

    # Visualize player bankrolls (only if there are players and rolls)
    if stats.num_players == 0 or stats.num_rolls == 0:
        print("⚠️ No data to visualize — skipping charts.")
    else:
        visualizer = Visualizer(stats)
        visualizer.visualize_bankrolls()

if __name__ == "__main__":
    main()
