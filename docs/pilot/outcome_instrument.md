# Functional-Communication Outcome (FCO) — instrument spec

**Leap 2 of the strategy:** measure what matters — real-world communicative
success — not a clinician test score. Implemented in
`src/outcomes/functional_communication.py`; used by the daily check-in
(`src/app/daily_checkin.py`) and the pilot ([PROTOCOL.md](PROTOCOL.md)).

> ⚠️ **Research instrument, not yet psychometrically validated.** The items
> below are a scaffold modeled on the communicative-participation
> construct. Before any score informs a clinical decision it requires
> validation (reliability, validity vs an anchored standard,
> responsiveness) — see §4. In the pilot the FCO is a feasibility/outcome
> signal, not a diagnostic.

## 1. Rationale

WAB-AQ and similar batteries measure *impairment* under clinician
administration; they are slow, coarse, and move little session-to-session
(RESEARCH_LOG #23). What changes a person's life is *participation* — being
able to say what they need in the situations they care about. The FCO
targets participation directly, is self-/caregiver-reportable in under a
minute, and is repeatable daily so it can serve as a continuous outcome and
as the closed-loop reward signal.

The construct deliberately mirrors validated communicative-participation
measures (the CPIB / ACOM family): items ask about *difficulty
participating in real communication situations*, not about linguistic
impairment.

## 2. Items

### Daily EMA (3 items, ~20 s) — captures day-to-day variation
Responses 0–4.

| id | prompt | direction |
|---|---|---|
| `ema_say` | Today, how well could you say what you wanted to say? | higher = better |
| `ema_breakdown` | Today, how often did your communication break down? | reverse (higher raw = worse) |
| `ema_limited` | Today, how much did communication trouble keep you from doing what you wanted? | reverse |

### Weekly communicative-participation composite (6 items) — situations people care about
Rated 0–3 difficulty (0 = not difficult … 3 = very difficult / cannot),
reverse-coded so the score reads higher = better function.

| id | situation |
|---|---|
| `cp_phone` | Talking on the phone |
| `cp_order` | Ordering or asking for something in a shop/café |
| `cp_stranger` | Having a conversation with someone you don't know |
| `cp_group` | Joining a group conversation |
| `cp_news` | Telling someone about something that happened to you |
| `cp_opinion` | Giving your opinion or making a point |

## 3. Scoring

All sub-scores normalize to **0–100, higher = better function**.
- `score_daily_ema` → mean of per-item (good/max), ×100, where
  good = raw for positive items, (max − raw) for reverse items.
- `score_weekly_participation` → same normalization over the 6 weekly items.
- `composite_fco(daily, weekly)` → weighted blend (default: weekly 0.6,
  daily 0.4 — weekly participation is the more stable, clinically anchored
  signal). Returns whichever is present if only one is.

Worked example (from `scripts/demo_daily_checkin.py`): daily {3,1,1} →
**75.0**; weekly {1,0,2,2,1,1} → **61.1**; composite → **66.7**.

Putting the FCO on the same 0–100 scale as the language-state estimate lets
the loop use `reward = Δ FCO` (or Δ state) interchangeably and lets us test
state↔function concurrent validity directly.

## 4. Validation plan (before clinical use)

1. **Reliability** — test–retest on stable days (ICC); internal consistency
   of the weekly composite (Cronbach's α).
2. **Validity** — concurrent correlation with a clinician-administered
   communicative-participation measure and with WAB-AQ; known-groups
   (severity strata) discrimination.
3. **Responsiveness** — sensitivity to change over the 8 weeks; minimal
   detectable change and (later) minimal clinically important difference.
4. **Accessibility/equivalence** — aphasia-friendly wording verified with
   people with aphasia; self- vs caregiver-report agreement; mode effects.

Until these are met, FCO scores are descriptive feasibility outputs only.

## 5. Caveats

- Self-report in aphasia can be affected by comprehension and
  metalinguistic awareness; caregiver corroboration is collected.
- The item set is provisional; the final set is fixed with the clinical PI
  and may adopt published, already-validated items in place of the
  scaffold above.
- The default composite weighting is a prior, to be re-estimated against an
  anchor during validation.
