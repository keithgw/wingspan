from src.utilities.utils import render_bird_container

class GameBoard:
    def __init__(self, capacity=5):
        self.capacity = capacity
        self.cards = []

    def check_if_full(self):
        return len(self.cards) == self.capacity

    def add_card(self, card):
        if self.check_if_full():
            raise ValueError("Game board is full. Cannot add more cards.")
        self.cards.append(card)

    def get_birds(self):
        return self.cards
    
    def render(self):
        print(render_bird_container(bird_container=self.get_birds(), capacity=self.capacity))
