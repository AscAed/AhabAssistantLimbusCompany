import random

def generate_bezier_path(
    start: tuple[int, int],
    end: tuple[int, int],
    steps: int | None = None
) -> list[tuple[int, int]]:
    """Generate a list of coordinates along a cubic Bézier curve between start and end.

    Args:
        start: (x, y) start coordinate.
        end: (x, y) end coordinate.
        steps: Number of steps along the path. If None, automatically determined.

    Returns:
        A list of (x, y) coordinates representing the path.
    """
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    distance = (dx * dx + dy * dy) ** 0.5

    if distance < 2:
        return [start, end]

    if steps is None:
        steps = max(5, min(50, int(distance / 15)))

    # Perpendicular vector unit values
    nx = -dy / distance
    ny = dx / distance

    # Randomise control points with perpendicular and parallel offsets
    offset1 = random.uniform(-0.25, 0.25) * distance
    offset2 = random.uniform(-0.25, 0.25) * distance

    p1_x = x0 + dx * random.uniform(0.2, 0.4) + nx * offset1
    p1_y = y0 + dy * random.uniform(0.2, 0.4) + ny * offset1

    p2_x = x0 + dx * random.uniform(0.6, 0.8) + nx * offset2
    p2_y = y0 + dy * random.uniform(0.6, 0.8) + ny * offset2

    path = []
    for i in range(steps + 1):
        t = i / steps
        # Cubic Bézier formula
        u = 1 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t

        bx = uuu * x0 + 3 * uu * t * p1_x + 3 * u * tt * p2_x + ttt * x1
        by = uuu * y0 + 3 * uu * t * p1_y + 3 * u * tt * p2_y + ttt * y1
        path.append((int(round(bx)), int(round(by))))

    return path
