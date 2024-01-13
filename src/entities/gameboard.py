class GameBoard:
    def __init__(self):
        self.cards = []

    def check_if_full(self):
        return len(self.cards) == 5

    def add_card(self, card):
        if self.check_if_full():
            raise ValueError("Game board is full. Cannot add more cards.")
        self.cards.append(card)

    def get_cards(self):
        return self.cards