from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from craps.statistics import Statistics
from craps.simulation_runner import simulate_single_session
from simulation_utils import get_dynamic_worker_count
from craps.simulation_report import simulation_report
from craps.high_roller import export_high_roller_histories
import pickle
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Run craps simulations.")
    parser.add_argument("--sessions", type=int, default=100, help="Number of sessions to run (default: 100)")
    parser.add_argument("--mode", choices=["live", "history"], default="live", help="Dice mode")
    parser.add_argument("--quiet", action="store_true", help="Suppress logging output")
    return parser.parse_args()

class SimulationManager:
    def __init__(self, num_sessions: int = 1000, max_workers: int = 4) -> None:
        self.num_sessions = num_sessions
        self.max_workers = max_workers
        self.stats_results: list[Statistics] = []

    def submit_simulations(self, executor: ProcessPoolExecutor):
        return [executor.submit(simulate_single_session) for _ in range(self.num_sessions)]

    def run_simulations(self) -> None:
        start_time = datetime.now()
        print(f"⏰ Starting {self.num_sessions:,} simulations with {self.max_workers} workers at {start_time.strftime('%H:%M:%S')}")

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = self.submit_simulations(executor)
            session_counter = 0
            for future in tqdm(
                as_completed(futures),
                total=self.num_sessions,
                desc="Running Simulations",
                unit="session",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} • {rate_fmt}]",
            ):
                result = future.result()
                result.session_number = session_counter
                self.stats_results.append(result)
                session_counter += 1

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        minutes, seconds = divmod(int(duration), 60)
        print(f"🏁 Finished at {end_time.strftime('%H:%M:%S')} (⌛ Duration: {minutes:02d}:{seconds:02d})")

    def save_results(self, path="output/aggregated_stats.pkl") -> None:
        with open(path, "wb") as f:
            pickle.dump(self.stats_results, f)
        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"💾 Saved {len(self.stats_results):,} sessions to {path} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    args = parse_args()
    session_count = args.sessions

    # 🛑 Confirm session count
    print(f"You are about to run {session_count:,} simulation sessions.")
    proceed = input("Proceed? [Y/n]: ").strip().lower()
    if proceed not in ("", "y", "yes"):
        print("Aborted by user.")
        exit(0)

    worker_count = get_dynamic_worker_count(target_utilization=0.80)
    sim = SimulationManager(num_sessions=session_count, max_workers=worker_count)
    sim.run_simulations()
    sim.save_results()
    simulation_report("output/aggregated_stats.pkl")
    export_high_roller_histories(simulation_data={"sessions": sim.stats_results})
