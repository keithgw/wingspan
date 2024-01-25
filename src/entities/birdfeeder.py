class BirdFeeder:
    def __init__(self):
        self.food_count = 0

    class NotEmptyError(Exception):
        pass

    def reroll(self):
        '''Reroll the bird feeder and set the food count to 5.'''
        if self.food_count == 0:
            self.food_count = 5
        else:
            raise BirdFeeder.NotEmptyError("Bird feeder is not empty!")
        
    def take_food(self):
        '''Take a food from the bird feeder.'''
        if self.food_count > 0:
            self.food_count -= 1
            if self.food_count == 0:
                self.reroll()
        else:
            self.reroll()

    def render(self):
        print("Bird Feeder: " + str(self.food_count))

    def to_representation(self):
        return self.food_count