import unittest
from src.entities.food_supply import FoodSupply
from src.entities.bird import Bird

class TestFoodSupply(unittest.TestCase):
    def test_increment(self):
        food = FoodSupply(3)
        food.increment(2)
        self.assertEqual(food.amount, 5)

    def test_decrement_no_error(self):
        food = FoodSupply(3)
        food.decrement(2)
        self.assertEqual(food.amount, 1)

    def test_decrement_with_error(self):
        food = FoodSupply(2)
        with self.assertRaises(FoodSupply.NotEnoughFoodError):
            food.decrement(3)

    def test_can_play_bird(self):
        food = FoodSupply(2)
        cheaper_bird = Bird('Osprey', 5, 1)
        equal_cost_bird = Bird('Fish Crow', 5, 2)
        more_expensive_bird = Bird('Great Horned Owl', 9, 3)
        self.assertTrue(food.can_play_bird(cheaper_bird))
        self.assertTrue(food.can_play_bird(equal_cost_bird))
        self.assertFalse(food.can_play_bird(more_expensive_bird))

if __name__ == '__main__':
    unittest.main()