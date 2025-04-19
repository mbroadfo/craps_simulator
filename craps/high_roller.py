import os
import csv
from typing import Any
from craps.statistics import Statistics


def export_high_roller_histories(simulation_data: dict[str, Any], output_dir: str = "output/high_rollers") -> None:
    os.makedirs(output_dir, exist_ok=True)
    best_sessions: dict[str, tuple[int, Statistics]] = {}

    for session in simulation_data["sessions"]:
        high_roller = getattr(session, "session_high_roller", None)
        if not high_roller:
            continue

        player_name, strategy_name, profit = high_roller

        if strategy_name not in best_sessions or profit > best_sessions[strategy_name][0]:
            best_sessions[strategy_name] = (profit, session)

    for strategy, (_, session) in best_sessions.items():
        file_name = f"high_roller_{strategy}_session_{getattr(session, 'session_number', 'unknown')}.csv"
        file_path = os.path.join(output_dir, file_name)

        with open(file_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["shooter_num", "roll_number", "dice", "total", "phase", "point"])
            for entry in session.roll_history:
                writer.writerow([
                    entry["shooter_num"],
                    entry["roll_number"],
                    entry["dice"],
                    entry["total"],
                    entry["phase"],
                    entry.get("point", "")
                ])
