import numpy as np

from src.constants import CHOOSE_A_BIRD_TO_DRAW, CHOOSE_A_BIRD_TO_PLAY
from src.entities.gameboard import GameBoard
from src.rl.reinforcement_learning import RandomPolicy, State


class Player:
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
        legal_actions = self._enumerate_legal_actions(tray=game_state.get_tray(), bird_deck=game_state.get_bird_deck())
        action = self._choose_action(legal_actions=legal_actions, game_state=game_state)
        return action

    def take_action(self, action, game_state):
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
        playable_birds = self._enumerate_playable_birds()
        bird_name = self._choose_a_bird_to_play(playable_birds=playable_birds, game_state=game_state)

        food_cost = self.bird_hand.get_card(bird_name).get_food_cost()
        self.food_supply.decrement(food_cost)
        self.bird_hand.play_bird(bird_name=bird_name, game_board=self.game_board)

    def gain_food(self, bird_feeder):
        bird_feeder.take_food()
        self.food_supply.increment(1)

    def _choose_a_bird_to_draw(self, valid_choices, game_state):
        raise NotImplementedError

    def draw_a_bird(self, game_state):
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
        self.turns_remaining -= 1
        self.score = self.game_board.get_score()

    def get_turns_remaining(self):
        return self.turns_remaining


class HumanPlayer(Player):
    def _choose_action(self, legal_actions, game_state):
        actions_map = {"1": self.actions[0], "2": self.actions[1], "3": self.actions[2]}

        prompt = "Type 1 to play a bird, 2 to gain food, or 3 to draw a bird."
        chosen_action = input(prompt).strip()

        while actions_map[chosen_action] not in legal_actions:
            print(f"You are unable to {actions_map[chosen_action]}. {prompt}")
            chosen_action = input(prompt).strip()

        return actions_map[chosen_action]

    def _choose_a_bird_to_play(self, playable_birds, game_state):
        prompt = "Choose a bird to play: " + "\n" + "\n".join(playable_birds) + "\n"
        chosen_bird = input(prompt)
        while chosen_bird not in self.bird_hand.get_card_names_in_hand():
            print(f"{chosen_bird} is not a valid bird. {prompt}")
            chosen_bird = input(prompt)
        return chosen_bird

    def _choose_a_bird_to_draw(self, valid_choices, game_state):
        birds_in_tray = [bird for bird in valid_choices if bird != "deck"]
        prompt_from_tray = "Choose a bird from the tray: " + "\n" + "\n".join(birds_in_tray)
        prompt_from_deck = "type 'deck' to draw from the bird deck."
        tray_is_empty = len(birds_in_tray) == 0

        if tray_is_empty:
            prompt = "The tray is empty, " + prompt_from_deck
        elif "deck" not in valid_choices:
            prompt = prompt_from_tray
        else:
            prompt = prompt_from_tray + "\nor " + prompt_from_deck

        chosen_bird = input(prompt).strip()
        while chosen_bird not in valid_choices:
            print(f"{chosen_bird} is not a valid choice.")
            chosen_bird = input(prompt).strip()

        return chosen_bird


class BotPlayer(Player):
    def __init__(self, policy=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if policy is None:
            self.policy = RandomPolicy()
        else:
            self.policy = policy

    def _get_state(self, phase, tray=None, bird_deck=None, legal_actions=None):
        state = State(
            game_board=self.game_board,
            bird_hand=self.bird_hand,
            food_supply=self.food_supply,
            phase=phase,
            tray=tray,
            bird_deck=bird_deck,
            legal_actions=legal_actions,
        )
        return state

    def _choose_action(self, legal_actions, game_state):
        state = self._get_state(
            phase="choose_action",
            tray=game_state.get_tray(),
            bird_deck=game_state.get_bird_deck(),
            legal_actions=legal_actions,
        )

        action_probs = self.policy(state)
        chosen_action = np.random.choice(legal_actions, p=action_probs)

        # Update phase for multi-step actions
        if chosen_action == self.actions[0]:
            game_state.set_phase(CHOOSE_A_BIRD_TO_PLAY)
        elif chosen_action == self.actions[2]:
            game_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)

        return chosen_action

    def _choose_a_bird_to_play(self, playable_birds, game_state):
        state = self._get_state(
            phase="choose_a_bird_to_play",
            tray=game_state.get_tray(),
            bird_deck=game_state.get_bird_deck(),
        )
        bird_probs = self.policy(state)
        birds_in_hand = self.bird_hand.get_card_names_in_hand()
        chosen_bird = np.random.choice(birds_in_hand, p=bird_probs)
        return chosen_bird

    def _choose_a_bird_to_draw(self, valid_choices, game_state):
        state = self._get_state(
            phase="choose_a_bird_to_draw",
            tray=game_state.get_tray(),
            bird_deck=game_state.get_bird_deck(),
        )
        draw_probs = self.policy(state)
        chosen_bird = np.random.choice(valid_choices, p=draw_probs[: len(valid_choices)])
        return chosen_bird
