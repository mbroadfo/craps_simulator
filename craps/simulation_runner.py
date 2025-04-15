from craps.statistics import Statistics


def simulate_single_session() -> Statistics:
    from craps.craps_engine import CrapsEngine
    from craps.roll_history_manager import RollHistoryManager
    from config import NUM_SHOOTERS

    engine = CrapsEngine(quiet_mode=True)
    roll_mgr = RollHistoryManager()
    
    if not engine.setup_session(num_shooters=NUM_SHOOTERS, dice_mode="live"):
        raise RuntimeError("Failed to initialize session.")
    
    engine.add_players_from_config()
    engine.lock_session()
    engine.assign_next_shooter()

    for _ in range(NUM_SHOOTERS):
        while True:
            engine.accept_bets()
            outcome = engine.roll_dice()
            if engine.game_state is None:
                raise RuntimeError("Game state not initialized")
            prev_phase = engine.game_state.phase
            engine.resolve_bets(outcome)
            engine.refresh_bet_statuses()
            engine.log_player_bets()
            summary = engine.handle_post_roll(outcome, prev_phase)
            if summary.new_shooter_assigned:
                break

    if engine.stats is None:
        raise RuntimeError("Statistics not initialized.")
    if engine.roll_history_manager is None:
        raise RuntimeError("Roll history manager not initialized.")
    if engine.player_lineup is None:
        raise RuntimeError("Player lineup not initialized.")
    
    return engine.finalize_session(
        stats=engine.stats,
        dice_mode="live",
        roll_history=engine.roll_history,
        roll_history_manager=engine.roll_history_manager,
        play_by_play=engine.play_by_play,
        players=engine.player_lineup.get_active_players_list()
    )
