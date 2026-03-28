from src.constants import CHOOSE_A_BIRD_TO_DRAW, CHOOSE_A_BIRD_TO_PLAY
from src.entities.gameboard import GameBoard


class Player:
    """Base class for game players. Manages hand, food, board, and turn actions.

    Subclasses must implement _choose_action, _choose_a_bird_to_play,
    and _choose_a_bird_to_draw to define decision-making behavior.
    """

    def __init__(self, name, bird_hand, food_supply, num_turns_remaining, game_board=None):
        self.name = name
        self.bird_hand = bird_hand
        self.food_supply = food_supply
        self.turns_remaining = num_turns_remaining
        if game_board is None:
            self.game_board = GameBoard()
        else:
            self.game_board = game_board
        self.score = 0
        self.actions = ["play_a_bird", "gain_food", "draw_a_bird"]  # lay_eggs not implemented yet

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_bird_hand(self):
        return self.bird_hand

    def get_food_supply(self):
        return self.food_supply

    def get_game_board(self):
        return self.game_board

    def _enumerate_playable_birds(self):
        """Return names of birds the player can afford to play."""
        return [bird.get_name() for bird in self.bird_hand.get_cards_in_hand() if self.food_supply.can_play_bird(bird)]

    def _enumerate_legal_actions(self, tray, bird_deck):
        """Return the list of actions available given the current board, hand, food, tray, and deck."""
        legal_actions = []

        # Check if player can play a bird
        if not self.game_board.check_if_full():
            if len(self._enumerate_playable_birds()) > 0:
                legal_actions.append(self.actions[0])

        # Player can always gain food
        legal_actions.append(self.actions[1])

        # Check if player can draw a bird
        if bird_deck.get_count() > 0 or tray.get_count() > 0:
            legal_actions.append(self.actions[2])

        return legal_actions

    def _choose_action(self, legal_actions, game_state):
        raise NotImplementedError

    def request_action(self, game_state):
        """Enumerate legal actions, delegate choice to subclass, and return the chosen action."""
        legal_actions = self._enumerate_legal_actions(tray=game_state.get_tray(), bird_deck=game_state.get_bird_deck())
        action = self._choose_action(legal_actions=legal_actions, game_state=game_state)
        return action

    def take_action(self, action, game_state):
        """Execute the chosen action, mutating the game state accordingly."""
        if action not in self.actions:
            raise Exception(f"Action {action} is not valid.")
        elif action == self.actions[0]:
            self.play_a_bird(game_state)
        elif action == self.actions[1]:
            self.gain_food(game_state.get_bird_feeder())
        else:
            self.draw_a_bird(game_state)

    def _choose_a_bird_to_play(self, playable_birds, game_state):
        raise NotImplementedError

    def play_a_bird(self, game_state):
        """Choose a playable bird, pay its food cost, and place it on the board."""
        playable_birds = self._enumerate_playable_birds()
        bird_name = self._choose_a_bird_to_play(playable_birds=playable_birds, game_state=game_state)

        food_cost = self.bird_hand.get_card(bird_name).get_food_cost()
        self.food_supply.decrement(food_cost)
        self.bird_hand.play_bird(bird_name=bird_name, game_board=self.game_board)

    def gain_food(self, bird_feeder):
        """Take one food from the bird feeder."""
        bird_feeder.take_food()
        self.food_supply.increment(1)

    def _choose_a_bird_to_draw(self, valid_choices, game_state):
        raise NotImplementedError

    def draw_a_bird(self, game_state):
        """Choose a bird from the tray or deck and add it to hand."""
        tray = game_state.get_tray()
        bird_deck = game_state.get_bird_deck()

        valid_choices = tray.see_birds_in_tray()
        if bird_deck.get_count() > 0:
            valid_choices.append("deck")

        chosen_bird = self._choose_a_bird_to_draw(valid_choices=valid_choices, game_state=game_state)

        if chosen_bird == "deck":
            try:
                self.bird_hand.draw_card_from_deck(bird_deck)
                print(f"You drew {self.bird_hand.get_card_names_in_hand()[-1]} from the deck.")
            except Exception as e:
                print(f"Error: {e}")
                chosen_bird = self._choose_a_bird_to_draw(valid_choices=valid_choices, game_state=game_state)
        else:
            self.bird_hand.draw_bird_from_tray(tray=tray, bird_name=chosen_bird)

    def get_score(self):
        return self.score

    def end_turn(self):
        """Decrement turns remaining and update score from the board."""
        self.turns_remaining -= 1
        self.score = self.game_board.get_score()

    def get_turns_remaining(self):
        return self.turns_remaining


class HumanPlayer(Player):
    """Player that makes decisions via CLI prompts."""

    def __init__(self, *args, advisor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.advisor = advisor

    def _show_hints(self, game_state, actions, label="Action"):
        """Display the advisor's recommended probabilities if available."""
        if self.advisor is None:
            return
        probs = self.advisor.get_action_probabilities(game_state, actions)
        best_idx = probs.argmax()
        print("  Advisor suggests:")
        for i, (action, prob) in enumerate(zip(actions, probs)):
            marker = " *" if i == best_idx else ""
            display = action.replace("_", " ")
            print(f"    {display:<20s} {prob:5.1%}{marker}")
        print()

    def _choose_action(self, legal_actions, game_state):
        actions_map = {"1": self.actions[0], "2": self.actions[1], "3": self.actions[2]}

        self._show_hints(game_state, legal_actions)

        options = []
        if "play_a_bird" in legal_actions:
            options.append("[1] Play a bird")
        if "gain_food" in legal_actions:
            options.append("[2] Gain food")
        if "draw_a_bird" in legal_actions:
            options.append("[3] Draw a bird")

        prompt = "  " + "  ".join(options) + "\n  > "
        chosen_action = input(prompt).strip()

        while chosen_action not in actions_map or actions_map[chosen_action] not in legal_actions:
            if chosen_action not in actions_map:
                print(f"  Invalid input '{chosen_action}'.")
            else:
                print(f"  You can't {actions_map[chosen_action].replace('_', ' ')} right now.")
            chosen_action = input("  > ").strip()

        return actions_map[chosen_action]

    def _choose_a_bird_to_play(self, playable_birds, game_state):
        self._show_hints(game_state, playable_birds, label="Bird to play")
        print("  Choose a bird to play:")
        for bird in playable_birds:
            print(f"    {bird}")
        chosen_bird = input("  > ").strip()
        while chosen_bird not in playable_birds:
            print(f"  '{chosen_bird}' is not a valid choice.")
            chosen_bird = input("  > ").strip()
        return chosen_bird

    def _choose_a_bird_to_draw(self, valid_choices, game_state):
        self._show_hints(game_state, valid_choices, label="Bird to draw")
        birds_in_tray = [bird for bird in valid_choices if bird != "deck"]
        tray_is_empty = len(birds_in_tray) == 0

        if tray_is_empty:
            print("  The tray is empty. Type 'deck' to draw from the deck.")
        else:
            print("  Choose a bird from the tray:")
            for bird in birds_in_tray:
                print(f"    {bird}")
            if "deck" in valid_choices:
                print("  Or type 'deck' to draw from the deck.")

        chosen_bird = input("  > ").strip()
        while chosen_bird not in valid_choices:
            print(f"  '{chosen_bird}' is not a valid choice.")
            chosen_bird = input("  > ").strip()

        return chosen_bird


class BotPlayer(Player):
    """Player that delegates all decisions to a Policy object."""

    def __init__(self, policy, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.policy = policy

    def _choose_action(self, legal_actions, game_state):
        action = self.policy(state=game_state, actions=legal_actions)

        # Update phase for multi-step actions
        if action == self.actions[0]:
            game_state.set_phase(CHOOSE_A_BIRD_TO_PLAY)
        elif action == self.actions[2]:
            game_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)

        return action

    def _choose_a_bird_to_play(self, playable_birds, game_state):
        return self.policy(state=game_state, actions=playable_birds)

    def _choose_a_bird_to_draw(self, valid_choices, game_state):
        return self.policy(state=game_state, actions=valid_choices)
