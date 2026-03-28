"""CLI for training and evaluating learned policies."""

import argparse
import os

from src.rl.evaluator import evaluate
from src.rl.linear_policy import LinearPolicy
from src.rl.policy import RandomPolicy
from src.rl.self_play import SelfPlayRunner
from src.rl.trainer import train_batch


def train(args):
    """Run the training loop."""
    policy = LinearPolicy()
    runner = SelfPlayRunner()
    baseline = RandomPolicy()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Training for {args.num_iterations} iterations, {args.games_per_iteration} games each\n")

    for iteration in range(1, args.num_iterations + 1):
        # Collect experience via self-play
        experiences, stats = runner.collect_experience(
            policy, num_games=args.games_per_iteration, num_turns=args.num_turns
        )

        # Train on collected experience
        train_batch(policy, experiences, learning_rate=args.learning_rate)

        # Evaluate against random baseline
        eval_results = evaluate(policy, baseline, num_games=args.eval_games, num_turns=args.num_turns)

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
    print(f"Mean score:      {results['mean_score']:.1f}")
    print(f"Mean opp score:  {results['mean_opponent_score']:.1f}")
    print(f"Mean score diff: {results['mean_score_diff']:+.1f}")


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

    # Evaluate subcommand
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a trained policy")
    eval_parser.add_argument("--policy_path", type=str, required=True)
    eval_parser.add_argument("--opponent", type=str, default="random", choices=["random", "mcts"])
    eval_parser.add_argument("--num_simulations", type=int, default=100, help="MCTS simulations (if opponent=mcts)")
    eval_parser.add_argument("--eval_games", type=int, default=100)
    eval_parser.add_argument("--num_turns", type=int, default=10)

    args = parser.parse_args()

    if args.command == "train":
        train(args)
    elif args.command == "evaluate":
        eval_policy(args)
