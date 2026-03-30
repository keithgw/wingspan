"""Evaluate policies by playing games against baselines."""

import contextlib
import io

import numpy as np


def _eval_chunk(args):
    """Play a chunk of evaluation games in a worker process.

    Top-level function so it's picklable by ProcessPoolExecutor.
    """
    weights, sub_weights, start_game_num, num_games, num_turns = args
    from src.rl.linear_policy import LinearPolicy
    from src.rl.policy import RandomPolicy

    challenger = LinearPolicy()
    challenger.weights = np.array(weights)
    challenger.sub_weights = np.array(sub_weights)
    baseline = RandomPolicy()

    return _evaluate_games(challenger, baseline, num_games, num_turns, start_game_num)


def _evaluate_games(challenger, baseline, num_games, num_turns, start_game_num=0):
    """Core evaluation loop shared by serial and parallel paths."""
    from src.game import WingspanGame

    wins = 0
    ties = 0
    scores = []
    opponent_scores = []

    for i in range(num_games):
        game_num = start_game_num + i
        challenger_first = game_num % 2 == 0
        if challenger_first:
            ordered = [challenger, baseline]
            challenger_idx = 0
        else:
            ordered = [baseline, challenger]
            challenger_idx = 1

        call_count = [0]

        def policy_factory(policies=ordered):
            idx = call_count[0]
            call_count[0] += 1
            return policies[idx]

        with contextlib.redirect_stdout(io.StringIO()):
            game = WingspanGame(
                num_players=2,
                num_human=0,
                num_turns=num_turns,
                bot_policy_factory=policy_factory,
            )
            game.play()

        game_scores = game.get_player_scores()
        c_score = game_scores[challenger_idx]
        o_score = game_scores[1 - challenger_idx]
        scores.append(c_score)
        opponent_scores.append(o_score)

        if c_score > o_score:
            wins += 1
        elif c_score == o_score:
            ties += 1

    return wins, ties, scores, opponent_scores


def evaluate(challenger, baseline, num_games=100, num_turns=10):
    """Play num_games between challenger and baseline, alternating positions.

    Even-numbered games: challenger is player 0, baseline is player 1.
    Odd-numbered games: baseline is player 0, challenger is player 1.
    This removes first-player positional bias.

    Returns a dict with win_rate, tie_rate, mean_score, mean_opponent_score,
    and mean_score_diff.
    """
    wins, ties, scores, opponent_scores = _evaluate_games(challenger, baseline, num_games, num_turns)
    return _build_eval_results(wins, ties, scores, opponent_scores)


def evaluate_parallel(policy, num_games=100, num_turns=10, pool=None):
    """Evaluate a LinearPolicy against RandomPolicy using a process pool.

    Args:
        policy: LinearPolicy with weights/sub_weights attributes.
        num_games: Total evaluation games.
        num_turns: Turns per game.
        pool: A ProcessPoolExecutor instance.

    Returns:
        Same dict as evaluate().
    """
    n_workers = pool._max_workers
    chunk_size = num_games // n_workers
    remainder = num_games % n_workers

    weights = policy.weights.tolist()
    sub_weights = policy.sub_weights.tolist()

    chunks = []
    game_offset = 0
    for i in range(n_workers):
        games = chunk_size + (1 if i < remainder else 0)
        if games > 0:
            chunks.append((weights, sub_weights, game_offset, games, num_turns))
            game_offset += games

    results = list(pool.map(_eval_chunk, chunks))

    total_wins = sum(r[0] for r in results)
    total_ties = sum(r[1] for r in results)
    all_scores = []
    all_opp_scores = []
    for _, _, scores, opp_scores in results:
        all_scores.extend(scores)
        all_opp_scores.extend(opp_scores)

    return _build_eval_results(total_wins, total_ties, all_scores, all_opp_scores)


def _build_eval_results(wins, ties, scores, opponent_scores):
    """Build the standard evaluation results dict."""
    num_games = len(scores)
    return {
        "win_rate": wins / num_games,
        "tie_rate": ties / num_games,
        "mean_score": np.mean(scores),
        "mean_opponent_score": np.mean(opponent_scores),
        "mean_score_diff": np.mean(np.array(scores) - np.array(opponent_scores)),
    }
