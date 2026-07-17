## 2024-07-14 - Fix Bare Except
**Learning:** Replaced bare `except:` with `except Exception:` to prevent unintended catching of system-level exceptions like `KeyboardInterrupt` or `SystemExit`.
**Action:** Always use `except Exception:` instead of bare `except:` to ensure system exceptions propagate properly.
## 2025-02-12 - [Python array looping in O(n^2) nested loop]
**Learning:** Found an O(n^2) algorithm with `np.linalg.norm` and `np.array` instance creation inside a double loop in Python.
**Action:** Replaced dynamic numpy array allocations and linalg operations with simple squared euclidean distance math (`(x1-x2)**2 + (y1-y2)**2 <= dist**2`). Benchmarks show ~30x speedup for 5000 points.
## 2025-02-14 - Constant Folding in List Memberships
**Learning:** Checking for membership against lists `["val1", "val2"]` is slightly slower than using sets `{"val1", "val2"}`.
**Action:** Use set literals when checking for membership in fixed collections to optimize speed with constant folding.
## 2026-07-17 - Add Screen Bounds Checking for Minitouch Input

**Learning:** When developing screen simulation components (like minitouch), it's important to pass screen max coordinate limits downwards into the builder layer so that logic bounds logic can evaluate whether the `x` and `y` offsets exceed display parameters locally before commands are pushed onto device stacks and potentially crash.
**Action:** Always retrieve and supply `max_x`, `max_y` limit configuration parameters into underlying structural components during their instantiation, and ensure explicit boundary exceptions are raised directly instead of silently clipping to improve failure visibility.
