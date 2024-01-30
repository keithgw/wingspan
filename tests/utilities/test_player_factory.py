import unittest
from unittest.mock import Mock
from src.entities.player import BotPlayer, HumanPlayer
from src.rl.policy import RandomPolicy
from src.utilities.player_factory import create_bot_player, create_human_player

class TestPlayerFactory(unittest.TestCase):
    def setUp(self):
        self.kwargs = {"name": "Test Player", "bird_hand": Mock(), "food_supply": Mock(), "num_turns_remaining": 10}

    def test_create_bot_player_without_policy(self):
        # Act
        player = create_bot_player(**self.kwargs)
        
        # Assert
        self.assertIsInstance(player, BotPlayer)
        self.assertIsInstance(player.policy, RandomPolicy)

    def test_create_bot_player_with_policy(self):
        # Arrange
        mock_policy = Mock()
        
        # Act
        player = create_bot_player(**self.kwargs, policy=mock_policy)
        
        # Assert
        self.assertEqual(player.policy, mock_policy)

    def test_create_human_player(self):
        # Act
        player = create_human_player(**self.kwargs)

        # Assert
        self.assertIsInstance(player, HumanPlayer)

