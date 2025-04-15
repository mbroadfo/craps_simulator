import psutil
import multiprocessing

def get_dynamic_worker_count(target_utilization: float = 0.8) -> int:
    """
    Calculate a dynamic number of workers based on CPU cores and target utilization.
    Caps to the maximum allowed by Windows for ProcessPoolExecutor.

    :param target_utilization: Desired CPU usage (0.0 to 1.0)
    :return: Optimal number of workers
    """
    logical_cores = multiprocessing.cpu_count()
    adjusted_workers = int(logical_cores * target_utilization)

    # Windows has a hard cap of 61 workers for ProcessPoolExecutor
    return min(adjusted_workers, 61)
