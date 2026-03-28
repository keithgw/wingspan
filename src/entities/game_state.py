from src.constants import VALID_PHASES


class GameState:
    """Central game state holding all shared objects: deck, tray, feeder, players, and turn tracking."""

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


class MCTSGameState(GameState):
    """GameState extended with hashable serialization for use as MCTS tree node keys.

    Handles hidden information: opponent hands are stored as counts (not contents),
    deck is stored as a count. Supports round-trip serialization via
    to_representation() / from_representation().
    """

    def set_tray(self, tray):
        self.tray = tray

    def set_players(self, players):
        self.players = players

    def _represent_bird_deck(self):
        """Represent the bird deck as a count (hidden information)."""
        return self.bird_deck.get_count()

    def _represent_discard_pile(self):
        """Represent the discard pile as a count."""
        return self.discard_pile.get_count()

    def _represent_player(self, player, full=True):
        """Represent a player, hiding hand contents for opponents."""
        player_dict = {
            "food_supply": player.get_food_supply().to_representation(),
            "game_board": player.get_game_board().to_representation(),
        }

        if full:
            player_dict["hand"] = player.get_bird_hand().to_representation()
        else:
            player_dict["hand"] = player.get_bird_hand().get_count()

        return frozenset(player_dict.items())

    def _get_opponents(self):
        """Return opponents ordered by next player."""
        player_index = self.game_turn % self.num_players
        return self.players[player_index + 1 :] + self.players[:player_index]

    def _reorder_players(self, current_player, opponents, game_turn):
        """Reorder players so the starting player is at index 0."""
        num_players = len(opponents) + 1
        player_turn_number = game_turn % num_players
        players = [current_player] + opponents
        return players[-player_turn_number:] + players[:-player_turn_number]

    def _get_turns_remaining(self, num_turns, game_turn, num_players):
        """Calculate turns remaining for a player at a given game turn."""
        return num_turns - (game_turn // num_players)

    def _construct_player(
        self, hand, representation, deck, game_turn, num_turns, num_players, name, playout_policy=None
    ):
        """Construct a BotPlayer from a state representation."""
        from src.entities.food_supply import FoodSupply
        from src.entities.gameboard import GameBoard
        from src.utilities.player_factory import create_bot_player

        food_supply = FoodSupply(initial_amount=representation["food_supply"])
        game_board = GameBoard.from_representation(representation["game_board"], deck)
        num_turns_remaining = self._get_turns_remaining(
            num_turns=num_turns, game_turn=game_turn, num_players=num_players
        )
        return create_bot_player(
            name=name,
            bird_hand=hand,
            food_supply=food_supply,
            game_board=game_board,
            num_turns_remaining=num_turns_remaining,
            policy=playout_policy,
        )

    def to_representation(self):
        """Serialize the full game state as a hashable frozenset."""
        state_dict = {
            "num_turns": self.num_turns,
            "game_turn": self.game_turn,
            "phase": self.phase,
            "bird_deck": self._represent_bird_deck(),
            "discard_pile": self._represent_discard_pile(),
            "tray": self.tray.to_representation(),
            "bird_feeder": self.bird_feeder.to_representation(),
            "current_player": self._represent_player(self.get_current_player(), full=True),
            "opponents": tuple(self._represent_player(player, full=False) for player in self._get_opponents()),
        }
        return frozenset(state_dict.items())

    @classmethod
    def from_representation(cls, representation, playout_policy=None):
        """Reconstruct an MCTSGameState from a hashable representation.

        If playout_policy is provided, all reconstructed BotPlayers use it
        instead of the default RandomPolicy.
        """
        from data.bird_list import birds as bird_list
        from src.entities.birdfeeder import BirdFeeder
        from src.entities.deck import Deck
        from src.entities.hand import BirdHand
        from src.entities.tray import Tray

        state_dict = dict(representation)

        bird_feeder = BirdFeeder(food_count=state_dict["bird_feeder"])

        num_opponents = len(state_dict["opponents"])
        game_state = cls(
            num_turns=state_dict["num_turns"],
            game_turn=state_dict["game_turn"],
            phase=state_dict["phase"],
            bird_feeder=bird_feeder,
            bird_deck=Deck(),
            discard_pile=Deck(),
            tray=None,
            players=[None] * (num_opponents + 1),
        )

        # Start with a full deck, then remove birds as we reconstruct state
        valid_bird_deck = game_state.get_bird_deck()
        valid_bird_deck.prepare_deck(bird_list)

        # Reconstruct tray
        game_state.set_tray(Tray.from_representation(state_dict["tray"], valid_bird_deck))

        # Reconstruct current player
        rep_current = dict(state_dict["current_player"])
        hand_current = BirdHand.from_representation(rep_current["hand"], valid_bird_deck)
        current_player = game_state._construct_player(
            hand=hand_current,
            representation=rep_current,
            deck=valid_bird_deck,
            game_turn=state_dict["game_turn"],
            num_turns=state_dict["num_turns"],
            num_players=num_opponents + 1,
            name="current_player",
            playout_policy=playout_policy,
        )

        # Reconstruct opponents
        opponents = []
        opponent_game_turn = state_dict["game_turn"]
        for i in range(num_opponents):
            rep_opponent = dict(state_dict["opponents"][i])
            hand_opponent = BirdHand()
            for _ in range(rep_opponent["hand"]):
                bird = valid_bird_deck.draw_card()
                hand_opponent.add_card(bird, bird.get_name())
            opponent_game_turn += 1
            opponents.append(
                game_state._construct_player(
                    hand=hand_opponent,
                    representation=rep_opponent,
                    deck=valid_bird_deck,
                    game_turn=opponent_game_turn,
                    num_turns=state_dict["num_turns"],
                    num_players=num_opponents + 1,
                    name=f"opponent_{i}",
                    playout_policy=playout_policy,
                )
            )

        # Reorder players to original turn order
        game_state.set_players(
            game_state._reorder_players(
                current_player=current_player,
                opponents=opponents,
                game_turn=state_dict["game_turn"],
            )
        )

        # Validate and fill discard pile
        valid_discard_pile = game_state.get_discard_pile()
        cards_to_discard = valid_bird_deck.get_count() - state_dict["bird_deck"]
        if cards_to_discard != state_dict["discard_pile"]:
            raise ValueError(
                f"Cards to discard ({cards_to_discard}) doesn't match "
                f"discard pile representation ({state_dict['discard_pile']})"
            )
        for _ in range(cards_to_discard):
            valid_discard_pile.add_card(valid_bird_deck.draw_card())

        return game_state

    @classmethod
    def from_game_state(cls, game_state):
        """Convert a GameState to an MCTSGameState."""
        return cls(
            num_turns=game_state.num_turns,
            bird_deck=game_state.bird_deck,
            discard_pile=game_state.discard_pile,
            tray=game_state.tray,
            bird_feeder=game_state.bird_feeder,
            players=game_state.players,
            game_turn=game_state.game_turn,
            phase=game_state.phase,
        )
