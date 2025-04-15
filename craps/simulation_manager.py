from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List
from craps.statistics import Statistics
from craps.simulation_runner import simulate_single_session
from tqdm import tqdm

class SimulationManager:
    def __init__(self, num_sessions: int = 1000, max_workers: int = 4) -> None:
        self.num_sessions = num_sessions
        self.max_workers = max_workers
        self.stats_results: List[Statistics] = []

    def run_simulations(self) -> None:

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(simulate_single_session) for _ in range(self.num_sessions)]
            for future in tqdm(as_completed(futures), total=self.num_sessions, desc="Running Simulations"):
                result = future.result()
                self.stats_results.append(result)
                
    def save_results(self, path: str="output/aggregated_stats.pkl") -> None:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self.stats_results, f)
        print(f"💾 Saved {len(self.stats_results)} sessions to {path}")
