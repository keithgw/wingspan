"""Generate analysis report notebooks for trained policies."""

import json
import os


def _md_cell(source):
    """Create a markdown notebook cell."""
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(source)}


def _code_cell(source, hidden=False):
    """Create a code notebook cell."""
    cell = {"cell_type": "code", "metadata": {}, "source": _lines(source), "outputs": [], "execution_count": None}
    if hidden:
        cell["metadata"]["jupyter"] = {"source_hidden": True}
    return cell


def _lines(text):
    """Split text into notebook-format line list (each line ends with \\n except last)."""
    lines = text.strip().split("\n")
    return [line + "\n" for line in lines[:-1]] + [lines[-1]]


def generate_report(policy_path, output_path=None, models_dir="models"):
    """Generate a Jupyter notebook analyzing a trained policy.

    Args:
        policy_path: Path to a .npz policy file.
        output_path: Where to write the .ipynb (default: alongside policy).
        models_dir: Directory with checkpoints for evolution analysis.

    Returns:
        Path to the generated notebook.
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(policy_path) or ".", "policy_report.ipynb")

    cells = []

    # --- Title and setup ---
    cells.append(
        _md_cell(f"""# Policy Analysis Report

Generated from `{policy_path}`.

This notebook provides a comprehensive analysis of the trained policy:
1. **Weight inspection** — What features drive each action?
2. **Feature importance** — Which features matter most?
3. **Strategy rules** — Human-readable summary of learned behavior
4. **Decision traces** — Step-by-step scoring for sample game states
5. **Weight evolution** — How weights changed during training

Run all cells to regenerate, or modify and explore interactively.""")
    )

    cells.append(
        _code_cell(
            f"""import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.rl.linear_policy import LinearPolicy
from src.rl.featurizer import FEATURE_NAMES, OPTION_FEATURE_NAMES, ACTION_INDEX
from src.rl.interpreter import (
    compute_feature_importance,
    compute_sub_feature_importance,
    generate_strategy_rules,
    format_strategy_summary,
    generate_diverse_states,
    format_game_context,
    trace_action_decision,
    trace_sub_decision,
    get_sub_decision_options,
    load_checkpoint_weights,
    compute_weight_evolution,
)

sns.set_theme(style="whitegrid", font_scale=0.9)
policy = LinearPolicy.load("{policy_path}")
print(f"Loaded policy: {{policy.weights.shape[0]}} features, {{policy.weights.shape[1]}} actions")""",
            hidden=True,
        )
    )

    # --- Section 1: Weights ---
    cells.append(
        _md_cell("""## 1. Action Weights

Each bar shows how strongly a feature pushes toward (positive) or away from (negative) an action.
Features with large absolute weights are the primary decision drivers.""")
    )

    cells.append(
        _code_cell("""actions = list(ACTION_INDEX.keys())
action_labels = [a.replace("_", " ").title() for a in actions]
sign_palette = {"pos": "#2c7bb6", "neg": "#d7191c"}

fig, axes = plt.subplots(1, 3, figsize=(16, 8), sharey=True)
for idx, (action, label) in enumerate(zip(actions, action_labels)):
    j = ACTION_INDEX[action]
    weights = [float(policy.weights[i, j]) for i in range(len(FEATURE_NAMES))]
    colors = [sign_palette["pos"] if w >= 0 else sign_palette["neg"] for w in weights]
    axes[idx].barh(FEATURE_NAMES, weights, color=colors)
    axes[idx].set_title(label, fontweight="bold")
    axes[idx].axvline(x=0, color="gray", linewidth=0.5)
    if idx > 0:
        axes[idx].tick_params(labelleft=False)
axes[0].invert_yaxis()
fig.suptitle("Action Weights by Feature", fontsize=14, fontweight="bold")
fig.tight_layout()
plt.show()""")
    )

    # --- Section 2: Importance ---
    cells.append(
        _md_cell("""## 2. Feature Importance

Overall importance = sum of |weight| across all 3 actions. Features at the top have the most
influence on action selection regardless of direction.""")
    )

    cells.append(
        _code_cell("""importance = compute_feature_importance(policy)
names, values = zip(*importance)

fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(list(names), list(values), color="#2c7bb6")
ax.invert_yaxis()
ax.set_title("Feature Importance (sum |weight| across actions)", fontweight="bold")
ax.set_xlabel("Importance")
fig.tight_layout()
plt.show()""")
    )

    # --- Section 3: Strategy rules ---
    cells.append(
        _md_cell("""## 3. Strategy Rules

Human-readable rules extracted from significant weight patterns. Each rule describes a condition
(feature state) and the resulting action preference.""")
    )

    cells.append(
        _code_cell("""rules = generate_strategy_rules(policy, threshold=0.3)
print(format_strategy_summary(rules))""")
    )

    # --- Section 4: Decision traces ---
    cells.append(
        _md_cell("""## 4. Decision Traces

Three representative game states (confident, moderate, uncertain) showing per-feature
score contributions for each action. This reveals *why* the policy makes each decision.""")
    )

    cells.append(
        _code_cell("""samples = generate_diverse_states(policy, num_candidates=200, seed=42)

for si, sample in enumerate(samples):
    state = sample["state"]
    entropy = sample["entropy"]
    label = sample["label"]

    print(f"{'=' * 70}")
    print(f"  Sample {si + 1}: {label} (entropy: {entropy:.2f})")
    print(f"{'=' * 70}")
    print(format_game_context(state))

    breakdowns = trace_action_decision(policy, state)
    print("\\n  Action Probabilities:")
    for b in breakdowns:
        bar = "#" * int(b.probability * 40)
        print(f"    {b.action_name:<14s}  prob: {b.probability:5.1%}  score: {b.total_score:+.3f}  {bar}")
        for c in b.contributions[:5]:
            sign = "+" if c.contribution >= 0 else ""
            print(f"      {sign}{c.contribution:.3f}  {c.feature_name:>22s}"
                  f"  (w={c.weight:+.3f} * v={c.feature_value:.3f})")
        print()

    # Sub-decision for top action
    top_action = breakdowns[0].action_name
    options = get_sub_decision_options(state)

    if top_action == "play_a_bird" and options["playable_birds"]:
        print("  Sub-Decision: Which bird to play?")
        sub_breakdowns = trace_sub_decision(policy, state, options["playable_birds"])
        for sb in sub_breakdowns:
            bar = "#" * int(sb.probability * 30)
            print(f"    {sb.action_name:<30s}  prob: {sb.probability:5.1%}  {bar}")
            for c in sb.contributions[:3]:
                sign = "+" if c.contribution >= 0 else ""
                print(f"      {sign}{c.contribution:.3f}  {c.feature_name:>26s}")
            print()

    elif top_action == "draw_a_bird":
        print("  Sub-Decision: Which bird to draw?")
        sub_breakdowns = trace_sub_decision(policy, state, options["drawable_options"])
        for sb in sub_breakdowns:
            bar = "#" * int(sb.probability * 30)
            print(f"    {sb.action_name:<30s}  prob: {sb.probability:5.1%}  {bar}")
            for c in sb.contributions[:3]:
                sign = "+" if c.contribution >= 0 else ""
                print(f"      {sign}{c.contribution:.3f}  {c.feature_name:>26s}")
            print()

    print()""")
    )

    # --- Section 5: Weight evolution ---
    cells.append(
        _md_cell("""## 5. Weight Evolution

How the top features' weights changed over training. Convergence (flat lines) suggests stable
learning; oscillation may indicate instability or competing gradients.""")
    )

    cells.append(
        _code_cell(f"""checkpoint_data = load_checkpoint_weights("{models_dir}", max_checkpoints=50)
iterations = checkpoint_data["iterations"]

if iterations:
    importance = compute_feature_importance(policy)
    top_features = [name for name, _ in importance[:5]]
    actions = list(ACTION_INDEX.keys())

    fig, axes = plt.subplots(len(top_features), 1, figsize=(10, 3 * len(top_features)), sharex=True)
    if len(top_features) == 1:
        axes = [axes]

    for idx, fname in enumerate(top_features):
        ax = axes[idx]
        for aname in actions:
            evo = compute_weight_evolution(checkpoint_data, fname, aname)
            ax.plot(evo["iterations"], evo["values"], label=aname, linewidth=1.5)
        ax.axhline(y=0, color="gray", linewidth=0.5)
        ax.set_title(fname, fontweight="bold")
        ax.set_ylabel("Weight")
        ax.legend(fontsize=8)

    axes[-1].set_xlabel("Training Iteration")
    fig.suptitle("Weight Evolution (top 5 features)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    plt.show()
else:
    print(f"No checkpoints found in {models_dir}")""")
    )

    # --- Section 6: Interactive exploration ---
    cells.append(
        _md_cell("""## 6. Interactive Exploration

Use the cells below to dig deeper. Modify parameters or add new cells to investigate
specific questions about the policy.

### What-if: Tweak a feature and see how action probabilities shift""")
    )

    cells.append(
        _code_cell("""from src.rl.featurizer import featurize
from src.rl.linear_policy import _softmax

# Pick a sample state and a feature to vary
sample_state = samples[1]["state"]  # moderate-certainty state
feature_to_vary = "food_supply"  # change this to explore other features
feature_idx = FEATURE_NAMES.index(feature_to_vary)

base_features = featurize(sample_state)
sweep_values = np.linspace(0, 1, 20)

action_names = list(ACTION_INDEX.keys())
prob_curves = {a: [] for a in action_names}

for val in sweep_values:
    modified = base_features.copy()
    modified[feature_idx] = val
    logits = modified @ policy.weights
    probs = _softmax(logits)
    for a in action_names:
        prob_curves[a].append(probs[ACTION_INDEX[a]])

fig, ax = plt.subplots(figsize=(8, 5))
for a in action_names:
    ax.plot(sweep_values, prob_curves[a], label=a.replace("_", " ").title(), linewidth=2)
ax.axvline(x=float(base_features[feature_idx]), color="gray", linestyle="--", alpha=0.5, label="Current value")
ax.set_xlabel(f"{feature_to_vary} (normalized)")
ax.set_ylabel("Action Probability")
ax.set_title(f"What-if: Varying {feature_to_vary}", fontweight="bold")
ax.legend()
ax.set_ylim(0, 1)
fig.tight_layout()
plt.show()""")
    )

    cells.append(
        _md_cell("""### Counterintuitive decisions

Find states where the policy's top action seems surprising.""")
    )

    cells.append(
        _code_cell("""# Find states where policy gains food despite having a playable bird
from src.rl.featurizer import featurize as _feat

surprises = []
for i in range(200):
    import random
    random.seed(i + 1000)
    np.random.seed(i + 1000)

    import contextlib, io
    from src.game import WingspanGame
    with contextlib.redirect_stdout(io.StringIO()):
        game = WingspanGame(num_players=2, num_human=0, num_turns=10)
        turns = (i * 20) // 200
        for _ in range(turns):
            if game.game_state.is_game_over():
                break
            p = game.game_state.get_current_player()
            a = p.request_action(game_state=game.game_state)
            p.take_action(action=a, game_state=game.game_state)
            game.game_state.end_player_turn(player=p)

    if game.game_state.is_game_over():
        continue

    features = _feat(game.game_state)
    can_play = features[FEATURE_NAMES.index("can_play_bird")]
    logits = features @ policy.weights
    probs = _softmax(logits)
    top_action = list(ACTION_INDEX.keys())[np.argmax(probs)]

    if can_play == 1.0 and top_action != "play_a_bird":
        surprises.append({
            "state": game.game_state,
            "top_action": top_action,
            "probs": {a: float(probs[j]) for a, j in ACTION_INDEX.items()},
            "turn": game.game_state.game_turn,
        })

print(f"Found {len(surprises)} states where policy skips a playable bird\\n")
for s in surprises[:3]:
    print(f"Turn {s['turn']}: chooses {s['top_action']}")
    for a, p in s["probs"].items():
        print(f"  {a:<14s} {p:.1%}")
    print(format_game_context(s["state"]))
    print()""")
    )

    # --- Build notebook ---
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12.0"},
        },
        "cells": cells,
    }

    with open(output_path, "w") as f:
        json.dump(notebook, f, indent=1)

    return output_path
