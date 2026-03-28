"""Evaluate policies by playing games against baselines."""

import contextlib
import io

import numpy as np


def evaluate(challenger, baseline, num_games=100, num_turns=10):
    """Play num_games between challenger (player 0) and baseline (player 1).

    Returns a dict with win_rate, mean_score, mean_opponent_score, and mean_score_diff.
    """
    from src.game import WingspanGame

    wins = 0
    scores = []
    opponent_scores = []

    for _ in range(num_games):
        policies = [challenger, baseline]
        call_count = [0]

        def policy_factory():
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
        scores.append(game_scores[0])
        opponent_scores.append(game_scores[1])
        if game_scores[0] > game_scores[1]:
            wins += 1

    return {
        "win_rate": wins / num_games,
        "mean_score": np.mean(scores),
        "mean_opponent_score": np.mean(opponent_scores),
        "mean_score_diff": np.mean(np.array(scores) - np.array(opponent_scores)),
    }
