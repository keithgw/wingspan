# Model Changelog

Performance history of trained Wingspan RL policies. Each version documents the feature set, training configuration, and evaluation results against a random baseline.

Evaluation protocol: 50 games alternating first/second player, opponent is `RandomPolicy`.

---

## v3 — Interaction + Polynomial Features

**Date:** 2026-03-30
**Git ref:** main (post-PR #96, #98)
**Baseline file:** `models/baselines/v3_linear_26features.npz`

### Features (26 state + 8 option)

Added 4 interaction/polynomial features from #92 that encode non-linear relationships the linear model cannot learn from raw features alone:

- `food_gap_for_best` — how much food needed to play the most expensive bird in hand
- `vp_at_stake` — VP gap between best bird in hand and best affordable bird (opportunity cost)
- `endgame_flag` — binary flag when 3 or fewer turns remain
- `urgency` — score gap to close divided by turns remaining

### Training

| Parameter | Value |
|-----------|-------|
| Iterations | 20,000 |
| Games/iteration | 100 |
| Learning rate | 0.01 |
| Turns/game | 10 |
| Workers | 14 (parallel, #95) |

### Evaluation vs Random

| Metric | Value |
|--------|-------|
| Win rate | 84.7% |
| Mean score | 14.0 |
| Mean opponent score | 8.4 |
| Mean score diff | +5.6 |

### Notes

Modest improvement over v2 (+1.1% win rate, +0.2 score diff). The new features ranked highly by importance: `urgency` was #1 overall, `endgame_flag` #5, `vp_at_stake` #8. The model learned intuitive strategies: play aggressively when behind (`urgency`), shift to playing birds in endgame (`endgame_flag`), gain food when holding expensive unaffordable birds (`vp_at_stake`). First model trained with parallel self-play (#95), reducing wall-clock training time ~7x.

---

## v2 — Strategic + Deck Composition Features

**Date:** 2026-03-30
**Git ref:** main (post-PR #94, pre-#92)
**Baseline file:** `models/baselines/v2_linear_22features.npz`

### Features (22 state + 8 option)

Added Tier 1 strategic calculations (turns remaining, best immediate VP, affordable bird count, greedy rollout of max achievable VP), Tier 2 deck composition awareness (unseen card stats, draw probabilities, draw upside), and opponent-relative features (best opponent score, avg opponent food, score lead).

Removed from v1: `tray_count`, `deck_remaining` (low signal).

### Training

| Parameter | Value |
|-----------|-------|
| Iterations | 21,075 |
| Games/iteration | 100 |
| Learning rate | 0.01 |
| Turns/game | 10 |

### Evaluation vs Random

| Metric | Value |
|--------|-------|
| Win rate | 83.6% |
| Mean score | 13.8 |
| Mean opponent score | 8.3 |
| Mean score diff | +5.4 |

### Notes

Major feature engineering pass. The greedy rollout (`max_achievable_vp`) and deck composition stats gave the model forward-looking awareness that v1 lacked.

---

## v1 — Initial Linear Policy

**Date:** 2026-03-29
**Git ref:** main (post-PR #89)
**Baseline file:** `models/baselines/v1_linear_16features.npz`

### Features (16 state + 8 option)

Baseline feature set: game progress, food supply, board score/count, hand stats (count, max points, min cost, can play, best ratio), tray stats (count, max points, best ratio), deck remaining, and opponent features (best score, avg food, score lead).

### Training

| Parameter | Value |
|-----------|-------|
| Iterations | 20,000 |
| Games/iteration | 100 |
| Learning rate | 0.01 |
| Turns/game | 10 |

### Evaluation vs Random

| Metric | Value |
|--------|-------|
| Win rate | 94.0% |
| Mean score | 13.5 |
| Mean opponent score | 7.1 |
| Mean score diff | +6.4 |

### Notes

First trained linear policy. High win rate partly reflects a simpler feature space that converges quickly. Score differential is strong but the model lacks strategic depth (no forward-looking features, no deck awareness).
