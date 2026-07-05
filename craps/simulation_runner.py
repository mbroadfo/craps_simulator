from craps.statistics import Statistics


def simulate_single_session() -> Statistics:
    from config import NUM_SHOOTERS
    from craps.table_runner import TableRunner

    runner = TableRunner(max_shooters=NUM_SHOOTERS, quiet_mode=True)
    return runner.run()
