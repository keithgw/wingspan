from src.entities.player import BotPlayer, HumanPlayer
from src.rl.policy import RandomPolicy


def create_human_player(*args, **kwargs):
    return HumanPlayer(*args, **kwargs)


def create_bot_player(*args, policy=None, **kwargs):
    if policy is None:
        policy = RandomPolicy()
    return BotPlayer(policy=policy, *args, **kwargs)
