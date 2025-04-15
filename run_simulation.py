from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from craps.statistics import Statistics
from craps.simulation_runner import simulate_single_session


class SimulationManager:
    def __init__(self, num_sessions: int = 1000, max_workers: int = 4) -> None:
        self.num_sessions = num_sessions
        self.max_workers = max_workers
        self.stats_results: list[Statistics] = []

    def submit_simulations(self, executor: ProcessPoolExecutor):
        return [executor.submit(simulate_single_session) for _ in range(self.num_sessions)]

    def run_simulations(self) -> None:
        start_time = datetime.now()
        print(f"⏰ Starting {self.num_sessions} simulations with {self.max_workers} workers at {start_time.strftime('%H:%M:%S')}")

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
        print(f"🏁 Finished at {end_time.strftime('%H:%M:%S')} (⌛ Duration: {duration:.2f} seconds)")

    def save_results(self, path="output/aggregated_stats.pkl") -> None:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self.stats_results, f)
        print(f"💾 Saved {len(self.stats_results)} sessions to {path}")

if __name__ == "__main__":
    sim = SimulationManager(num_sessions=1000, max_workers=10)
    sim.run_simulations()
    sim.save_results()
