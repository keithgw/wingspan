from typing import Tuple

class Bird:
    """
    Represents a bird in the Wingspan game.

    Attributes:
        common_name (str): The common name of the bird.
        points (int): The number of points the bird is worth.
        food_cost (int): The amount of food required to play the bird.
    """

    def __init__(self, common_name: str, points: int, food_cost: int) -> None:
        self.common_name = common_name
        self.points = points
        self.food_cost = food_cost

    def get_name(self) -> str:
        """
        Get the common name of the bird.

        Returns:
            str: The common name of the bird.
        """
        return self.common_name
    
    def get_points(self) -> int:
        """
        Get the number of points the bird is worth.

        Returns:
            int: The number of points the bird is worth.
        """
        return self.points
    
    def get_food_cost(self) -> int:
        """
        Get the amount of food required to play the bird.

        Returns:
            int: The amount of food required to play the bird.
        """
        return self.food_cost
    
    def to_representation(self) -> Tuple[int, int]:
        """
        Get the representation of the bird for use in composing state representations.

        Returns:
            Tuple[int, int]: The representation of the bird as a tuple of (points, food_cost).
        """
        return (self.points, self.food_cost)
    
    def activate(self):
        """
        Activate the bird.

        This method should be overridden by subclasses to define the specific activation behavior.
        """
        pass
