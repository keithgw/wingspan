import os
import shutil

TERM_WIDTH = shutil.get_terminal_size((80, 24)).columns


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def render_divider(char="─", width=None):
    """Return a horizontal line of the given character."""
    if width is None:
        width = min(TERM_WIDTH, 60)
    return char * width


def render_header(title, width=None):
    """Return a section header like '── Title ────────────' padded to width."""
    if width is None:
        width = min(TERM_WIDTH, 60)
    prefix = f"{'─' * 2} {title} "
    return prefix + "─" * max(0, width - len(prefix))


def render_bird_container(bird_container, capacity=None):
    """
    Render a bird container (hand, tray, or game board) as a formatted table.

    Args:
        bird_container (list[Bird]): The bird container to render.
        capacity (int): The capacity of the bird container.
    """
    if capacity is None:
        capacity = len(bird_container)

    output = f"  {'Name':<28s} {'VP':>3s}  {'Food':>4s}\n"
    for bird in bird_container:
        output += f"  {bird.get_name():<28s} {bird.get_points():>3d}  {bird.get_food_cost():>4d}\n"

    for _ in range(len(bird_container), capacity):
        output += f"  {'·':<28s} {'─':>3s}  {'─':>4s}\n"
    return output
