# Craps Simulator

[![CI](https://github.com/mbroadfo/craps_simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/mbroadfo/craps_simulator/actions/workflows/ci.yml)

A craps simulation engine for testing betting strategies at scale — run a
single interactive session or 100k+ parallel bot sessions and compare
realized results against theoretical house edge.

- **16 betting strategies** (Pass Line, Iron Cross, 3-Point Molly/Dolly,
  regression systems, ATS, and more) driven by a shared strategy contract
- **RulesEngine** with full payout tables and bet-validity rules
- **FastAPI layer** for driving sessions over HTTP
- Statistics, play-by-play logs, roll history capture/replay, and
  bankroll visualization

## Setup (Windows / PowerShell)

Requires Python 3.11+ (developed on 3.13).

```powershell
git clone https://github.com/mbroadfo/craps_simulator.git
cd craps_simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Verify the install:

```powershell
pytest tests/ -q     # full test suite
mypy craps           # type check
```

Both must pass before committing — CI runs the same two commands on
Windows and Ubuntu for every push and pull request to `master`.

## Running

Interactive single session (players configured in `config.py`):

```powershell
python main.py
```

Bulk simulation (parallel sessions, aggregated report):

```powershell
python run_simulation.py --sessions 1000
```

Outputs (statistics report, roll history CSV, bankroll chart) land in
`output/`.

## Project layout

| Path | Purpose |
|------|---------|
| `craps/` | Engine, game state, table, bets, rules |
| `craps/strategies/` | The strategy library |
| `craps/api/` | FastAPI session/game endpoints |
| `tests/` | Unit + API tests |
| `config.py` | Active players, house rules, dice test patterns |
| `PHASE1_BRIEF.md` | Current modernization plan (event-sourced core) |
