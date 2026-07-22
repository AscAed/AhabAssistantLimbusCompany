import numpy as np


def random_normal_distribution(a, b, n=5):
    output = np.mean(np.random.uniform(a, b, size=n))
    return output


def random_theta():
    theta = np.random.uniform(0, 2 * np.pi)
    return np.array([np.sin(theta), np.cos(theta)])


def random_rho(dis):
    return random_normal_distribution(-dis, dis)


def insert_swipe(p0, p3, speed=15, min_distance=10):
    """
    从起点到终点插入路径点。
    首先生成三次贝塞尔曲线

    参数：
        p0：起点。
        p3：终点。
        速度：平均移动速度，每 10 毫秒的像素数。
        min_distance：

    返回：
        list[list[int]]：点列表。

    例子：
        > insert_swipe（（400， 400）， （600， 600）， 20）
        [[400, 400], [406, 406], [416, 415], [429, 428], [444, 442], [462, 459], [481, 478], [504, 500], [527, 522],
        [545, 540], [560, 557], [573, 570], [584, 582], [592, 590], [597, 596], [600, 600]]
    """
    p0 = np.array(p0)
    p3 = np.array(p3)

    # Random control points in Bézier curve
    distance = np.linalg.norm(p3 - p0)
    p1 = 2 / 3 * p0 + 1 / 3 * p3 + random_theta() * random_rho(distance * 0.1)
    p2 = 1 / 3 * p0 + 2 / 3 * p3 + random_theta() * random_rho(distance * 0.1)

    # Random `t` on Bézier curve, sparse in the middle, dense at start and end
    segments = max(int(distance / speed) + 1, 5)
    lower = random_normal_distribution(-85, -60)
    upper = random_normal_distribution(80, 90)
    theta = np.arange(lower + 0.0, upper + 0.0001, (upper - lower) / segments)
    ts = np.sin(theta / 180 * np.pi)
    ts = np.sign(ts) * abs(ts) ** 0.9
    ts = (ts - min(ts)) / (max(ts) - min(ts))

    # Generate cubic Bézier curve
    points = []
    prev = (-100, -100)
    # ⚡ Bolt: Replace np.linalg.norm with squared Euclidean distance to avoid numpy allocation overhead
    min_dist_sq = min_distance ** 2
    for t in ts:
        point = (
            p0 * (1 - t) ** 3
            + 3 * p1 * t * (1 - t) ** 2
            + 3 * p2 * t**2 * (1 - t)
            + p3 * t**3
        )
        point = point.astype(int).tolist()
        # ⚡ Bolt: Replace np.linalg.norm with squared Euclidean distance to avoid numpy allocation overhead in tight loop
        # ⚡ Bolt: Replace np.linalg.norm with squared distance for O(n) performance improvement avoiding numpy allocations
        if (point[0] - prev[0]) ** 2 + (point[1] - prev[1]) ** 2 < min_dist_sq:
        if (point[0] - prev[0])**2 + (point[1] - prev[1])**2 < min_dist_sq:
            continue

        points.append(point)
        prev = point

    # Delete nearing points
    if len(points) > 1:
        p0_list = points[0]
        # ⚡ Bolt: Replace np.linalg.norm array operations with python loop and squared distance math
        filtered_points = [p0_list]
        for p in points[1:]:
            if (p[0] - p0_list[0])**2 + (p[1] - p0_list[1])**2 >= min_dist_sq:
                filtered_points.append(p)
        points = filtered_points
    # ⚡ Bolt: Replace np.linalg.norm array operations with python loop over squared distance to avoid numpy object overhead
    if len(points) > 1:
        new_points = [points[0]]
        p_start = points[0]
        for p in points[1:]:
            if (p[0] - p_start[0])**2 + (p[1] - p_start[1])**2 > min_dist_sq:
                new_points.append(p)
        points = new_points

        if len(points) <= 1:
            points = [p0.tolist(), p3.tolist()]
    else:
        points = [p0.tolist(), p3.tolist()]
    return points
