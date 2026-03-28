from src.constants import VALID_PHASES


class GameState:
    def __init__(
        self,
        num_turns,
        bird_deck,
        discard_pile,
        tray,
        bird_feeder,
        players,
        game_turn=0,
        phase=VALID_PHASES[0],
    ):
        if num_turns < 0:
            raise ValueError("num_turns must be non-negative.")
        self.num_turns = num_turns
        self.num_players = len(players)

        if game_turn > num_turns * self.num_players:
            raise ValueError("game_turn must be less than or equal to num_turns * num_players.")
        self.game_turn = game_turn

        if phase not in VALID_PHASES:
            raise ValueError(f"phase must be one of {VALID_PHASES}.")
        self.phase = phase

        self.bird_deck = bird_deck
        self.discard_pile = discard_pile
        self.tray = tray
        self.bird_feeder = bird_feeder
        self.players = players

    def get_num_turns(self):
        return self.num_turns

    def get_game_turn(self):
        return self.game_turn

    def get_phase(self):
        return self.phase

    def set_phase(self, phase):
        if phase not in VALID_PHASES:
            raise ValueError(f"phase must be one of {VALID_PHASES}, received {phase}.")
        self.phase = phase

    def get_bird_deck(self):
        return self.bird_deck

    def get_discard_pile(self):
        return self.discard_pile

    def get_tray(self):
        return self.tray

    def get_bird_feeder(self):
        return self.bird_feeder

    def get_players(self):
        return self.players

    def get_player(self, idx):
        return self.players[idx]

    def get_current_player(self):
        """Returns the current player object."""
        player_idx = self.game_turn % self.num_players
        return self.players[player_idx]

    def end_player_turn(self, player):
        """Ends the given player's turn: refills tray, updates turn accounting."""
        if self.tray.is_not_full():
            self.tray.refill(self.bird_deck)

        player.end_turn()
        self.game_turn += 1
        self.phase = VALID_PHASES[0]

    def is_game_over(self):
        return self.game_turn == self.num_turns * self.num_players
