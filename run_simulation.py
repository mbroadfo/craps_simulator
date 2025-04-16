from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from craps.statistics import Statistics
from craps.simulation_runner import simulate_single_session
from simulation_utils import get_dynamic_worker_count
from craps.simulation_report import simulation_report
import pickle
import os

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
            for future in tqdm(
                as_completed(futures),
                total=self.num_sessions,
                desc="Running Simulations",
                unit="session",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} • {rate_fmt}]",
            ):
                result = future.result()
                self.stats_results.append(result)
        
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
    worker_count = get_dynamic_worker_count(target_utilization=0.80)
    sim = SimulationManager(num_sessions=100000, max_workers=worker_count)
    sim.run_simulations()
    sim.save_results()
    simulation_report("output/aggregated_stats.pkl")
