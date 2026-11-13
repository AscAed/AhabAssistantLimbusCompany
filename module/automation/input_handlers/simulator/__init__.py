import math


def insert_swipe(p0, p3, speed=15, min_distance=10):
    """插入确定性的直线路径点，保留起终点及中间点最小间距。"""
    start = [int(p0[0]), int(p0[1])]
    end = [int(p3[0]), int(p3[1])]
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = math.hypot(dx, dy)
    segments = max(math.ceil(distance / speed), 1)
    min_distance_squared = min_distance**2
    points = [start]

    for index in range(1, segments):
        point = [
            int(start[0] + dx * index / segments),
            int(start[1] + dy * index / segments),
        ]
        previous = points[-1]
        previous_distance = (point[0] - previous[0]) ** 2 + (point[1] - previous[1]) ** 2
        end_distance = (end[0] - point[0]) ** 2 + (end[1] - point[1]) ** 2
        if previous_distance >= min_distance_squared and end_distance >= min_distance_squared:
            points.append(point)

    # Short paths still need both endpoints even when they are closer than min_distance.
    points.append(end)
    return points
