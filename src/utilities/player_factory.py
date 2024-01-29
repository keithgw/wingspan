from src.entities.player import HumanPlayer, BotPlayer
from src.rl.policy import RandomPolicy

def create_human_player(*args, **kwargs):
    """Create a human player."""
    return HumanPlayer(*args, **kwargs)

def create_bot_player(policy=None, *args, **kwargs):
    """Create a bot player with the given policy."""
    if policy is None:
        policy = RandomPolicy()
    return BotPlayer(policy=policy, *args, **kwargs)