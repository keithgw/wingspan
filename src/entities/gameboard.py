class GameBoard:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        if len(self.cards) >= 5:
            raise ValueError("Game board is full. Cannot add more cards.")
        self.cards.append(card)

    def get_cards(self):
        return self.cards