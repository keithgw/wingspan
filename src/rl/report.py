"""Generate self-contained HTML analysis reports for trained policies."""

import base64
import io
import os
from datetime import date


def _fig_to_base64(fig):
    """Render a matplotlib figure to a base64-encoded PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    import matplotlib.pyplot as plt

    plt.close(fig)
    return f"data:image/png;base64,{encoded}"


def _html_table(headers, rows, align=None):
    """Build an HTML table string."""
    parts = ['<table class="report-table">', "<thead><tr>"]
    for i, h in enumerate(headers):
        a = align[i] if align else "left"
        parts.append(f'<th style="text-align:{a}">{h}</th>')
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for i, val in enumerate(row):
            a = align[i] if align else "left"
            parts.append(f'<td style="text-align:{a}">{val}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def generate_report(policy_path, output_path=None, models_dir="models"):
    """Generate a self-contained HTML report analyzing a trained policy.

    Args:
        policy_path: Path to a .npz policy file.
        output_path: Where to write the .html (default: alongside policy).
        models_dir: Directory with checkpoints for evolution analysis.

    Returns:
        Path to the generated report.
    """
    if not os.path.isfile(policy_path):
        raise FileNotFoundError(f"Policy file not found: {policy_path}")

    if output_path is None:
        output_path = os.path.join(os.path.dirname(policy_path) or ".", "policy_report.html")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    import matplotlib.pyplot as plt
    import seaborn as sns

    from src.rl.featurizer import ACTION_INDEX, FEATURE_NAMES, OPTION_FEATURE_NAMES
    from src.rl.interpreter import (
        compute_feature_importance,
        compute_weight_evolution,
        format_game_context,
        generate_diverse_states,
        generate_strategy_rules,
        get_sub_decision_options,
        load_checkpoint_weights,
        trace_action_decision,
        trace_sub_decision,
    )
    from src.rl.linear_policy import LinearPolicy

    sns.set_theme(style="whitegrid", font_scale=0.9)
    policy = LinearPolicy.load(policy_path)
    actions = list(ACTION_INDEX.keys())
    sign_palette = {"pos": "#2c7bb6", "neg": "#d7191c"}

    sections = []

    # ---- Section 1: Action Weights ----
    fig, axes = plt.subplots(1, 3, figsize=(16, 8), sharey=True)
    action_labels = [a.replace("_", " ").title() for a in actions]
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
    weights_img = _fig_to_base64(fig)

    sections.append(f"""<h2>1. Action Weights</h2>
<p>Each bar shows how strongly a feature pushes toward (positive, blue) or away from
(negative, red) an action. Features with large absolute weights are the primary decision
drivers for the learned policy.</p>
<img src="{weights_img}" alt="Action weights" style="width:100%;max-width:1200px">""")

    # ---- Section 2: Feature Importance ----
    importance = compute_feature_importance(policy)
    names, values = zip(*importance)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(list(names), list(values), color="#2c7bb6")
    ax.invert_yaxis()
    ax.set_title("Feature Importance (sum |weight| across actions)", fontweight="bold")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    importance_img = _fig_to_base64(fig)

    top5 = importance[:5]
    top5_text = ", ".join(f"**{n}** ({v:.2f})" for n, v in top5)

    sections.append(f"""<h2>2. Feature Importance</h2>
<p>Overall importance is the sum of absolute weights across all three actions. Features at the
top have the most influence on action selection, regardless of direction.</p>
<p>The top 5 features are: {top5_text}.</p>
<img src="{importance_img}" alt="Feature importance" style="width:100%;max-width:800px">""")

    # ---- Section 3: Strategy Rules ----
    rules = generate_strategy_rules(policy, threshold=0.3)

    if rules:
        rule_rows = []
        for i, rule in enumerate(rules, 1):
            rule_rows.append([str(i), rule.condition, rule.behavior, f"{rule.magnitude:.2f}"])
        rules_table = _html_table(
            ["#", "Condition", "Behavior", "Strength"],
            rule_rows,
            align=["right", "left", "left", "right"],
        )
    else:
        rules_table = "<p><em>No significant strategy patterns detected.</em></p>"

    sections.append(f"""<h2>3. Strategy Rules</h2>
<p>Human-readable rules extracted from significant weight patterns. Each rule describes a game
condition and the resulting action preference the policy has learned. Rules are sorted by
strength (weight spread between preferred and avoided actions).</p>
{rules_table}""")

    # ---- Section 4: Decision Traces ----
    samples = generate_diverse_states(policy, num_candidates=200, seed=42)
    trace_parts = []

    for si, sample in enumerate(samples):
        state = sample["state"]
        entropy = sample["entropy"]
        label = sample["label"]
        context = format_game_context(state)

        breakdowns = trace_action_decision(policy, state)

        # Action probability bar chart
        fig, ax = plt.subplots(figsize=(8, 3))
        bnames = [b.action_name.replace("_", " ").title() for b in breakdowns]
        bprobs = [b.probability for b in breakdowns]
        bcolors = ["#2c7bb6", "#F5A623", "#4CAF50"]
        ax.barh(bnames, bprobs, color=bcolors[: len(bnames)])
        ax.set_xlim(0, 1)
        ax.set_xlabel("Probability")
        ax.set_title(f"Sample {si + 1}: {label} (entropy: {entropy:.2f})", fontweight="bold")
        fig.tight_layout()
        trace_img = _fig_to_base64(fig)

        # Top contributions table
        top_action = breakdowns[0]
        contrib_rows = []
        for c in top_action.contributions[:8]:
            sign = "+" if c.contribution >= 0 else ""
            contrib_rows.append(
                [
                    c.feature_name,
                    f"{sign}{c.contribution:.3f}",
                    f"{c.weight:+.3f}",
                    f"{c.feature_value:.3f}",
                ]
            )
        contrib_table = _html_table(
            ["Feature", "Contribution", "Weight", "Value"],
            contrib_rows,
            align=["left", "right", "right", "right"],
        )

        # Sub-decision if applicable
        sub_html = ""
        options = get_sub_decision_options(state)
        if top_action.action_name == "play_a_bird" and options["playable_birds"]:
            sub_breakdowns = trace_sub_decision(policy, state, options["playable_birds"])
            sub_rows = [[sb.action_name, f"{sb.probability:.1%}", f"{sb.total_score:+.3f}"] for sb in sub_breakdowns]
            sub_html = "<h4>Sub-decision: which bird to play?</h4>" + _html_table(
                ["Bird", "Probability", "Score"], sub_rows, align=["left", "right", "right"]
            )
        elif top_action.action_name == "draw_a_bird":
            sub_breakdowns = trace_sub_decision(policy, state, options["drawable_options"])
            sub_rows = [[sb.action_name, f"{sb.probability:.1%}", f"{sb.total_score:+.3f}"] for sb in sub_breakdowns]
            sub_html = "<h4>Sub-decision: which bird to draw?</h4>" + _html_table(
                ["Option", "Probability", "Score"], sub_rows, align=["left", "right", "right"]
            )

        trace_parts.append(f"""<div class="trace-block">
<img src="{trace_img}" alt="Trace {si + 1}" style="width:100%;max-width:700px">
<pre class="game-context">{context}</pre>
<p>Top action: <strong>{top_action.action_name}</strong> ({top_action.probability:.1%}).
Top feature contributions:</p>
{contrib_table}
{sub_html}
</div>""")

    sections.append(
        """<h2>4. Decision Traces</h2>
<p>Three representative game states spanning confident, moderate, and uncertain decisions.
For each state, the chart shows the action probability distribution, followed by the game
context and the feature contributions driving the top action.</p>"""
        + "\n".join(trace_parts)
    )

    # ---- Section 5: Weight Evolution ----
    checkpoint_data = load_checkpoint_weights(models_dir, max_checkpoints=50)
    iterations = checkpoint_data["iterations"]

    if iterations:
        top_features = [name for name, _ in importance[:5]]

        fig, axes_evo = plt.subplots(len(top_features), 1, figsize=(10, 3 * len(top_features)), sharex=True)
        if len(top_features) == 1:
            axes_evo = [axes_evo]

        for idx, fname in enumerate(top_features):
            ax = axes_evo[idx]
            for aname in actions:
                evo = compute_weight_evolution(checkpoint_data, fname, aname)
                ax.plot(evo["iterations"], evo["values"], label=aname, linewidth=1.5)
            ax.axhline(y=0, color="gray", linewidth=0.5)
            ax.set_title(fname, fontweight="bold")
            ax.set_ylabel("Weight")
            ax.legend(fontsize=8)

        axes_evo[-1].set_xlabel("Training Iteration")
        fig.suptitle("Weight Evolution (top 5 features)", fontsize=14, fontweight="bold")
        fig.tight_layout()
        evo_img = _fig_to_base64(fig)

        evo_narrative = (
            f"Training ran for {iterations[-1]:,} iterations. "
            f"The chart below shows how the weights for the five most important features "
            f"evolved during training. Converging lines suggest stable learning; oscillation "
            f"may indicate competing gradients or noisy reward signals."
        )

        sections.append(f"""<h2>5. Weight Evolution</h2>
<p>{evo_narrative}</p>
<img src="{evo_img}" alt="Weight evolution" style="width:100%;max-width:900px">""")
    else:
        sections.append("""<h2>5. Weight Evolution</h2>
<p><em>No checkpoints found. Run training with <code>--save_every</code> to enable
evolution analysis.</em></p>""")

    # ---- Section 6: Sub-Decision Weights ----
    n_state = len(FEATURE_NAMES)
    option_weights = [
        (OPTION_FEATURE_NAMES[i], float(policy.sub_weights[n_state + i])) for i in range(len(OPTION_FEATURE_NAMES))
    ]
    option_weights.sort(key=lambda x: abs(x[1]), reverse=True)

    sub_rows = [[name, f"{w:+.4f}"] for name, w in option_weights]
    sub_table = _html_table(["Feature", "Weight"], sub_rows, align=["left", "right"])

    sections.append(f"""<h2>6. Sub-Decision Weights</h2>
<p>When the policy decides <em>which</em> bird to play or draw, these per-option feature
weights determine the selection. Positive weights favor birds with that attribute;
negative weights avoid them.</p>
{sub_table}""")

    # ---- Assemble HTML ----
    body = "\n".join(sections)
    n_features = policy.weights.shape[0]
    n_actions = policy.weights.shape[1]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Policy Analysis Report</title>
<style>
  body {{
    max-width: 900px;
    margin: 2em auto;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: #24292e;
    line-height: 1.6;
    padding: 0 1em;
  }}
  h1 {{ border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
  h2 {{ border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; margin-top: 2em; }}
  img {{ display: block; margin: 1em 0; }}
  .report-table {{
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 0.9em;
    width: 100%;
  }}
  .report-table th, .report-table td {{
    border: 1px solid #dfe2e5;
    padding: 6px 12px;
  }}
  .report-table th {{
    background-color: #f6f8fa;
    font-weight: 600;
  }}
  .report-table tr:nth-child(even) {{
    background-color: #f6f8fa;
  }}
  .trace-block {{
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 1em;
    margin: 1.5em 0;
    background: #fafbfc;
  }}
  .game-context {{
    background: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 4px;
    padding: 0.8em;
    font-size: 0.85em;
    overflow-x: auto;
  }}
  .meta {{ color: #586069; font-size: 0.9em; }}
</style>
</head>
<body>
<h1>Policy Analysis Report</h1>
<p class="meta">
  Generated from <code>{os.path.basename(policy_path)}</code> &mdash;
  {n_features} features, {n_actions} actions &mdash;
  {date.today().isoformat()}
</p>

{body}

<hr>
<p class="meta">Generated by <code>python -m src.train report</code></p>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
