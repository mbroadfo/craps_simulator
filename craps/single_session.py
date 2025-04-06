from typing import List, Optional, Any
from config import HOUSE_RULES
from craps.dice import Dice
from craps.statistics import Statistics
from craps.house_rules import HouseRules
from craps.log_manager import LogManager
from craps.session_initializer import InitializeSession
from craps.rules_engine import RulesEngine
from craps.play_by_play import PlayByPlay
from craps.player_setup import SetupPlayers
from craps.lineup import PlayerLineup
from craps.statistics_report import StatisticsReport
from craps.view_log import InteractiveLogViewer
from craps.visualizer import Visualizer
import os

def run_single_session(
    house_rules: Optional[HouseRules] = None,
    strategies: Optional[List[Any]] = None,
    initial_bankroll: Optional[int] = 500, 
    num_shooters: Optional[int] = 10, 
    roll_history_file: Optional[str] = None) -> Statistics:
    """
    Run a single session of craps and log the roll history.
    """
    # ✅ Set the house_rules
    if house_rules is None:
        house_rules = HouseRules(HOUSE_RULES)

    # Set dice mode
    dice = Dice(roll_history_file) if roll_history_file and os.path.exists(roll_history_file) else Dice()

    # ✅ Initialize session-level objects
    rules_engine = RulesEngine()
    play_by_play = PlayByPlay()
    log_manager = LogManager()
    player_lineup = PlayerLineup(house_rules, None, play_by_play, rules_engine)

    # ✅ Initialize players via SetupPlayers
    strategies = strategies or []
    players = SetupPlayers().setup()

    # ✅ Validate players exist
    if not players:
        play_by_play.clear_play_by_play_file()
        play_by_play.write("⚠️ No active players configured. Exiting session early.")
        return Statistics(
            table_minimum=house_rules.table_minimum,
            num_shooters=num_shooters or 10,
            num_players=0
        )
    
    # ✅ Assign player strategies
    player_lineup.assign_strategies(players)
    
    # ✅ Initialize the Session
    session_initializer = InitializeSession(
        session_mode="live",
        house_rules=house_rules,
        play_by_play=play_by_play,
        log_manager=log_manager,
        rules_engine=rules_engine,
        player_lineup=player_lineup
    )
    
    session_data = session_initializer.prepare_session(
        num_shooters or 10,  # ✅ Default if None
        len(strategies or [])  # ✅ Safe check for None
    )

    if session_data is None:
        raise RuntimeError("Failed to initialize session.")

    house_rules, table, roll_history_manager, log_manager, play_by_play, stats, game_state = session_data
    
    # ✅ Set num_players now that players are loaded
    stats.num_players = len(players)

    # ✅ Initialize bankroll history
    stats.initialize_bankroll_history(players)

    # ✅ Initialize roll history
    roll_history = []

    # ✅ Initialize player stats...   
    stats.initialize_player_stats(players)


    # ✅ Simulate shooters
    if num_shooters is None:
        num_shooters = 10

    for shooter_num in range(1, num_shooters + 1):
        player_index = (shooter_num - 1) % len(players)  # ✅ Safe calculation
        shooter = players[player_index]

        # Assign new shooter via GameState
        game_state.assign_new_shooter(shooter, shooter_num)

        while True:
            # Allow all players to place bets
            play_by_play.write(f"  ---------- Place Your Bets! -------------")
            for player in players:
                bets = player.betting_strategy.place_bets(game_state, player, table)
                if bets:
                    player.place_bet(bets, table, game_state.phase, play_by_play)

            # Roll the dice and resolve bets
            outcome = dice.roll()  # Now returns Tuple[int, int]
            total = sum(outcome)
            stats.update_rolls(total=total, table_risk=table.total_risk())
            stats.update_shooter_stats(shooter)

            # Log the roll
            roll_message = f"  🎲 Roll #{stats.session_rolls} → {outcome} = {total}"
            play_by_play.write(roll_message)

            # Log the roll to the history
            roll_history.append({
                "shooter_num": shooter_num,
                "roll_number": stats.session_rolls,
                "dice": outcome,
                "total": total,
                "phase": game_state.phase,
                "point": game_state.point
            })

            # Check bets on the table
            table.check_bets(outcome, game_state.phase, game_state.point)

            # Settle resolved bets & update stats
            resolved_bets = table.settle_resolved_bets()
            for bet in resolved_bets:
                stats.update_win_loss(bet)
            
            # 🧼 Remove winning bets that must come down (contract or per house rules)
            for bet in resolved_bets:
                if bet.status == "won" and bet in table.bets:
                    if bet.is_contract_bet or not house_rules.leave_winning_bets_up:
                        table.bets.remove(bet)
                        
            # Update the game state
            previous_phase = game_state.phase
            state_message = game_state.update_state(outcome)
            play_by_play.write(state_message)
            
            # 💡 Adjust bets after resolution (if strategy supports it)
            for player in players:
                if hasattr(player.betting_strategy, "adjust_bets"):
                    player.betting_strategy.adjust_bets(game_state, player, table)

            # 🧼 For remaining Place/Buy/Lay bets, set status based on puck + house rules
            for bet in table.bets:
                if bet.bet_type == "Field":
                    bet.status = "active"
                elif bet.bet_type in ["Place", "Buy", "Lay"]:
                    if game_state.phase == "point" or house_rules.leave_bets_working:
                        bet.status = "active"
                    else:
                        bet.status = "inactive"
                elif bet.bet_type in ["Hop", "Hardways", "Proposition"]:
                    if bet.status == "won":
                        bet.status = "active"

            # 🛠️ Log current player bets
            for player in players:
                remaining_bets = [b for b in table.bets if b.owner == player]
                if remaining_bets:
                    summary = ", ".join(f"{b.bet_type} {b.number} (${b.amount} {b.status})" for b in remaining_bets)
                    play_by_play.write(f"  📊 {player.name}'s remaining bets: {summary}")

            # Update player bankrolls in statistics
            stats.update_player_bankrolls(players)

            # ✅ Handle "Point Made" (shooter stays)
            if previous_phase == "point" and total == game_state.point:
                game_state.clear_point()
                continue  # Shooter keeps shooting

            # ✅ Handle 7-Out (shooter ends)
            if previous_phase == "point" and total == 7:
                stats.record_seven_out()
                game_state.clear_shooter()  # Reset shooter status
                break  # Next shooter

    # ✅ Wrap up Session
    stats.roll_history = roll_history
    stats.update_player_stats(players)
    statistics_report = StatisticsReport()
    statistics_report.write_statistics(stats)
    
    # View the play-by-play log
    log_viewer = InteractiveLogViewer()
    log_viewer.view(play_by_play.play_by_play_file)
    
    # View the statistics report
    log_viewer = InteractiveLogViewer()
    log_viewer.view("output/statistics_report.txt")

    # Visualize player bankrolls (only if there are players and rolls)
    if stats.num_players == 0 or stats.session_rolls == 0:
        print("⚠️ No data to visualize — skipping charts.")
    else:
        visualizer = Visualizer(stats)
        visualizer.visualize_bankrolls()

    return stats
