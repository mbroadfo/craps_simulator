import pickle
from craps.statistics import Statistics

def summarize_simulation(path: str) -> None:
    with open(path, "rb") as f:
        sessions: list[Statistics] = pickle.load(f)

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
