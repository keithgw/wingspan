import unittest
from src.entities.food_supply import FoodSupply
from src.entities.bird import Bird
from unittest.mock import patch
from io import StringIO

class TestFoodSupply(unittest.TestCase):
    def setUp(self):
        self.initial_amount = 3
        self.food_supply = FoodSupply(self.initial_amount)

    def test_increment(self):
        self.food_supply.increment(2)
        self.assertEqual(self.food_supply.amount, self.initial_amount + 2)

    def test_decrement_no_error(self):
        self.food_supply.decrement(2)
        self.assertEqual(self.food_supply.amount, self.initial_amount - 2)

    def test_decrement_with_error(self):
        with self.assertRaises(FoodSupply.NotEnoughFoodError):
            self.food_supply.decrement(self.initial_amount + 1)

    def test_can_play_bird(self):
        self.food_supply.amount = 2
        cheaper_bird = Bird('Osprey', 5, 1)
        equal_cost_bird = Bird('Fish Crow', 5, 2)
        more_expensive_bird = Bird('Great Horned Owl', 9, 3)
        self.assertTrue(self.food_supply.can_play_bird(cheaper_bird))
        self.assertTrue(self.food_supply.can_play_bird(equal_cost_bird))
        self.assertFalse(self.food_supply.can_play_bird(more_expensive_bird))

    def test_render(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.food_supply.render()
            self.assertEqual(fake_out.getvalue().strip(), "Food supply: 3")

    def test_to_representation(self):
        self.assertEqual(self.food_supply.to_representation(), self.initial_amount)

if __name__ == '__main__':
    unittest.main()