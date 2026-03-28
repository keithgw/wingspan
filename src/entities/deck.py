import random


class Deck:
    def __init__(self, cards=None):
        if cards is None:
            self.cards = []
        else:
            self.cards = cards

    def get_count(self):
        return len(self.cards)

    def add_card(self, card):
        self.cards.append(card)

    def prepare_deck(self, cards):
        """Add cards to the deck and shuffle."""
        self.cards.extend(cards)
        self.shuffle()

    def remove_and_return_bird(self, condition):
        """Remove and return the first bird meeting the condition.

        Raises:
            ValueError: If no bird meets the condition.
        """
        for i, bird in enumerate(self.cards):
            if condition(bird):
                return self.cards.pop(i)
        raise ValueError("No bird in the deck meets the condition")

    def draw_card(self):
        if self.get_count() == 0:
            raise ValueError("Deck is empty")
        # cards will be drawn from the top of the deck
        return self.cards.pop(0)

    def shuffle(self):
        random.shuffle(self.cards)
