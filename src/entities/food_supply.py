class FoodSupply:
    def __init__(self, initial_amount: int = 0):
        """
        Initializes a FoodSupply object.

        Args:
            initial_amount (int): The initial amount of food supply. Defaults to 0.
        """
        self.amount = initial_amount

    def increment(self, amount: int):
        """
        Increments the amount of food supply.

        Args:
            amount (int): The amount to increment the food supply by.
        """
        self.amount += amount

    class NotEnoughFoodError(Exception):
        pass

    def decrement(self, amount: int):
        """
        Decrements the amount of food supply.

        Args:
            amount (int): The amount to decrement the food supply by.

        Raises:
            FoodSupply.NotEnoughFoodError: If the food supply is not enough to decrement by the specified amount.
        """
        if self.amount >= amount:
            self.amount -= amount
        else:
            raise FoodSupply.NotEnoughFoodError("Not enough food supply!")

    def can_play_bird(self, bird) -> bool:
        """
        Checks if the player has enough food to play a bird.

        Args:
            bird (Bird): The bird to check if the player has enough food to play.

        Returns:
            bool: True if the player has enough food to play the bird, False otherwise.
        """
        return self.amount >= bird.get_food_cost()

    def render(self):
        """
        Renders the current amount of food supply.
        """
        print("Food supply: " + str(self.amount))

    def to_representation(self) -> int:
        """
        Returns a representation of the FoodSupply object.

        Returns:
            dict: A representation of the FoodSupply object.
        """
        return self.amount