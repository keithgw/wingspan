"""CLI for training, evaluating, and visualizing learned policies."""

import argparse
import csv
import os

from src.rl.evaluator import evaluate, evaluate_parallel
from src.rl.linear_policy import LinearPolicy
from src.rl.policy import RandomPolicy
from src.rl.self_play import SelfPlayRunner
from src.rl.trainer import train_batch

METRICS_FILENAME = "training_metrics.csv"
METRICS_FIELDS = [
    "iteration",
    "self_play_wins",
    "self_play_losses",
    "self_play_ties",
    "self_play_mean_reward",
    "eval_win_rate",
    "eval_tie_rate",
    "eval_mean_score",
    "eval_mean_opponent_score",
    "eval_mean_score_diff",
]


def _init_metrics_file(output_dir):
    """Create (or overwrite) the metrics CSV with headers. Return path."""
    path = os.path.join(output_dir, METRICS_FILENAME)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=METRICS_FIELDS)
        writer.writeheader()
    return path


def _ensure_metrics_file(output_dir):
    """Create the metrics CSV with headers if it doesn't exist. Return path."""
    path = os.path.join(output_dir, METRICS_FILENAME)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=METRICS_FIELDS)
            writer.writeheader()
    return path


def _get_last_iteration(metrics_path):
    """Read the last iteration number from the metrics CSV, or 0 if empty."""
    try:
        with open(metrics_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                return int(rows[-1]["iteration"])
    except (FileNotFoundError, KeyError):
        pass
    return 0


def _append_metrics(path, row):
    """Append one row to the metrics CSV."""
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=METRICS_FIELDS)
        writer.writerow(row)


def train(args):
    """Run the training loop, logging metrics to CSV."""
    os.makedirs(args.output_dir, exist_ok=True)

    if args.resume:
        latest_path = os.path.join(args.output_dir, "policy_latest.npz")
        if not os.path.exists(latest_path):
            print(f"No policy found at {latest_path}. Use --fresh to start from scratch.")
            return
        policy = LinearPolicy.load(latest_path)
        print(f"Resuming from {latest_path}")
        metrics_path = _ensure_metrics_file(args.output_dir)
        start_iteration = _get_last_iteration(metrics_path)
    else:
        policy = LinearPolicy()
        print("Starting with fresh policy")
        metrics_path = _init_metrics_file(args.output_dir)
        start_iteration = 0

    runner = SelfPlayRunner()
    baseline = RandomPolicy()
    use_parallel = args.workers > 1

    mode_str = f"{args.workers} workers" if use_parallel else "sequential"
    print(f"Training for {args.num_iterations} iterations, {args.games_per_iteration} games each ({mode_str})")
    print(f"Metrics will be saved to {metrics_path}\n")

    pool = None
    if use_parallel:
        from concurrent.futures import ProcessPoolExecutor

        pool = ProcessPoolExecutor(max_workers=args.workers)

    try:
        for iteration in range(start_iteration + 1, start_iteration + args.num_iterations + 1):
            # Collect experience via self-play
            if pool is not None:
                action_exps, sub_exps, stats = SelfPlayRunner.collect_experience_parallel(
                    policy, num_games=args.games_per_iteration, num_turns=args.num_turns, pool=pool
                )
            else:
                action_exps, sub_exps, stats = runner.collect_experience(
                    policy, num_games=args.games_per_iteration, num_turns=args.num_turns
                )

            # Train on collected experience
            train_batch(policy, action_exps, sub_exps, learning_rate=args.learning_rate)

            # Evaluate against random baseline
            if pool is not None:
                eval_results = evaluate_parallel(policy, num_games=args.eval_games, num_turns=args.num_turns, pool=pool)
            else:
                eval_results = evaluate(policy, baseline, num_games=args.eval_games, num_turns=args.num_turns)

            # Log metrics
            _append_metrics(
                metrics_path,
                {
                    "iteration": iteration,
                    "self_play_wins": stats["wins"],
                    "self_play_losses": stats["losses"],
                    "self_play_ties": stats["ties"],
                    "self_play_mean_reward": f"{stats['mean_reward']:.3f}",
                    "eval_win_rate": f"{eval_results['win_rate']:.3f}",
                    "eval_tie_rate": f"{eval_results['tie_rate']:.3f}",
                    "eval_mean_score": f"{eval_results['mean_score']:.1f}",
                    "eval_mean_opponent_score": f"{eval_results['mean_opponent_score']:.1f}",
                    "eval_mean_score_diff": f"{eval_results['mean_score_diff']:.1f}",
                },
            )

            print(
                f"Iter {iteration:3d} | "
                f"Self-play: {stats['wins']}W/{stats['losses']}L/{stats['ties']}T | "
                f"vs Random: {eval_results['win_rate']:.0%} win, "
                f"score diff {eval_results['mean_score_diff']:+.1f}"
            )

            # Save checkpoint
            if iteration % args.save_every == 0 or iteration == args.num_iterations:
                path = os.path.join(args.output_dir, f"policy_iter_{iteration}.npz")
                policy.save(path)
    finally:
        if pool is not None:
            pool.shutdown(wait=False)

    # Save final policy
    final_path = os.path.join(args.output_dir, "policy_latest.npz")
    policy.save(final_path)
    print(f"\nFinal policy saved to {final_path}")
    print(f"Training metrics saved to {metrics_path}")


def eval_policy(args):
    """Evaluate a trained policy against a baseline."""
    policy = LinearPolicy.load(args.policy_path)

    if args.opponent == "random":
        opponent = RandomPolicy()
        opponent_name = "Random"
    elif args.opponent == "mcts":
        from src.rl.policy import MCTSPolicy

        opponent = MCTSPolicy(num_simulations=args.num_simulations)
        opponent_name = f"MCTS ({args.num_simulations} sims)"

    print(f"Evaluating {args.policy_path} vs {opponent_name} over {args.eval_games} games\n")

    results = evaluate(policy, opponent, num_games=args.eval_games, num_turns=args.num_turns)

    print(f"Win rate:        {results['win_rate']:.1%}")
    print(f"Tie rate:        {results['tie_rate']:.1%}")
    print(f"Mean score:      {results['mean_score']:.1f}")
    print(f"Mean opp score:  {results['mean_opponent_score']:.1f}")
    print(f"Mean score diff: {results['mean_score_diff']:+.1f}")


def plot_metrics(args):
    """Plot training metrics from a CSV file."""
    import matplotlib.pyplot as plt

    metrics_path = os.path.join(args.metrics_dir, METRICS_FILENAME)
    if not os.path.exists(metrics_path):
        print(f"No metrics file found at {metrics_path}")
        print("Run 'train' first to generate metrics.")
        return

    # Read CSV
    iterations = []
    win_rates = []
    score_diffs = []
    with open(metrics_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            iterations.append(int(row["iteration"]))
            win_rates.append(float(row["eval_win_rate"]))
            score_diffs.append(float(row["eval_mean_score_diff"]))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Win rate
    ax1.plot(iterations, win_rates, "b-", linewidth=1.5)
    ax1.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="50% baseline")
    ax1.set_ylabel("Win Rate vs Random")
    ax1.set_ylim(0, 1)
    ax1.legend()
    ax1.set_title("Training Progress")
    ax1.grid(True, alpha=0.3)

    # Score difference
    ax2.plot(iterations, score_diffs, "r-", linewidth=1.5)
    ax2.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax2.set_xlabel("Training Iteration")
    ax2.set_ylabel("Mean Score Diff vs Random")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()

    if args.save:
        plot_path = os.path.join(args.metrics_dir, "training_progress.png")
        fig.savefig(plot_path, dpi=150)
        print(f"Plot saved to {plot_path}")
    else:
        plt.show()


def interpret_policy(args):
    """Inspect and interpret a trained policy."""
    from src.rl.featurizer import ACTION_INDEX, FEATURE_NAMES, OPTION_FEATURE_NAMES
    from src.rl.interpreter import (
        compute_feature_importance,
        compute_weight_evolution,
        format_game_context,
        format_strategy_summary,
        generate_diverse_states,
        generate_strategy_rules,
        get_sub_decision_options,
        load_checkpoint_weights,
        rank_features_by_action,
        trace_action_decision,
        trace_sub_decision,
    )

    policy = LinearPolicy.load(args.policy_path)
    output_dir = os.path.dirname(args.policy_path) or "."
    print(f"Loaded policy from {args.policy_path}\n")

    if args.mode == "weights":
        actions = list(ACTION_INDEX.keys())

        if args.action:
            ranked = rank_features_by_action(policy, args.action)
            print(f"Features ranked by weight for {args.action}:\n")
            for rank, (name, weight) in enumerate(ranked, 1):
                print(f"  {rank:2d}. {name:>24s}  {weight:+.4f}")
        else:
            _plot_weights(policy, actions, FEATURE_NAMES, OPTION_FEATURE_NAMES, output_dir, args.save)

    elif args.mode == "importance":
        action_imp = compute_feature_importance(policy)

        print("Feature Importance (action-level)\n")
        print(f"  {'Rank':>4s}  {'Feature':>24s}  {'Importance':>10s}")
        print(f"  {'----':>4s}  {'-' * 24:>24s}  {'-' * 10:>10s}")
        for rank, (name, imp) in enumerate(action_imp, 1):
            print(f"  {rank:4d}  {name:>24s}  {imp:10.3f}")

        _plot_importance(action_imp, output_dir, args.save)

    elif args.mode == "summary":
        rules = generate_strategy_rules(policy, threshold=args.threshold)
        print(format_strategy_summary(rules))

    elif args.mode == "trace":
        samples = generate_diverse_states(policy, num_candidates=args.num_samples, seed=args.seed)

        all_breakdowns = []
        for si, sample in enumerate(samples):
            state = sample["state"]
            entropy = sample["entropy"]
            label = sample["label"]

            print(f"{'=' * 70}")
            print(f"  Sample {si + 1}: {label} (entropy: {entropy:.2f})")
            print(f"{'=' * 70}")
            print(format_game_context(state))
            print()

            # Action-level trace
            breakdowns = trace_action_decision(policy, state)
            all_breakdowns.append(breakdowns)
            print("  Action Probabilities:")
            for b in breakdowns:
                bar = "#" * int(b.probability * 40)
                print(f"    {b.action_name:<14s}  prob: {b.probability:5.1%}  score: {b.total_score:+.3f}  {bar}")
                for c in b.contributions[:5]:
                    sign = "+" if c.contribution >= 0 else ""
                    print(
                        f"      {sign}{c.contribution:.3f}  {c.feature_name:>22s}"
                        f"  (w={c.weight:+.3f} * v={c.feature_value:.3f})"
                    )
                print()

            # Sub-decision trace for the top action
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

        if all_breakdowns:
            _plot_trace(all_breakdowns[0], output_dir, args.save)

    elif args.mode == "evolution":
        checkpoint_data = load_checkpoint_weights(args.models_dir, max_checkpoints=args.max_checkpoints)
        iterations = checkpoint_data["iterations"]

        if not iterations:
            print(f"No checkpoints found in {args.models_dir}")
            return

        print(f"Loaded {len(iterations)} checkpoints (iter {iterations[0]} to {iterations[-1]})\n")

        importance = compute_feature_importance(policy)
        top_features = [name for name, _ in importance[:5]]

        print("Weight Evolution (top 5 features by final importance)\n")
        for fname in top_features:
            print(f"  {fname}:")
            for aname in ACTION_INDEX:
                evo = compute_weight_evolution(checkpoint_data, fname, aname)
                print(f"    {aname:>14s}: {evo['values'][0]:+.3f} -> {evo['values'][-1]:+.3f}")
            print()

        features_to_plot = [args.feature] if args.feature else top_features
        _plot_evolution(checkpoint_data, features_to_plot, ACTION_INDEX, args.models_dir, args.save)


def _show_or_save(fig, output_dir, filename, save):
    """Display a figure interactively, or save to file with --save."""
    import matplotlib.pyplot as plt

    if save:
        plot_path = os.path.join(output_dir, filename)
        fig.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"\nPlot saved to {plot_path}")
    else:
        plt.show()


def _plot_weights(policy, actions, feature_names, option_feature_names, output_dir, save):
    """Two separate figures: faceted action weights and sub-decision option weights."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    sns.set_theme(style="whitegrid", font_scale=0.9)
    sign_palette = {"pos": "#2c7bb6", "neg": "#d7191c"}

    # --- Figure 1: Action weights (faceted) ---
    records = []
    action_labels = [a.replace("_", " ").title() for a in actions]
    for idx, label in enumerate(action_labels):
        for i, fname in enumerate(feature_names):
            w = float(policy.weights[i, idx])
            records.append({"feature": fname, "weight": w, "sign": "pos" if w >= 0 else "neg", "action": label})
    df = pd.DataFrame(records)

    g = sns.catplot(
        data=df,
        x="weight",
        y="feature",
        col="action",
        col_order=action_labels,
        hue="sign",
        kind="bar",
        dodge=False,
        errorbar=None,
        palette=sign_palette,
        legend=False,
        height=7,
        aspect=0.5,
        order=list(feature_names),
    )
    for ax in g.axes.flat:
        ax.axvline(x=0, color="gray", linewidth=0.5, zorder=0)
    g.set_titles("{col_name}", fontweight="bold")
    g.set_xlabels("Weight")
    g.set_ylabels("")
    g.fig.suptitle("Action Weights", fontsize=14, fontweight="bold", y=1.02)
    _show_or_save(g.fig, output_dir, "weights_actions.png", save)

    # --- Figure 2: Sub-decision option weights ---
    n_state = len(feature_names)
    option_weights = policy.sub_weights[n_state:].tolist()
    option_order = list(option_feature_names)
    option_signs = ["pos" if w >= 0 else "neg" for w in option_weights]
    df_sub = pd.DataFrame({"feature": option_order, "weight": option_weights, "sign": option_signs})

    fig_sub, ax_sub = plt.subplots(figsize=(8, 4))
    sns.barplot(
        data=df_sub,
        x="weight",
        y="feature",
        hue="sign",
        order=option_order,
        palette=sign_palette,
        dodge=False,
        legend=False,
        ax=ax_sub,
    )
    ax_sub.axvline(x=0, color="gray", linewidth=0.5, zorder=0)
    ax_sub.set_title("Sub-Decision Weights (per-bird option features)", fontweight="bold")
    ax_sub.set_xlabel("Weight")
    ax_sub.set_ylabel("")
    fig_sub.tight_layout()
    _show_or_save(fig_sub, output_dir, "weights_sub.png", save)


def _plot_importance(action_imp, output_dir, save):
    """Feature importance horizontal bar chart."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    sns.set_theme(style="whitegrid", font_scale=0.9)

    names, values = zip(*action_imp)
    df = pd.DataFrame({"feature": list(names), "importance": list(values)})

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.barplot(data=df, x="importance", y="feature", color="#2c7bb6", ax=ax)
    ax.set_title("Feature Importance (sum |weight| across actions)", fontweight="bold")
    ax.set_xlabel("Importance")
    ax.set_ylabel("")

    fig.tight_layout()
    _show_or_save(fig, output_dir, "importance.png", save)


def _plot_trace(breakdowns, output_dir, save):
    """Decision trace: per-action feature contribution bar charts."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    sns.set_theme(style="whitegrid", font_scale=0.9)
    sign_palette = {"pos": "#2c7bb6", "neg": "#d7191c"}
    top_n = 8

    action_order = ["play_a_bird", "gain_food", "draw_a_bird"]
    sorted_breakdowns = sorted(breakdowns, key=lambda x: action_order.index(x.action_name))

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for ax, b in zip(axes, sorted_breakdowns):
        top = b.contributions[:top_n]
        names = [c.feature_name for c in top]
        values = [c.contribution for c in top]
        df = pd.DataFrame(
            {"feature": names, "contribution": values, "sign": ["pos" if v >= 0 else "neg" for v in values]}
        )
        sns.barplot(
            data=df,
            x="contribution",
            y="feature",
            hue="sign",
            order=names,
            palette=sign_palette,
            dodge=False,
            legend=False,
            ax=ax,
        )
        ax.axvline(x=0, color="gray", linewidth=0.5, zorder=0)
        ax.set_title(f"{b.action_name}\nprob: {b.probability:.1%}, score: {b.total_score:+.3f}", fontweight="bold")
        ax.set_xlabel("Contribution")
        ax.set_ylabel("")

    fig.suptitle("Decision Trace - Feature Contributions (top 8)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _show_or_save(fig, output_dir, "trace.png", save)


def _plot_evolution(checkpoint_data, features_to_plot, action_index, output_dir, save):
    """Weight evolution line plots."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    from src.rl.interpreter import compute_weight_evolution

    sns.set_theme(style="whitegrid", font_scale=0.9)

    n = len(features_to_plot)
    fig, axes = plt.subplots(n, 1, figsize=(10, 3 * n), sharex=True, squeeze=False)

    for idx, fname in enumerate(features_to_plot):
        ax = axes[idx, 0]
        records = []
        for aname in action_index:
            evo = compute_weight_evolution(checkpoint_data, fname, aname)
            for it, val in zip(evo["iterations"], evo["values"]):
                records.append({"iteration": it, "weight": val, "action": aname})
        df = pd.DataFrame(records)
        sns.lineplot(data=df, x="iteration", y="weight", hue="action", ax=ax, linewidth=1.5)
        ax.axhline(y=0, color="gray", linewidth=0.5, zorder=0)
        ax.set_title(fname, fontweight="bold")
        ax.set_ylabel("Weight")
        if idx < n - 1:
            ax.set_xlabel("")

    axes[-1, 0].set_xlabel("Training Iteration")
    fig.suptitle("Weight Evolution Over Training", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _show_or_save(fig, output_dir, "evolution.png", save)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and evaluate Wingspan RL policies.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Train subcommand
    train_parser = subparsers.add_parser("train", help="Train a policy via self-play")
    train_parser.add_argument("--num_iterations", type=int, default=50)
    train_parser.add_argument("--games_per_iteration", type=int, default=100)
    train_parser.add_argument("--num_turns", type=int, default=10)
    train_parser.add_argument("--learning_rate", type=float, default=0.01)
    train_parser.add_argument("--eval_games", type=int, default=50)
    train_parser.add_argument("--save_every", type=int, default=10)
    train_parser.add_argument("--output_dir", type=str, default="models")
    train_parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for self-play and eval (default: 1, sequential)",
    )
    resume_group = train_parser.add_mutually_exclusive_group(required=True)
    resume_group.add_argument("--resume", action="store_true", help="Resume from policy_latest.npz in output_dir")
    resume_group.add_argument("--fresh", action="store_true", help="Start training from scratch")

    # Evaluate subcommand
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a trained policy")
    eval_parser.add_argument("--policy_path", type=str, required=True)
    eval_parser.add_argument("--opponent", type=str, default="random", choices=["random", "mcts"])
    eval_parser.add_argument("--num_simulations", type=int, default=100, help="MCTS simulations (if opponent=mcts)")
    eval_parser.add_argument("--eval_games", type=int, default=100)
    eval_parser.add_argument("--num_turns", type=int, default=10)

    # Plot subcommand
    plot_parser = subparsers.add_parser("plot", help="Plot training metrics")
    plot_parser.add_argument(
        "--metrics_dir", type=str, default="models", help="Directory containing training_metrics.csv"
    )
    plot_parser.add_argument("--save", action="store_true", help="Save plot to file instead of displaying")

    # Interpret subcommand
    interpret_parser = subparsers.add_parser("interpret", help="Inspect and interpret a trained policy")
    interpret_parser.add_argument("--policy_path", type=str, required=True, help="Path to a .npz policy file")
    interpret_parser.add_argument(
        "--mode",
        type=str,
        default="summary",
        choices=["weights", "importance", "summary", "trace", "evolution"],
        help="Analysis mode (default: summary)",
    )
    interpret_parser.add_argument(
        "--action",
        type=str,
        default=None,
        choices=["play_a_bird", "gain_food", "draw_a_bird"],
        help="Filter to a specific action (weights mode)",
    )
    interpret_parser.add_argument("--feature", type=str, default=None, help="Filter to a specific feature (evolution)")
    interpret_parser.add_argument(
        "--threshold", type=float, default=0.5, help="Min weight magnitude for strategy rules (default: 0.5)"
    )
    interpret_parser.add_argument(
        "--num_samples", type=int, default=200, help="Candidate pool size for diverse trace selection (default: 200)"
    )
    interpret_parser.add_argument("--seed", type=int, default=42, help="Random seed for sample states (default: 42)")
    interpret_parser.add_argument(
        "--models_dir", type=str, default="models", help="Checkpoint directory for evolution mode"
    )
    interpret_parser.add_argument(
        "--max_checkpoints", type=int, default=50, help="Max checkpoints to load (default: 50)"
    )
    interpret_parser.add_argument("--save", action="store_true", help="Save plots to files")

    args = parser.parse_args()

    if args.command == "train":
        train(args)
    elif args.command == "evaluate":
        eval_policy(args)
    elif args.command == "plot":
        plot_metrics(args)
    elif args.command == "interpret":
        interpret_policy(args)
