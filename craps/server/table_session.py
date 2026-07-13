"""One live table: a TableRunner driven as an asyncio task (D4).

The engine stays synchronous — ``roll_once()`` is called directly from
the drive coroutine (a roll is microseconds of CPU), with pacing via
``asyncio.sleep`` and pause/resume via an ``asyncio.Event`` gate. At
TURBO (0ms) the loop still yields once per roll so it can't starve the
server. The flat shooter count here executes the identical roll
sequence as TableRunner.run()'s nested loop.
"""
from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Union

from craps.edge import EdgeTracker
from craps.server.broadcaster import Broadcaster
from craps.statistics import Statistics
from craps.table_runner import LineupConfig, TableRunner


class TableSession:
    def __init__(
        self,
        table_id: str,
        players: LineupConfig,
        house_rules: Optional[Dict[str, Any]] = None,
        roll_delay_ms: int = 0,
        max_shooters: int = 10,
        max_rolls: Optional[int] = None,
        dice_seed: Optional[int] = None,
        record: bool = True,
        sessions_dir: Union[str, Path] = "sessions",
    ) -> None:
        self.table_id = table_id
        self.roll_delay_ms = roll_delay_ms
        self.state = "created"  # created → running ⇄ paused → finished | stopped
        self.runner = TableRunner(
            table_id=table_id,
            players=players,
            house_rules=house_rules,
            max_shooters=max_shooters,
            max_rolls=max_rolls,
            dice_seed=dice_seed,
            record=record,
            sessions_dir=sessions_dir,
            quiet_mode=True,
        )
        self.broadcaster = Broadcaster(table_id)
        # Before start_session(), so SessionStarted reaches subscribers.
        self.broadcaster.subscribe(self.runner.engine.events)
        # D5 ledger: realized vs theoretical edge per player.
        self.edge_tracker = EdgeTracker(lambda: self.runner.engine.house_rules)
        self.edge_tracker.subscribe(self.runner.engine.events)
        self.stats: Optional[Statistics] = None
        self._task: Optional["asyncio.Task[None]"] = None
        self._gate = asyncio.Event()
        self._gate.set()

    def start(self) -> None:
        if self.state != "created":
            raise RuntimeError(f"table {self.table_id} is already {self.state}")
        self.runner.start_session()
        self.state = "running"
        self._task = asyncio.create_task(self._drive(), name=f"table:{self.table_id}")

    def pause(self) -> None:
        if self.state != "running":
            raise RuntimeError(f"table {self.table_id} is {self.state}, not running")
        self._gate.clear()
        self.state = "paused"

    def resume(self) -> None:
        if self.state != "paused":
            raise RuntimeError(f"table {self.table_id} is {self.state}, not paused")
        self.state = "running"
        self._gate.set()

    def step(self) -> None:
        """Let exactly one paced roll through, then stay paused.

        set()+clear() back-to-back is safe here because asyncio.Event
        wakes its waiter by resolving an already-created Future — the
        _drive loop's `await self._gate.wait()` still completes even
        though clear() runs (synchronously, no intervening await)
        right after set(). clear() only affects the *next* wait()
        call, which correctly blocks the loop again after this one
        roll — state stays "paused" throughout, matching that.
        """
        if self.state != "paused":
            raise RuntimeError(f"table {self.table_id} is {self.state}, not paused")
        self._gate.set()
        self._gate.clear()

    def set_pace(self, roll_delay_ms: int) -> None:
        self.roll_delay_ms = roll_delay_ms

    async def stop(self) -> None:
        """Cancel the drive task and finalize what was played."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
            self._gate.set()  # a paused table must wake to notice the cancel
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _drive(self) -> None:
        runner = self.runner
        rolls = 0
        shooters_done = 0
        try:
            while shooters_done < runner.max_shooters:
                await self._gate.wait()
                if self.roll_delay_ms:
                    await asyncio.sleep(self.roll_delay_ms / 1000)
                else:
                    await asyncio.sleep(0)  # TURBO still yields per roll
                summary = runner.roll_once()
                rolls += 1
                if summary.new_shooter_assigned:
                    shooters_done += 1
                if runner.max_rolls is not None and rolls >= runner.max_rolls:
                    break
            self.stats = runner.finalize()
            self.state = "finished"
        except asyncio.CancelledError:
            self.stats = runner.finalize()
            self.state = "stopped"
            raise
        finally:
            self.broadcaster.close()

    def snapshot(self) -> Dict[str, Any]:
        engine = self.runner.engine
        game_state = engine.game_state
        players = (
            engine.player_lineup.get_active_players_list()
            if engine.player_lineup
            else []
        )
        if players:
            seats = [
                {"name": p.name, "strategy": p.strategy_name, "bankroll": p.balance}
                for p in players
            ]
        else:
            # Not started yet: show the configured lineup, bankrolls unknown.
            seats = [
                {"name": name, "strategy": strategy, "bankroll": None}
                for name, strategy in (self.runner.players or [])
            ]
        return {
            "table_id": self.table_id,
            "state": self.state,
            "roll_delay_ms": self.roll_delay_ms,
            "next_seq": self.broadcaster.next_seq,
            "session_rolls": engine.stats.session_rolls if engine.stats else 0,
            "shooter_index": engine.shooter_index,
            "puck_on": game_state.puck_on if game_state else False,
            "point": game_state.point if game_state else None,
            "players": seats,
            "recording": str(self.runner.recorder.path) if self.runner.recorder else None,
        }

    def stats_snapshot(self) -> Dict[str, Any]:
        """Event-derived stats for the leaderboard/sparkline consumers."""
        stats = self.runner.engine.stats
        if stats is None:
            return {"table_id": self.table_id, "session_rolls": 0}
        return {
            "table_id": self.table_id,
            "session_rolls": stats.session_rolls,
            "total_amount_bet": stats.total_amount_bet,
            "total_amount_won": stats.total_amount_won,
            "total_amount_lost": stats.total_amount_lost,
            "player_stats": {
                name: {
                    "bets_settled": ps["bets_settled"],
                    "bets_won": ps["bets_won"],
                    "highest_bankroll": ps["highest_bankroll"],
                    "lowest_bankroll": ps["lowest_bankroll"],
                }
                for name, ps in stats.player_stats.items()
            },
            "bankroll_history": stats.bankroll_history,
            "at_risk_history": stats.at_risk_history,
            "edges": self.edge_tracker.snapshot(),
        }
