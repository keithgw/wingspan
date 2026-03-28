"""CLI for training, evaluating, and visualizing learned policies."""

import argparse
import csv
import os

from src.rl.evaluator import evaluate
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

    print(f"Training for {args.num_iterations} iterations, {args.games_per_iteration} games each")
    print(f"Metrics will be saved to {metrics_path}\n")

    for iteration in range(start_iteration + 1, start_iteration + args.num_iterations + 1):
        # Collect experience via self-play
        action_exps, sub_exps, stats = runner.collect_experience(
            policy, num_games=args.games_per_iteration, num_turns=args.num_turns
        )

        # Train on collected experience
        train_batch(policy, action_exps, sub_exps, learning_rate=args.learning_rate)

        # Evaluate against random baseline
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

    args = parser.parse_args()

    if args.command == "train":
        train(args)
    elif args.command == "evaluate":
        eval_policy(args)
    elif args.command == "plot":
        plot_metrics(args)
