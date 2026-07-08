"""D5: realized vs theoretical edge (Phase 2, Step 3 analytics).

Theoretical house edge per bet type, expressed **per amount bet at
resolution** (the wizardofodds "per bet resolved" convention) — the
honest weight for blending composite strategies: a player's theoretical
benchmark is the edge of each bet weighted by the amount they actually
had riding when bets resolved.

Everything is computed exactly with Fractions from first principles —
dice combinatorics and this table's own payout ratios — so the numbers
respond to house rules (field 2/12 multiples, vig timing) instead of
being folklore constants. Positive edge = expected player loss.

Realized edge streams from BetResolved: profit on wins (net of any
commission, since payouts already are), stake on losses. The leaderboard
delta realized − (−theoretical) converges to zero if the engine's math
is right — the wizardofodds-grade check, live on screen.
"""
from __future__ import annotations
from fractions import Fraction
from itertools import combinations
from typing import Callable, Dict, Iterable, Optional, Tuple, Union

from craps.events import BetResolved, EventBus
from craps.house_rules import HouseRules

Number = Optional[Union[int, Tuple[int, int]]]

#: Ways to roll each box total with two dice (7 kept separate: it is
#: the resolver in the before-seven probabilities).
WAYS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
ALL_WAYS = {**WAYS, 7: 6}

VIG = Fraction(1, 20)  # the 5% commission

TRUE_ODDS = {4: Fraction(2), 5: Fraction(3, 2), 6: Fraction(6, 5),
             8: Fraction(6, 5), 9: Fraction(3, 2), 10: Fraction(2)}
DONT_TRUE_ODDS = {4: Fraction(1, 2), 5: Fraction(2, 3), 6: Fraction(5, 6),
                  8: Fraction(5, 6), 9: Fraction(2, 3), 10: Fraction(1, 2)}
PLACE_ODDS = {4: Fraction(9, 5), 5: Fraction(7, 5), 6: Fraction(7, 6),
              8: Fraction(7, 6), 9: Fraction(7, 5), 10: Fraction(9, 5)}
PROP_ODDS = {2: Fraction(30), 3: Fraction(15), 7: Fraction(4),
             11: Fraction(15), 12: Fraction(30)}

SMALL_NUMBERS = (2, 3, 4, 5, 6)
TALL_NUMBERS = (8, 9, 10, 11, 12)


def p_before_seven(number: int) -> Fraction:
    """P(number rolls before a 7)."""
    return Fraction(WAYS[number], WAYS[number] + 6)


def p_all_before_seven(numbers: Iterable[int]) -> Fraction:
    """P(every listed total appears at least once before the first 7).

    Inclusion-exclusion over 'a 7 beats the whole subset':
    P = Σ_{T⊆S} (−1)^|T| · 6/(6 + ways(T)).
    Sanity anchor: S={6} → 1 − 6/11 = 5/11, the classic 6-before-7.
    """
    pool = list(numbers)
    total = Fraction(0)
    for size in range(len(pool) + 1):
        for subset in combinations(pool, size):
            blocked_ways = sum(WAYS[n] for n in subset)
            total += (-1) ** size * Fraction(6, 6 + blocked_ways)
    return total


def _one_roll_edge(p_win: Fraction, ratio: Fraction) -> Fraction:
    """One-roll bet: lose stake unless it hits at ratio-to-1."""
    return 1 - p_win * (ratio + 1)


def theoretical_edge(
    bet_type: str,
    number: Number = None,
    house_rules: Optional[HouseRules] = None,
) -> Optional[Fraction]:
    """House edge per amount bet at resolution; None if untabulated
    (callers must report such amounts as uncovered, never guess)."""
    vig_on_win = house_rules.vig_on_win if house_rules else True
    field_2 = house_rules.field_bet_payout_2 if house_rules else 2
    field_12 = house_rules.field_bet_payout_12 if house_rules else 3

    if bet_type in ("Pass Line", "Come"):
        return Fraction(7, 495)  # 1.4141%
    if bet_type in ("Don't Pass", "Don't Come"):
        return Fraction(27, 1980)  # 1.3636% (bar-12 pushes excluded)
    if bet_type.endswith("Odds"):
        return Fraction(0)  # free odds are free

    if bet_type == "Place" and isinstance(number, int):
        p = p_before_seven(number)
        return (1 - p) - p * PLACE_ODDS[number]

    if bet_type == "Buy" and isinstance(number, int):
        p = p_before_seven(number)
        ratio = TRUE_ODDS[number]
        if vig_on_win:
            return (1 - p) - p * (ratio - VIG)  # 5% of the buy, winners only
        return (1 - p) - p * ratio + VIG        # 5% of the buy, upfront

    if bet_type == "Lay" and isinstance(number, int):
        p = 1 - p_before_seven(number)
        ratio = DONT_TRUE_ODDS[number]
        if vig_on_win:
            return (1 - p) - p * ratio * (1 - VIG)  # 5% of the win, winners only
        return (1 - p) - p * ratio + ratio * VIG    # 5% of potential win, upfront

    if bet_type == "Field":
        # 16/36 ways win: 3,4,9,10,11 even money; 2 and 12 configurable.
        return Fraction(6 - field_2 - field_12, 36)

    if bet_type == "Hardways" and isinstance(number, int):
        easy_ways = 4 if number in (6, 8) else 2
        p = Fraction(1, 1 + easy_ways + 6)  # hard vs easy-or-seven
        ratio = Fraction(9) if number in (6, 8) else Fraction(7)
        return (1 - p) - p * ratio

    if bet_type == "Proposition" and isinstance(number, int):
        return _one_roll_edge(Fraction(ALL_WAYS[number], 36), PROP_ODDS[number])

    if bet_type == "Any Craps":
        return _one_roll_edge(Fraction(4, 36), Fraction(7))

    if bet_type == "Horn":
        # Per 4 units: 2/12 net +27 (1 way each), 3/11 net +12 (2 ways
        # each), else -4. EV = (27+27+24+24-30*4)/(36*4) = -1/8.
        return Fraction(1, 8)  # 12.5%

    if bet_type == "World":
        # Per 5 units: 2/12 net +26, 3/11 net +11, 7 pushes (6 ways),
        # else -5. EV = (26+26+22+22+0-24*5)/(36*5) = -2/15.
        return Fraction(2, 15)  # 13.33%

    if bet_type == "Hop" and isinstance(number, tuple):
        is_pair = number[0] == number[1]
        p = Fraction(1 if is_pair else 2, 36)
        return _one_roll_edge(p, Fraction(30) if is_pair else Fraction(15))

    if bet_type in ("All", "Tall", "Small"):
        targets = {
            "Small": SMALL_NUMBERS,
            "Tall": TALL_NUMBERS,
            "All": SMALL_NUMBERS + TALL_NUMBERS,
        }[bet_type]
        ratio = Fraction(175) if bet_type == "All" else Fraction(34)
        return 1 - p_all_before_seven(targets) * (ratio + 1)

    return None  # untabulated (e.g. Don't Place): report as uncovered


class EdgeTracker:
    """Event consumer keeping the D5 ledger per player.

    Realized: profit/loss over amount bet at resolution, straight from
    BetResolved. Theoretical: each resolved amount weighted by its bet's
    edge — composite strategies get an honest blended benchmark. Amounts
    whose bet type has no tabulated edge accumulate in `uncovered` and
    are excluded from the blend rather than guessed at.
    """

    def __init__(self, house_rules_provider: Callable[[], Optional[HouseRules]]) -> None:
        self._house_rules = house_rules_provider
        self.wagered: Dict[str, int] = {}
        self.pnl: Dict[str, int] = {}
        self.expected_loss: Dict[str, Fraction] = {}
        self.covered: Dict[str, int] = {}
        self.uncovered: Dict[str, int] = {}

    def subscribe(self, bus: EventBus) -> None:
        bus.subscribe(BetResolved, self._on_resolved)  # type: ignore[arg-type]

    def _on_resolved(self, e: BetResolved) -> None:
        if e.status not in ("won", "lost"):
            return  # pushes/returns are not resolutions of risk
        name = e.player_name
        self.wagered[name] = self.wagered.get(name, 0) + e.amount
        self.pnl[name] = self.pnl.get(name, 0) + (e.payout if e.status == "won" else -e.amount)

        edge = theoretical_edge(e.bet_type, e.number, self._house_rules())
        if edge is None:
            self.uncovered[name] = self.uncovered.get(name, 0) + e.amount
        else:
            self.covered[name] = self.covered.get(name, 0) + e.amount
            self.expected_loss[name] = self.expected_loss.get(name, Fraction(0)) + edge * e.amount

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        """Player-view percentages: negative = losing money, and
        realized − theoretical converges to zero as rolls climb."""
        result: Dict[str, Dict[str, float]] = {}
        for name, wagered in self.wagered.items():
            covered = self.covered.get(name, 0)
            realized = 100.0 * self.pnl.get(name, 0) / wagered if wagered else 0.0
            theoretical = (
                -100.0 * float(self.expected_loss.get(name, Fraction(0))) / covered
                if covered else 0.0
            )
            result[name] = {
                "wagered": wagered,
                "pnl": self.pnl.get(name, 0),
                "realized_edge_pct": realized,
                "theoretical_edge_pct": theoretical,
                "edge_delta_pct": realized - theoretical,
                "uncovered_wagered": self.uncovered.get(name, 0),
            }
        return result
