class FoodSupply:
    def __init__(self, initial_amount=0):
        self.amount = initial_amount

    def increment(self, amount):
        self.amount += amount

    class NotEnoughFoodError(Exception):
        pass

    def decrement(self, amount):
        if self.amount >= amount:
            self.amount -= amount
        else:
            raise FoodSupply.NotEnoughFoodError("Not enough food supply!")
        
    def can_play_bird(self, bird):
        '''
        Checks if the player has enough food to play a bird.
        
        Args:
            bird (Bird): The bird to check if the player has enough food to play.
        '''
        return self.amount >= bird.get_food_cost()
    
    def render(self):
        print("Food supply: " + str(self.amount))