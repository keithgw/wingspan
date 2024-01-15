import unittest
from src.entities.birdfeeder import BirdFeeder
from unittest.mock import patch
from io import StringIO

class TestBirdFeeder(unittest.TestCase):
    def setUp(self):
        self.bird_feeder = BirdFeeder()

    def test_take_food(self):
        self.bird_feeder.food_count = 3
        self.bird_feeder.take_food()
        self.assertEqual(self.bird_feeder.food_count, 2)

    def test_take_food_when_empty(self):
        self.bird_feeder.food_count = 0
        self.bird_feeder.take_food()
        # Assert that reroll() is called when food_count is 0
        self.assertEqual(self.bird_feeder.food_count, 5)

    def test_take_food_when_empty_after_decrement(self):
        self.bird_feeder.food_count = 1
        self.bird_feeder.take_food()
        # Assert that reroll() is called when food_count is 0
        self.assertEqual(self.bird_feeder.food_count, 5)
        
    def test_reroll(self):
        self.bird_feeder.food_count = 0
        self.bird_feeder.reroll()
        # Assert that food_count is 5 after reroll()
        self.assertEqual(self.bird_feeder.food_count, 5)

    def test_reroll_when_not_empty(self):
        self.bird_feeder.food_count = 3
        with self.assertRaises(BirdFeeder.NotEmptyError):
            self.bird_feeder.reroll()

    def test_render(self):
        self.bird_feeder.food_count = 3
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.bird_feeder.render()
            self.assertEqual(fake_out.getvalue().strip(), "Bird Feeder: 3")

if __name__ == '__main__':
    unittest.main()
