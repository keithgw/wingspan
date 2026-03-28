import numpy as np

# Canonical action indices for the CHOOSE_ACTION phase
ACTION_INDEX = {"play_a_bird": 0, "gain_food": 1, "draw_a_bird": 2}

# Feature names for interpretability (#80)
FEATURE_NAMES = [
    "game_progress",
    "food_supply",
    "board_score",
    "board_count",
    "hand_count",
    "hand_max_points",
    "hand_min_cost",
    "can_play_bird",
    "hand_best_ratio",
    "tray_count",
    "tray_max_points",
    "tray_best_ratio",
    "deck_remaining",
    "opponent_best_score",
    "opponent_avg_food",
    "score_lead",
]

NUM_FEATURES = len(FEATURE_NAMES)

# Per-option features for sub-decisions (which bird to play/draw)
OPTION_FEATURE_NAMES = [
    "option_points",
    "option_cost",
    "option_ratio",
    "option_affordable",
    "option_turns_to_afford",
    "option_playable_in_time",
    "option_points_vs_opponent",
    "option_is_deck",
]

NUM_OPTION_FEATURES = len(OPTION_FEATURE_NAMES)

# Combined feature size for sub-decision scoring
NUM_SUB_FEATURES = NUM_FEATURES + NUM_OPTION_FEATURES


def _points_cost_ratio(bird):
    """Return points/cost ratio, treating cost-0 birds as high efficiency (capped at 5)."""
    cost = bird.get_food_cost()
    if cost == 0:
        return 5.0
    return bird.get_points() / cost


def _best_ratio(birds):
    """Return the best points/cost ratio from a list of birds, or 0.0 if empty."""
    if not birds:
        return 0.0
    return max(_points_cost_ratio(bird) for bird in birds)


def featurize(state):
    """Convert a GameState to a fixed-size numpy feature vector.

    All features are from the current player's perspective, normalized
    to roughly [0, 1] or small bounded ranges for stable learning.
    Returns a 1-D numpy array of shape (NUM_FEATURES,).
    """
    player = state.get_current_player()
    hand_birds = player.get_bird_hand().get_cards_in_hand()
    board = player.get_game_board()
    food = player.get_food_supply().amount
    tray_birds = state.get_tray().get_birds_in_tray()

    # Game progress
    total_turns = state.num_turns * state.num_players
    game_progress = state.game_turn / total_turns if total_turns > 0 else 1.0

    # Current player features (use live board score)
    board_score = board.get_score()
    board_count = len(board.get_birds()) / board.capacity
    hand_count = len(hand_birds)
    hand_max_points = max((b.get_points() for b in hand_birds), default=0)
    playable = [b for b in hand_birds if food >= b.get_food_cost()]
    hand_min_cost = min((b.get_food_cost() for b in playable), default=0) if playable else 0.0
    can_play_bird = 1.0 if playable and not board.check_if_full() else 0.0
    hand_best_ratio = _best_ratio(hand_birds)

    # Tray features
    tray_count = len(tray_birds) / state.get_tray().capacity
    tray_max_points = max((b.get_points() for b in tray_birds), default=0)
    tray_best_ratio = _best_ratio(tray_birds)

    # Shared resources
    deck_remaining = state.get_bird_deck().get_count() / 180.0

    # Opponent features (use live board score for consistency)
    opponents = [p for p in state.get_players() if p is not player]
    if opponents:
        opponent_best_score = max(p.get_game_board().get_score() for p in opponents)
        opponent_avg_food = np.mean([p.get_food_supply().amount for p in opponents])
    else:
        opponent_best_score = 0
        opponent_avg_food = 0

    score_lead = board_score - opponent_best_score

    return np.array(
        [
            game_progress,
            food / 10.0,
            board_score / 50.0,
            board_count,
            hand_count / 10.0,
            hand_max_points / 10.0,
            hand_min_cost / 5.0,
            can_play_bird,
            hand_best_ratio / 5.0,
            tray_count,
            tray_max_points / 10.0,
            tray_best_ratio / 5.0,
            deck_remaining,
            opponent_best_score / 50.0,
            opponent_avg_food / 10.0,
            score_lead / 50.0,
        ],
        dtype=np.float64,
    )


def featurize_option(state, bird_name):
    """Compute features for a single bird option (or 'deck') in context.

    Returns a numpy array of shape (NUM_OPTION_FEATURES,).
    For 'deck', uses zeros for bird-specific features and sets option_is_deck=1.
    """
    player = state.get_current_player()
    food = player.get_food_supply().amount
    turns_left = player.get_turns_remaining()

    opponents = [p for p in state.get_players() if p is not player]
    opponent_best_score = max((p.get_game_board().get_score() for p in opponents), default=0)

    if bird_name == "deck":
        return np.array(
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            dtype=np.float64,
        )

    # Look up the bird object from hand or tray
    bird = None
    for b in player.get_bird_hand().get_cards_in_hand():
        if b.get_name() == bird_name:
            bird = b
            break
    if bird is None:
        for b in state.get_tray().get_birds_in_tray():
            if b.get_name() == bird_name:
                bird = b
                break
    if bird is None:
        return np.zeros(NUM_OPTION_FEATURES, dtype=np.float64)

    points = bird.get_points()
    cost = bird.get_food_cost()
    ratio = _points_cost_ratio(bird)
    affordable = 1.0 if food >= cost else 0.0
    turns_to_afford = max(0, cost - food) if food < cost else 0.0
    # Can we afford and play it before the game ends?
    # Need 1 turn to play + turns_to_afford turns to gain food
    turns_needed = turns_to_afford + 1
    playable_in_time = 1.0 if turns_needed <= turns_left else 0.0
    points_vs_opponent = points / max(opponent_best_score, 1)

    return np.array(
        [
            points / 10.0,
            cost / 5.0,
            ratio / 5.0,
            affordable,
            turns_to_afford / 5.0,
            playable_in_time,
            min(points_vs_opponent, 2.0) / 2.0,
            0.0,  # not deck
        ],
        dtype=np.float64,
    )
