import unittest
from src.entities.food_supply import FoodSupply

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

if __name__ == '__main__':
    unittest.main()