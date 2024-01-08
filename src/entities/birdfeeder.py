class BirdFeeder:
    def __init__(self):
        self.food_count = 0

    class NotEmptyError(Exception):
        pass

    def reroll(self):
        if self.food_count == 0:
            self.food_count = 5
        else:
            raise BirdFeeder.NotEmptyError("Bird feeder is not empty!")
        
    def take_food(self):
        if self.food_count > 0:
            self.food_count -= 1
            if self.food_count == 0:
                self.reroll()
        else:
            self.reroll()