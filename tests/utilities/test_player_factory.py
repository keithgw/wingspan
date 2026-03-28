import unittest

from src.entities.food_supply import FoodSupply
from src.entities.hand import BirdHand
from src.entities.player import BotPlayer, HumanPlayer
from src.rl.policy import RandomPolicy
from src.utilities.player_factory import create_bot_player, create_human_player


class TestPlayerFactory(unittest.TestCase):
    def test_create_bot_player_default_policy(self):
        player = create_bot_player(name="Bot", bird_hand=BirdHand(), food_supply=FoodSupply(), num_turns_remaining=5)
        self.assertIsInstance(player, BotPlayer)
        self.assertIsInstance(player.policy, RandomPolicy)

    def test_create_bot_player_custom_policy(self):
        custom_policy = lambda state, actions: actions[0]  # noqa: E731
        player = create_bot_player(
            policy=custom_policy, name="Bot", bird_hand=BirdHand(), food_supply=FoodSupply(), num_turns_remaining=5
        )
        self.assertIsInstance(player, BotPlayer)
        self.assertEqual(player.policy, custom_policy)

    def test_create_human_player(self):
        player = create_human_player(
            name="Human", bird_hand=BirdHand(), food_supply=FoodSupply(), num_turns_remaining=5
        )
        self.assertIsInstance(player, HumanPlayer)


if __name__ == "__main__":
    unittest.main()
