"""Leap 2 — the outcome that matters: functional communication.

WAB-AQ is a slow, coarse clinician-administered proxy that barely moves
session-to-session (experiment #23). The pilot's primary endpoint is
*real-world communicative success* — can the person say what they need,
in the situations they care about. This module defines a lightweight,
self-/caregiver-reportable instrument and its scoring, designed to be
answered daily (a 3-item EMA) and weekly (a participation composite) on a
phone.

The construct deliberately mirrors validated communicative-participation
measures (CPIB / ACOM family): items ask about *difficulty participating
in real communication situations*, not about impairment. Scores are
normalised to 0–100 (higher = better function) so they sit on the same
scale as the language-state estimate and can serve as the closed-loop
reward (`reward = Δ functional score`) or the clinical endpoint.

NOTE: this is a research instrument scaffold. Real deployment requires
psychometric validation (reliability, validity vs an anchored standard,
responsiveness) before any scores drive clinical decisions — see
docs/pilot/outcome_instrument.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    item_id: str
    prompt: str
    max_score: int           # Likert top (responses 0..max_score)
    reverse: bool            # True if higher raw = worse function
    weight: float = 1.0


# Daily 3-item EMA — fast, repeatable, captures day-to-day variation.
DAILY_EMA: tuple[Item, ...] = (
    Item("ema_say", "Today, how well could you say what you wanted to say?",
         4, reverse=False),
    Item("ema_breakdown", "Today, how often did your communication break down?",
         4, reverse=True),
    Item("ema_limited", "Today, how much did communication trouble keep you "
         "from doing what you wanted?", 4, reverse=True),
)

# Weekly communicative-participation composite — situations people care about.
WEEKLY_PARTICIPATION: tuple[Item, ...] = (
    Item("cp_phone", "Talking on the phone", 3, reverse=True),
    Item("cp_order", "Ordering or asking for something in a shop/café", 3, reverse=True),
    Item("cp_stranger", "Having a conversation with someone you don't know", 3, reverse=True),
    Item("cp_group", "Joining a group conversation", 3, reverse=True),
    Item("cp_news", "Telling someone about something that happened to you", 3, reverse=True),
    Item("cp_opinion", "Giving your opinion or making a point", 3, reverse=True),
)


def _score_items(items: tuple[Item, ...], responses: dict[str, int]) -> float:
    """Normalise a set of Likert responses to 0–100 (higher = better)."""
    num = 0.0
    denom = 0.0
    for it in items:
        if it.item_id not in responses:
            continue
        raw = float(responses[it.item_id])
        good = (it.max_score - raw) if it.reverse else raw   # higher = better
        num += it.weight * (good / it.max_score)
        denom += it.weight
    if denom == 0:
        return float("nan")
    return 100.0 * num / denom


def score_daily_ema(responses: dict[str, int]) -> float:
    """Daily functional-communication score in 0–100."""
    return _score_items(DAILY_EMA, responses)


def score_weekly_participation(responses: dict[str, int]) -> float:
    """Weekly communicative-participation score in 0–100."""
    return _score_items(WEEKLY_PARTICIPATION, responses)


def composite_fco(daily: float | None = None,
                  weekly: float | None = None,
                  daily_weight: float = 0.4) -> float:
    """Functional-Communication Outcome: blend daily EMA + weekly participation.

    When only one is present, returns it. When both, a weighted average
    (weekly participation carries more weight as the more stable, clinically
    anchored signal).
    """
    vals = []
    weights = []
    if daily is not None and daily == daily:        # not NaN
        vals.append(daily); weights.append(daily_weight)
    if weekly is not None and weekly == weekly:
        vals.append(weekly); weights.append(1.0 - daily_weight)
    if not vals:
        return float("nan")
    total = sum(weights)
    return sum(v * w for v, w in zip(vals, weights)) / total
