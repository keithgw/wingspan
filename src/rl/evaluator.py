"""Evaluate policies by playing games against baselines."""

import contextlib
import io

import numpy as np


def evaluate(challenger, baseline, num_games=100, num_turns=10):
    """Play num_games between challenger and baseline, alternating positions.

    Even-numbered games: challenger is player 0, baseline is player 1.
    Odd-numbered games: baseline is player 0, challenger is player 1.
    This removes first-player positional bias.

    Returns a dict with win_rate, tie_rate, mean_score, mean_opponent_score,
    and mean_score_diff.
    """
    from src.game import WingspanGame

    wins = 0
    ties = 0
    scores = []
    opponent_scores = []

    for game_num in range(num_games):
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

    return {
        "win_rate": wins / num_games,
        "tie_rate": ties / num_games,
        "mean_score": np.mean(scores),
        "mean_opponent_score": np.mean(opponent_scores),
        "mean_score_diff": np.mean(np.array(scores) - np.array(opponent_scores)),
    }
