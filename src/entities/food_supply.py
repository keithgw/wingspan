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