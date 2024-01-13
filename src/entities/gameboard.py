class GameBoard:
    def __init__(self, limit=5):
        self.limit = limit
        self.cards = []

    def check_if_full(self):
        return len(self.cards) == self.limit

    def add_card(self, card):
        if self.check_if_full():
            raise ValueError("Game board is full. Cannot add more cards.")
        self.cards.append(card)

    def get_birds(self):
        return self.cards
    
    def render(self):
        print("{:<30s}{:<15s}{:<10s}".format("Bird Name", "Point Value", "Food Cost"))
        for bird in self.get_birds():
            print("{:<30s}{:<15d}{:<10d}".format(bird.get_name(), bird.get_points(), bird.get_food_cost()))
        for _ in range(len(self.cards), self.limit):
            print("{:<30s}{:<15s}{:<10s}".format("empty", "--", "--"))
        