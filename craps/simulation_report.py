import pickle
from craps.statistics import Statistics
import matplotlib.pyplot as plt
from collections import Counter

def simulation_report(path: str) -> None:
    with open(path, "rb") as f:
        sessions: list[Statistics] = pickle.load(f)
    
    summarize_simulation(sessions)
    summarize_by_shooter(sessions)

def summarize_simulation(sessions: list[Statistics]) -> None:
    total_sessions = len(sessions)
    total_throws = sum(s.session_rolls for s in sessions)
    total_bet = sum(s.total_amount_bet for s in sessions)
    total_won = sum(s.total_amount_won for s in sessions)
    total_lost = sum(s.total_amount_lost for s in sessions)
    total_take = sum(s.house_take() for s in sessions)

    throws_per_session = total_throws / total_sessions if total_sessions else 0
    house_edge = (total_take / total_bet * 100) if total_bet else 0

    print("\n🎲 Simulation Summary")
    print("-" * 80)
    print(f"Total Sessions       : {total_sessions:,}")
    print(f"Total Throws         : {total_throws:,}")
    print(f"Throws per Session   : {throws_per_session:.2f}")
    print(f"Total Bet            : ${total_bet:,}")
    print(f"Total Won            : ${total_won:,}")
    print(f"Total Lost           : ${total_lost:,}")
    print(f"House Take           : ${total_take:,}")
    print(f"House Edge           : {house_edge:.3f}%")
    print("-" * 80)

def summarize_by_shooter(sessions: list[Statistics]) -> None:
    from collections import Counter

    print("\n📊 Shooter Outcome Summary")
    print("-" * 80)

    outcome_counter: dict[str, Counter] = {}
    shooter_net_results = []

    max_win = float('-inf')
    max_loss = float('inf')
    max_winner = ""
    max_loser = ""

    for stats in sessions:
        for shooter_result in stats.shooter_stats.values():
            for player, net in shooter_result.items():
                if player not in outcome_counter:
                    outcome_counter[player] = Counter()

                if net > 0:
                    outcome_counter[player]["won"] += 1
                elif net < 0:
                    outcome_counter[player]["lost"] += 1
                else:
                    outcome_counter[player]["push"] += 1

                shooter_net_results.append(net)

                if net > max_win:
                    max_win = net
                    max_winner = player
                if net < max_loss:
                    max_loss = net
                    max_loser = player

    print(f"📈 Shooter outcome histograms...")
    for player, counter in outcome_counter.items():
        print(f"{player:>12} →  Won: {counter['won']:>5}, Lost: {counter['lost']:>5}, Push: {counter['push']:>5}")

    plot_shooter_outcomes_bar(outcome_counter)
    
    print("-" * 80)
    print(f"🥇 Max won by a player in one shooter: {max_win:,} ({max_winner})")
    print(f"💀 Max lost by a player in one shooter: {max_loss:,} ({max_loser})")

    # Histogram
    plt.figure(figsize=(10, 6))
    plt.hist(shooter_net_results, bins=100, color='skyblue', edgecolor='black')
    plt.title("Histogram of Net Win/Loss per Shooter")
    plt.xlabel("Net Amount Won or Lost by a Player per Shooter")
    plt.ylabel("Frequency")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig("output/shooter_histogram.png")

import matplotlib.pyplot as plt

def plot_shooter_outcomes_bar(outcome_counter: dict[str, Counter]) -> None:
    print(f"📊 Generating shooter outcome bar chart...")
    for player, counts in outcome_counter.items():
        outcomes = ['Won', 'Lost', 'Push']
        values = [counts['won'], counts['lost'], counts['push']]
        total = sum(values)
        percentages = [v / total * 100 for v in values]

        plt.figure(figsize=(8, 2))
        bars = plt.barh(outcomes, percentages, color=["green", "red", "gray"])
        for bar, pct in zip(bars, percentages):
            width = bar.get_width()
            plt.text(width + 1, bar.get_y() + bar.get_height() / 2,
                     f"{width:.2f}%", va='center')

        plt.xlim(0, 100)
        plt.title(f"Shooter Outcomes for {player}")
        plt.xlabel("Percentage")
        plt.tight_layout()
        plt.savefig(f"output/{player.lower().replace(' ', '_')}_shooter_outcomes_bar.png")
