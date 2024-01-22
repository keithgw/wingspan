class State:
    VALID_PHASES = ['choose_action', 'choose_a_bird_to_play', 'choose_a_bird_to_draw']
    def __init__(self, game_board, bird_hand, food_supply, phase, tray, bird_deck, legal_actions):
        if phase not in self.VALID_PHASES:
            raise ValueError(f"Invalid phase {phase}, must be one of {self.VALID_PHASES}")
        self.game_board = game_board
        self.bird_hand = bird_hand
        self.food_supply = food_supply
        self.phase = phase
        self.tray = tray
        self.bird_deck = bird_deck
        self.legal_actions = legal_actions

class Policy:
    def __call__(self, state):
        if state.phase == 'choose_action':
            return self._policy_choose_action(state.legal_actions)
        elif state.phase == 'choose_a_bird_to_play':
            return self._policy_choose_a_bird_to_play(state.bird_hand, state.food_supply)
        else:
            return self._policy_choose_a_bird_to_draw(state.tray, state.bird_deck)

    def _policy_choose_action(self, legal_actions):
        # Return probabilities for the actions 'play_a_bird', 'gain_food', 'draw_a_card'
        raise NotImplementedError

    def _policy_choose_a_bird_to_play(self, hand, food_supply):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        raise NotImplementedError


    def _policy_choose_a_bird_to_draw(self, tray, deck):
        # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'
        raise NotImplementedError

class RandomPolicy(Policy):
    def _policy_choose_action(self, legal_actions):
        # Return probabilities for the actions 'play_a_bird', 'gain_food', 'draw_a_card'

        # uniform random policy
        probabilities = [1/len(legal_actions)] * len(legal_actions)
        return probabilities

    def _policy_choose_a_bird_to_play(self, hand, food_supply):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        
        birds = hand.get_cards_in_hand()
        is_playable = [food_supply.can_play_bird(bird) for bird in birds]
        
        # set probability=0 for birds that cannot be played, else uniform random policy
        uniform_prob = 1/sum(is_playable)
        probabilities = [uniform_prob if playable else 0 for playable in is_playable]

        return probabilities

    def _policy_choose_a_bird_to_draw(self, tray, deck):
        # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'
        
        # uniform random policy
        num_birds_in_tray = tray.get_count()

        # deck is empty:
        if deck.get_count() == 0:
            return [1/num_birds_in_tray] * num_birds_in_tray + [0]
        else:
            return [1/(num_birds_in_tray + 1)] * (num_birds_in_tray + 1)