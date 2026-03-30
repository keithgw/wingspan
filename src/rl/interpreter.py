"""Analysis functions for interpreting LinearPolicy weights.

Most functions are pure (state in, data out). Exceptions are checkpoint
loading (reads .npz files from disk) and sample-state generation (creates
game instances). Display formatting and matplotlib visualization live in
train.py.
"""

import glob
import os
import re
from collections import namedtuple

import numpy as np

from src.rl.featurizer import (
    ACTION_INDEX,
    FEATURE_NAMES,
    NUM_FEATURES,
    NUM_SUB_FEATURES,
    OPTION_FEATURE_NAMES,
    featurize,
    featurize_option,
)
from src.rl.linear_policy import LinearPolicy, _softmax

# --- Data types ---

FeatureContribution = namedtuple("FeatureContribution", ["feature_name", "weight", "feature_value", "contribution"])
ActionBreakdown = namedtuple("ActionBreakdown", ["action_name", "total_score", "probability", "contributions"])
StrategyRule = namedtuple("StrategyRule", ["condition", "behavior", "magnitude", "feature_name", "action_name"])

# --- Human-readable labels for strategy summaries ---

FEATURE_LABELS = {
    "game_progress": "the game progresses",
    "food_supply": "food supply is high",
    "board_score": "board score is high",
    "board_count": "board is filling up",
    "hand_count": "holding many cards",
    "hand_max_points": "hand contains high-value birds",
    "hand_min_cost": "cheapest playable bird costs more",
    "can_play_bird": "a bird is playable",
    "hand_best_ratio": "hand has efficient birds (high pts/cost)",
    "turns_remaining": "many turns remain",
    "best_immediate_vp": "a high-VP bird is playable now",
    "affordable_bird_count": "many birds are affordable",
    "max_achievable_vp": "high VP is still achievable",
    "tray_max_points": "tray has high-value birds",
    "tray_best_ratio": "tray has efficient birds",
    "unseen_mean_ratio": "unseen cards have good efficiency",
    "prob_draw_better": "drawing could improve hand",
    "prob_draw_affordable": "many unseen cards are affordable",
    "draw_vp_upside": "drawing has VP upside over playing",
    "opponent_best_score": "best opponent is scoring well",
    "opponent_avg_food": "opponents have more food",
    "score_lead": "ahead in score",
}

ACTION_LABELS = {
    "play_a_bird": "play birds",
    "gain_food": "gain food",
    "draw_a_bird": "draw cards",
}

OPTION_FEATURE_LABELS = {
    "option_points": "bird's victory points",
    "option_cost": "bird's food cost",
    "option_ratio": "bird's points/cost efficiency",
    "option_affordable": "bird is affordable now",
    "option_turns_to_afford": "turns needed to afford bird",
    "option_playable_in_time": "bird can be played before game ends",
    "option_points_vs_opponent": "bird scores well vs opponents",
    "option_is_deck": "drawing from deck (unknown bird)",
}


# --- Weight inspection ---


def get_action_weight_table(policy):
    """Return action weights as a list of dicts, one per feature.

    Each dict: {"feature": str, "play_a_bird": float, "gain_food": float, "draw_a_bird": float}
    """
    table = []
    for i, fname in enumerate(FEATURE_NAMES):
        row = {"feature": fname}
        for action, j in ACTION_INDEX.items():
            row[action] = policy.weights[i, j]
        table.append(row)
    return table


def get_sub_weight_table(policy):
    """Return sub-decision weights as a list of dicts.

    Each dict: {"feature": str, "weight": float}
    """
    all_names = FEATURE_NAMES + OPTION_FEATURE_NAMES
    return [{"feature": name, "weight": policy.sub_weights[i]} for i, name in enumerate(all_names)]


def rank_features_by_action(policy, action_name):
    """Return features sorted by absolute weight magnitude for a given action.

    Returns list of (feature_name, weight) sorted descending by |weight|.
    """
    if action_name not in ACTION_INDEX:
        raise ValueError(f"Unknown action: {action_name}. Must be one of {list(ACTION_INDEX.keys())}")
    j = ACTION_INDEX[action_name]
    pairs = [(FEATURE_NAMES[i], policy.weights[i, j]) for i in range(NUM_FEATURES)]
    return sorted(pairs, key=lambda x: abs(x[1]), reverse=True)


# --- Feature importance ---


def compute_feature_importance(policy):
    """Compute overall importance of each state feature across all actions.

    Importance = sum of absolute weights across all 3 actions.
    Returns list of (feature_name, importance) sorted descending.
    """
    importance = np.sum(np.abs(policy.weights), axis=1)
    pairs = [(FEATURE_NAMES[i], float(importance[i])) for i in range(NUM_FEATURES)]
    return sorted(pairs, key=lambda x: x[1], reverse=True)


def compute_sub_feature_importance(policy):
    """Compute importance of each sub-decision feature.

    Returns list of (feature_name, abs_weight) sorted descending.
    """
    all_names = FEATURE_NAMES + OPTION_FEATURE_NAMES
    pairs = [(name, float(abs(policy.sub_weights[i]))) for i, name in enumerate(all_names)]
    return sorted(pairs, key=lambda x: x[1], reverse=True)


# --- Strategy summaries ---


def generate_strategy_rules(policy, threshold=0.5):
    """Generate human-readable strategy rules from weight analysis.

    Scans the weight matrix for significant patterns:
    - Preference shifts: a feature drives toward one action and away from another
    - Sub-decision priorities: option features with strong weights

    Returns list of StrategyRule sorted by magnitude descending.
    """
    rules = []

    # Action-level rules: for each feature, find the strongest preference shift
    for i, fname in enumerate(FEATURE_NAMES):
        weights_for_feature = {a: policy.weights[i, j] for a, j in ACTION_INDEX.items()}
        best_action = max(weights_for_feature, key=weights_for_feature.get)
        worst_action = min(weights_for_feature, key=weights_for_feature.get)
        spread = weights_for_feature[best_action] - weights_for_feature[worst_action]

        if spread >= threshold:
            condition = f"When {FEATURE_LABELS.get(fname, fname)}"
            behavior = f"prefers to {ACTION_LABELS[best_action]} over {ACTION_LABELS[worst_action]}"
            rules.append(
                StrategyRule(
                    condition=condition,
                    behavior=behavior,
                    magnitude=round(spread, 2),
                    feature_name=fname,
                    action_name=best_action,
                )
            )

    # Sub-decision rules: option-specific features (last 8 of sub_weights)
    for i, fname in enumerate(OPTION_FEATURE_NAMES):
        w = policy.sub_weights[NUM_FEATURES + i]
        if abs(w) >= threshold:
            label = OPTION_FEATURE_LABELS.get(fname, fname)
            behavior = f"values {label}" if w > 0 else f"avoids {label}"
            rules.append(
                StrategyRule(
                    condition="When choosing between birds",
                    behavior=behavior,
                    magnitude=round(abs(w), 2),
                    feature_name=fname,
                    action_name=None,
                )
            )

    return sorted(rules, key=lambda r: r.magnitude, reverse=True)


def format_strategy_summary(rules):
    """Convert strategy rules into a multi-line human-readable summary."""
    if not rules:
        return "No significant strategy patterns detected (try lowering the threshold)."

    lines = [f"Strategy Summary ({len(rules)} rules discovered)", ""]
    for i, rule in enumerate(rules, 1):
        lines.append(f"  {i:2d}. {rule.condition}: {rule.behavior} (strength: {rule.magnitude:.2f})")
    return "\n".join(lines)


# --- Decision traces ---


def trace_action_decision(policy, state):
    """Decompose the action scoring for a given game state.

    Traces all 3 canonical actions regardless of legality, showing
    per-feature contributions (weight * feature_value) to each action's score.

    Returns a list of ActionBreakdown sorted by probability descending.
    """
    features = featurize(state)
    all_logits = features @ policy.weights
    probs = _softmax(all_logits)

    breakdowns = []
    for action, j in ACTION_INDEX.items():
        contributions = []
        for i, fname in enumerate(FEATURE_NAMES):
            contributions.append(
                FeatureContribution(
                    feature_name=fname,
                    weight=float(policy.weights[i, j]),
                    feature_value=float(features[i]),
                    contribution=float(policy.weights[i, j] * features[i]),
                )
            )
        contributions.sort(key=lambda c: abs(c.contribution), reverse=True)
        breakdowns.append(
            ActionBreakdown(
                action_name=action,
                total_score=float(all_logits[j]),
                probability=float(probs[j]),
                contributions=contributions,
            )
        )

    return sorted(breakdowns, key=lambda b: b.probability, reverse=True)


def trace_sub_decision(policy, state, options):
    """Decompose the sub-decision scoring for bird options.

    Returns list of ActionBreakdown sorted by probability descending.
    """
    all_names = FEATURE_NAMES + OPTION_FEATURE_NAMES
    state_features = featurize(state)
    scores = []
    combined_list = []

    for option_name in options:
        option_features = featurize_option(state, option_name)
        combined = np.concatenate([state_features, option_features])
        combined_list.append(combined)
        scores.append(float(combined @ policy.sub_weights))

    logits = np.array(scores)
    probs = _softmax(logits)

    breakdowns = []
    for k, option_name in enumerate(options):
        contributions = []
        for i, fname in enumerate(all_names):
            contributions.append(
                FeatureContribution(
                    feature_name=fname,
                    weight=float(policy.sub_weights[i]),
                    feature_value=float(combined_list[k][i]),
                    contribution=float(policy.sub_weights[i] * combined_list[k][i]),
                )
            )
        contributions.sort(key=lambda c: abs(c.contribution), reverse=True)
        breakdowns.append(
            ActionBreakdown(
                action_name=option_name,
                total_score=float(logits[k]),
                probability=float(probs[k]),
                contributions=contributions,
            )
        )

    return sorted(breakdowns, key=lambda b: b.probability, reverse=True)


def create_sample_states(num_samples=3, seed=42):
    """Create deterministic sample GameStates for decision trace demonstrations."""
    import random

    from src.game import WingspanGame

    # Save caller's RNG state so we don't leak side effects
    py_state = random.getstate()
    np_state = np.random.get_state()

    try:
        states = []
        for i in range(num_samples):
            random.seed(seed + i)
            np.random.seed(seed + i)
            game = WingspanGame(num_players=2, num_turns=10)
            states.append(game.game_state)
        return states
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)


def generate_diverse_states(policy, num_candidates=200, seed=42):
    """Generate game states spanning confident to uncertain decisions.

    Plays partial games with random bots to create early/mid/late-game states,
    scores each by action-distribution entropy, and returns three representative
    states: most confident, moderate, and most uncertain.

    Returns list of dicts with keys: state, probs, entropy, label, turn.
    """
    import contextlib
    import io
    import random

    from src.game import WingspanGame

    # Save caller's RNG state so we don't leak side effects
    py_state = random.getstate()
    np_state = np.random.get_state()

    try:
        candidates = []
        num_turns = 10
        total_game_turns = num_turns * 2  # 2 players

        for i in range(num_candidates):
            random.seed(seed + i)
            np.random.seed(seed + i)

            with contextlib.redirect_stdout(io.StringIO()):
                game = WingspanGame(num_players=2, num_human=0, num_turns=num_turns)

                # Spread candidates across game stages
                turns_to_play = (i * total_game_turns) // num_candidates
                for _ in range(turns_to_play):
                    if game.game_state.is_game_over():
                        break
                    player = game.game_state.get_current_player()
                    action = player.request_action(game_state=game.game_state)
                    player.take_action(action=action, game_state=game.game_state)
                    game.game_state.end_player_turn(player=player)

            if game.game_state.is_game_over():
                continue

            state = game.game_state
            all_logits = featurize(state) @ policy.weights
            probs = _softmax(all_logits)
            entropy = float(-np.sum(probs * np.log(probs + 1e-10)))
            normalized = entropy / float(np.log(3))

            candidates.append({"state": state, "probs": probs, "entropy": normalized, "turn": state.game_turn})

        if not candidates:
            return []

        candidates.sort(key=lambda x: x["entropy"])
        n = len(candidates)

        return [
            {**candidates[0], "label": "Confident"},
            {**candidates[n // 2], "label": "Moderate"},
            {**candidates[-1], "label": "Uncertain"},
        ]
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)


def format_game_context(state):
    """Render a game state as a human-readable summary for decision traces."""
    player = state.get_current_player()
    hand = player.get_bird_hand().get_cards_in_hand()
    board = player.get_game_board()
    food = player.get_food_supply().amount
    tray_birds = state.get_tray().get_birds_in_tray()
    total_turns = state.num_turns * state.num_players
    progress = state.game_turn / total_turns if total_turns > 0 else 1.0

    lines = []
    lines.append(f"  Turn {state.game_turn}/{total_turns} ({progress:.0%} complete)")
    lines.append(
        f"  Food: {food}  |  Board: {board.get_score()} pts"
        f" ({len(board.get_birds())}/{board.capacity} slots)  |  Hand: {len(hand)} cards"
    )

    if hand:
        lines.append("")
        lines.append("  Hand:")
        for b in sorted(hand, key=lambda b: b.get_points(), reverse=True):
            playable = "*" if food >= b.get_food_cost() and not board.check_if_full() else " "
            lines.append(f"    {playable} {b.get_name():<30s} {b.get_points():>2d} pts, cost {b.get_food_cost()}")

    board_birds = board.get_birds()
    if board_birds:
        lines.append("")
        lines.append("  Board:")
        for b in board_birds:
            lines.append(f"      {b.get_name():<30s} {b.get_points():>2d} pts")

    if tray_birds:
        lines.append("")
        lines.append("  Tray:")
        for b in sorted(tray_birds, key=lambda b: b.get_points(), reverse=True):
            lines.append(f"      {b.get_name():<30s} {b.get_points():>2d} pts, cost {b.get_food_cost()}")

    opponents = [p for p in state.get_players() if p is not player]
    for opp in opponents:
        ob = opp.get_game_board()
        lines.append("")
        lines.append(
            f"  Opponent: {ob.get_score()} pts ({len(ob.get_birds())} birds), food: {opp.get_food_supply().amount}"
        )

    return "\n".join(lines)


def get_sub_decision_options(state):
    """Return playable birds and drawable options for the current player."""
    player = state.get_current_player()
    hand = player.get_bird_hand().get_cards_in_hand()
    food = player.get_food_supply().amount
    board = player.get_game_board()
    tray = state.get_tray()

    playable = [b.get_name() for b in hand if food >= b.get_food_cost() and not board.check_if_full()]
    drawable = tray.see_birds_in_tray() + ["deck"]

    return {"playable_birds": playable, "drawable_options": drawable}


# --- Weight evolution ---


def load_checkpoint_weights(models_dir, max_checkpoints=50):
    """Load weights from checkpoint files, subsampled to max_checkpoints.

    Returns dict with:
        "iterations": list[int]
        "action_weights": np.ndarray shape (N, NUM_FEATURES, num_actions)
        "sub_weights": np.ndarray shape (N, NUM_SUB_FEATURES)
    """
    pattern = os.path.join(models_dir, "policy_iter_*.npz")
    files = glob.glob(pattern)

    iter_re = re.compile(r"policy_iter_(\d+)\.npz$")
    entries = []
    for f in files:
        m = iter_re.search(f)
        if m:
            entries.append((int(m.group(1)), f))
    entries.sort(key=lambda x: x[0])

    if not entries:
        return {
            "iterations": [],
            "action_weights": np.empty((0, NUM_FEATURES, 3)),
            "sub_weights": np.empty((0, NUM_SUB_FEATURES)),
        }

    # Subsample to max_checkpoints evenly spaced entries
    if len(entries) > max_checkpoints:
        indices = np.round(np.linspace(0, len(entries) - 1, max_checkpoints)).astype(int)
        entries = [entries[i] for i in indices]

    iterations = []
    action_weights_list = []
    sub_weights_list = []

    for iteration, filepath in entries:
        policy = LinearPolicy.load(filepath)
        # Skip checkpoints with mismatched feature dimensions (e.g. old runs)
        if policy.weights.shape[0] != NUM_FEATURES:
            continue
        iterations.append(iteration)
        action_weights_list.append(policy.weights)
        sub_weights_list.append(policy.sub_weights)

    if not iterations:
        return {
            "iterations": [],
            "action_weights": np.empty((0, NUM_FEATURES, 3)),
            "sub_weights": np.empty((0, NUM_SUB_FEATURES)),
        }

    return {
        "iterations": iterations,
        "action_weights": np.stack(action_weights_list),
        "sub_weights": np.stack(sub_weights_list),
    }


def compute_weight_evolution(checkpoint_data, feature_name, action_name=None):
    """Extract the evolution of a single weight over training.

    If action_name is provided, extracts from the action weight matrix.
    If action_name is None, extracts from sub_weights.

    Returns dict with "iterations", "values", "feature_name", "action_name".
    """
    iterations = checkpoint_data["iterations"]

    if action_name is not None:
        if action_name not in ACTION_INDEX:
            raise ValueError(f"Unknown action: {action_name}")
        if feature_name not in FEATURE_NAMES:
            raise ValueError(f"Unknown feature: {feature_name}. Must be one of {FEATURE_NAMES}")
        fi = FEATURE_NAMES.index(feature_name)
        ai = ACTION_INDEX[action_name]
        values = checkpoint_data["action_weights"][:, fi, ai].tolist()
    else:
        all_names = FEATURE_NAMES + OPTION_FEATURE_NAMES
        if feature_name not in all_names:
            raise ValueError(f"Unknown feature: {feature_name}. Must be one of {all_names}")
        fi = all_names.index(feature_name)
        values = checkpoint_data["sub_weights"][:, fi].tolist()

    return {
        "iterations": iterations,
        "values": values,
        "feature_name": feature_name,
        "action_name": action_name,
    }
