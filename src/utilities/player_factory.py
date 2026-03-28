from src.entities.player import BotPlayer, HumanPlayer
from src.rl.policy import RandomPolicy


def create_human_player(*args, **kwargs):
    """Create a HumanPlayer with the given arguments."""
    return HumanPlayer(*args, **kwargs)


def create_bot_player(*args, policy=None, **kwargs):
    """Create a BotPlayer with the given policy (defaults to RandomPolicy)."""
    if policy is None:
        policy = RandomPolicy()
    return BotPlayer(policy=policy, *args, **kwargs)
