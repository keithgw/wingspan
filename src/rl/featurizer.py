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
    # Tier 1: strategic calculations (#91)
    "turns_remaining",
    "best_immediate_vp",
    "affordable_bird_count",
    "max_achievable_vp",
    # Tray quality (kept from original)
    "tray_max_points",
    "tray_best_ratio",
    # Tier 2: deck composition (#91)
    "unseen_mean_ratio",
    "prob_draw_better",
    "prob_draw_affordable",
    "draw_vp_upside",
    # Opponent/relative
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


def _max_achievable_vp(hand_birds, food, board_slots_left, turns_left):
    """Greedy rollout: max VP achievable over remaining turns.

    Sorts hand by VP descending, greedily plays affordable birds (spending
    a turn each), spends turns gaining food when needed. Returns total VP
    that could be added to the board.
    """
    if turns_left <= 0 or board_slots_left <= 0 or not hand_birds:
        return 0.0

    candidates = sorted(hand_birds, key=lambda b: b.get_points(), reverse=True)
    total_vp = 0.0
    remaining_food = food
    remaining_turns = turns_left
    remaining_slots = board_slots_left

    for bird in candidates:
        if remaining_turns <= 0 or remaining_slots <= 0:
            break
        cost = bird.get_food_cost()
        food_needed = max(0, cost - remaining_food)
        # Need food_needed turns to gain food + 1 turn to play
        turns_needed = food_needed + 1
        if turns_needed <= remaining_turns:
            total_vp += bird.get_points()
            remaining_food = remaining_food + food_needed - cost
            remaining_turns -= turns_needed
            remaining_slots -= 1

    return total_vp


def _get_visible_birds(state, player):
    """Collect all birds visible to the current player (hand, all boards, tray)."""
    visible = []
    visible.extend(player.get_bird_hand().get_cards_in_hand())
    for p in state.get_players():
        visible.extend(p.get_game_board().get_birds())
    visible.extend(state.get_tray().get_birds_in_tray())
    return visible


def _unseen_bird_stats(state, player):
    """Compute statistics about unseen birds (deck + opponent hand + discard).

    Returns (mean_ratio, prob_better, prob_affordable, draw_upside) where:
    - mean_ratio: average VP/cost ratio of unseen cards
    - prob_better: fraction with ratio > best in hand
    - prob_affordable: fraction with cost <= current food
    - draw_upside: expected VP of best affordable unseen card minus best immediate play VP
    """
    from data.bird_list import birds as all_birds

    visible = _get_visible_birds(state, player)
    visible_names = {b.get_name() for b in visible}

    # Build unseen pool (subtract visible by name; duplicates possible across games but
    # each card is unique in a single game)
    unseen = [b for b in all_birds if b.get_name() not in visible_names]

    if not unseen:
        return 0.0, 0.0, 0.0, 0.0

    food = player.get_food_supply().amount
    hand_birds = player.get_bird_hand().get_cards_in_hand()
    best_hand_ratio = _best_ratio(hand_birds)
    board = player.get_game_board()

    # Unseen card statistics
    unseen_ratios = [_points_cost_ratio(b) for b in unseen]
    mean_ratio = sum(unseen_ratios) / len(unseen_ratios)
    prob_better = sum(1 for r in unseen_ratios if r > best_hand_ratio) / len(unseen)
    prob_affordable = sum(1 for b in unseen if b.get_food_cost() <= food) / len(unseen)

    # Draw upside: expected VP of affordable unseen cards vs best immediate play
    affordable_unseen = [b for b in unseen if b.get_food_cost() <= food]
    if affordable_unseen:
        mean_affordable_vp = sum(b.get_points() for b in affordable_unseen) / len(affordable_unseen)
    else:
        mean_affordable_vp = 0.0

    playable = [b for b in hand_birds if food >= b.get_food_cost() and not board.check_if_full()]
    best_immediate_vp = max((b.get_points() for b in playable), default=0)
    draw_upside = mean_affordable_vp - best_immediate_vp

    return mean_ratio, prob_better, prob_affordable, draw_upside


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

    # Tier 1: strategic calculations (#91)
    turns_remaining = player.get_turns_remaining()
    board_slots_left = board.capacity - len(board.get_birds())
    best_immediate_vp = max((b.get_points() for b in playable), default=0) if playable else 0
    affordable_count = len(playable) if playable else 0
    max_vp = _max_achievable_vp(hand_birds, food, board_slots_left, turns_remaining)

    # Tray quality features (kept from original)
    tray_max_points = max((b.get_points() for b in tray_birds), default=0)
    tray_best_ratio = _best_ratio(tray_birds)

    # Tier 2: deck composition (#91)
    unseen_mean_ratio, prob_draw_better, prob_draw_affordable, draw_vp_upside = _unseen_bird_stats(state, player)

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
            # Tier 1
            turns_remaining / state.num_turns,
            best_immediate_vp / 10.0,
            affordable_count / 5.0,
            max_vp / 50.0,
            # Tray quality
            tray_max_points / 10.0,
            tray_best_ratio / 5.0,
            # Tier 2
            unseen_mean_ratio / 5.0,
            prob_draw_better,
            prob_draw_affordable,
            np.clip(draw_vp_upside / 10.0, -1.0, 1.0),
            # Opponent/relative
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
