import time
import numpy as np

def random_normal_distribution(a, b, n=5):
    output = np.mean(np.random.uniform(a, b, size=n))
    return output

def random_theta():
    theta = np.random.uniform(0, 2 * np.pi)
    return np.array([np.sin(theta), np.cos(theta)])

def random_rho(dis):
    return random_normal_distribution(-dis, dis)

def insert_swipe_old(p0, p3, speed=15, min_distance=10):
    p0 = np.array(p0)
    p3 = np.array(p3)

    distance = np.linalg.norm(p3 - p0)
    p1 = 2 / 3 * p0 + 1 / 3 * p3 + random_theta() * random_rho(distance * 0.1)
    p2 = 1 / 3 * p0 + 2 / 3 * p3 + random_theta() * random_rho(distance * 0.1)

    segments = max(int(distance / speed) + 1, 5)
    lower = random_normal_distribution(-85, -60)
    upper = random_normal_distribution(80, 90)
    theta = np.arange(lower + 0.0, upper + 0.0001, (upper - lower) / segments)
    ts = np.sin(theta / 180 * np.pi)
    ts = np.sign(ts) * abs(ts) ** 0.9
    ts = (ts - min(ts)) / (max(ts) - min(ts))

    points = []
    prev = (-100, -100)
    for t in ts:
        point = (
            p0 * (1 - t) ** 3
            + 3 * p1 * t * (1 - t) ** 2
            + 3 * p2 * t**2 * (1 - t)
            + p3 * t**3
        )
        point = point.astype(int).tolist()
        if np.linalg.norm(np.subtract(point, prev)) < min_distance:
            continue

        points.append(point)
        prev = point

    if len(points[1:]):
        distance = np.linalg.norm(np.subtract(points[1:], points[0]), axis=1)
        mask = np.append(True, distance > min_distance)
        points = np.array(points)[mask].tolist()
        if len(points) <= 1:
            points = [p0, p3]
    else:
        points = [p0, p3]
    return points

def insert_swipe_new(p0, p3, speed=15, min_distance=10):
    p0 = np.array(p0)
    p3 = np.array(p3)

    distance = ((p3[0] - p0[0]) ** 2 + (p3[1] - p0[1]) ** 2) ** 0.5
    p1 = 2 / 3 * p0 + 1 / 3 * p3 + random_theta() * random_rho(distance * 0.1)
    p2 = 1 / 3 * p0 + 2 / 3 * p3 + random_theta() * random_rho(distance * 0.1)

    segments = max(int(distance / speed) + 1, 5)
    lower = random_normal_distribution(-85, -60)
    upper = random_normal_distribution(80, 90)
    theta = np.arange(lower + 0.0, upper + 0.0001, (upper - lower) / segments)
    ts = np.sin(theta / 180 * np.pi)
    ts = np.sign(ts) * abs(ts) ** 0.9
    ts = (ts - min(ts)) / (max(ts) - min(ts))

    points = []
    prev = (-100, -100)
    min_distance_sq = min_distance ** 2
    for t in ts:
        point = (
            p0 * (1 - t) ** 3
            + 3 * p1 * t * (1 - t) ** 2
            + 3 * p2 * t**2 * (1 - t)
            + p3 * t**3
        )
        point = point.astype(int).tolist()
        dist_sq = (point[0] - prev[0]) ** 2 + (point[1] - prev[1]) ** 2
        if dist_sq < min_distance_sq:
            continue

        points.append(point)
        prev = point

    if len(points[1:]):
        points_arr = np.array(points)
        dist_sq = np.sum((points_arr[1:] - points_arr[0]) ** 2, axis=1)
        mask = np.append(True, dist_sq > min_distance ** 2)
        points = points_arr[mask].tolist()
        if len(points) <= 1:
            points = [p0, p3]
    else:
        points = [p0, p3]
    return points

n_iters = 1000

t0 = time.time()
for _ in range(n_iters):
    insert_swipe_old((400, 400), (600, 600), 20)
t1 = time.time()
print(f"Old: {t1 - t0:.4f}s")

t0 = time.time()
for _ in range(n_iters):
    insert_swipe_new((400, 400), (600, 600), 20)
t1 = time.time()
print(f"New: {t1 - t0:.4f}s")
