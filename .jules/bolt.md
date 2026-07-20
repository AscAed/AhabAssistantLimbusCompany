## 2024-07-14 - Fix Bare Except
**Learning:** Replaced bare `except:` with `except Exception:` to prevent unintended catching of system-level exceptions like `KeyboardInterrupt` or `SystemExit`.
**Action:** Always use `except Exception:` instead of bare `except:` to ensure system exceptions propagate properly.
## 2025-02-12 - [Python array looping in O(n^2) nested loop]
**Learning:** Found an O(n^2) algorithm with `np.linalg.norm` and `np.array` instance creation inside a double loop in Python.
**Action:** Replaced dynamic numpy array allocations and linalg operations with simple squared euclidean distance math (`(x1-x2)**2 + (y1-y2)**2 <= dist**2`). Benchmarks show ~30x speedup for 5000 points.

## 2025-02-14 - Constant Folding in List Memberships
**Learning:** Checking for membership against lists `["val1", "val2"]` is slightly slower than using sets `{"val1", "val2"}`.
**Action:** Use set literals when checking for membership in fixed collections to optimize speed with constant folding.

## 2025-02-28 - Fast Image Bounding Box Extraction
**Learning:** Using `np.max()` and `np.where()` over image arrays to find bounding boxes is bottlenecked by dynamic Python array allocations and lack of C-level vectorization for bounding box problems.
**Action:** Use `cv2.boundingRect()` combined with `cv2.max` and `(mask).astype(np.uint8)`. Benchmarks show ~20x speedup for bounding box extraction with safe backwards compatibility by checking `w==0` and manually raising expected original errors.

## 2025-03-05 - Avoid np.linalg.norm in tight loops
**Learning:** `np.linalg.norm` is slow in python tight loops (like connected component clustering) because it implicitly creates and handles small `np.array` differences causing memory allocation overhead.
**Action:** Replace `np.linalg.norm(a - b) <= max_dist` with squared Euclidean distance math directly on coordinate indexes like `(a[0]-b[0])**2 + (a[1]-b[1])**2 <= max_dist**2`. It's O(1) inside an O(n) array iteration and prevents numpy instantiation overhead.
