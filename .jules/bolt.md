## 2025-02-12 - [Python array looping in O(n^2) nested loop]
**Learning:** Found an O(n^2) algorithm with `np.linalg.norm` and `np.array` instance creation inside a double loop in Python.
**Action:** Replaced dynamic numpy array allocations and linalg operations with simple squared euclidean distance math (`(x1-x2)**2 + (y1-y2)**2 <= dist**2`). Benchmarks show ~30x speedup for 5000 points.
## 2025-02-14 - Constant Folding in List Memberships
**Learning:** Checking for membership against lists `["val1", "val2"]` is slightly slower than using sets `{"val1", "val2"}`.
**Action:** Use set literals when checking for membership in fixed collections to optimize speed with constant folding.
