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

## 2025-03-05 - Avoid np.linalg.norm in simulator input loops
**Learning:** `np.linalg.norm` is extremely slow in python tight loops (like Bezier curve generation for input simulation) because it implicitly creates and handles small `np.array` differences, causing significant memory allocation overhead.
**Action:** Replace `np.linalg.norm(a - b) <= max_dist` with squared Euclidean distance math directly on coordinate indexes like `(a[0]-b[0])**2 + (a[1]-b[1])**2 <= max_dist**2`. It's O(1) inside an O(n) array iteration and prevents numpy instantiation overhead.
## 2023-10-27 - [Scalar Distance Optimization]
**Learning:** Python-to-C API calls (`np.subtract`, `np.linalg.norm`) on tiny 2-element lists inside a `for` loop have significant overhead compared to raw arithmetic.
**Action:** Use scalar distance (`(x1-x2)**2 + (y1-y2)**2 < threshold**2`) in coordinate processing loops to bypass NumPy allocation overhead.

## 2026-07-21 - Avoid Multiple Screenshots in UI Automation Polling
**Learning:** Sequential `auto.find_element()` calls across a block of elements (e.g. searching for very_high to very_low buttons) will capture a new screenshot each time, causing massive I/O overhead.
**Action:** Take one screenshot manually before the loop (`auto.take_screenshot()`), then pass `take_screenshot=False` to all subsequent `find_element` calls using that frame to dramatically speed up the check sequence.
## 2026-07-25 - [Vectorized sort on OpenCV coordinate results]
**Learning:** Using Python's built-in `sorted(points, key=lambda x: res[x[1], x[0]])` on a large set of coordinate tuples extracted from a NumPy array (like from `np.where(res >= threshold)`) introduces huge overhead due to lambda evaluation and array indexing in Python.
**Action:** Use `np.argsort()` directly on the slice of scores (`scores = res[loc]`), then index the `x` and `y` arrays with the sorted indices (`loc[1][sort_indices].tolist()`), and finally zip them. This shifts the sorting and indexing completely into C, yielding ~3x speedups on large coordinate sets.
## 2024-07-26 - [Avoid lambda lookups over NumPy arrays]
**Learning:** In computer vision tasks (like OpenCV template matching), using Python's built-in `sorted()` with a lambda function that accesses a 2D NumPy array element-by-element introduces massive interpreter overhead due to repeated boundary checks and object instantiations.
**Action:** When sorting match coordinates by score, always use NumPy's vectorized `np.argsort()` directly on the score array and then use array indexing to reorder the coordinate lists before converting them back to Python types via `.tolist()`. This provides a significant (often 6x+) performance boost in multi-target matching logic.
## 2025-03-05 - Avoid multiple screenshots during state detection
**Learning:** Sequential `auto.find_element()` calls inside state detection loops can implicitly trigger multiple full-screen captures if not explicitly prevented.
**Action:** Take a screenshot once manually (`self.auto.take_screenshot()`) at the start of a detection block, and explicitly pass `take_screenshot=False` to all subsequent `find_element` calls to reuse the cached frame and avoid I/O overhead.

## 2025-03-05 - Fast Array Coordinate Sorting
**Learning:** Python's built-in `sorted()` with a lambda key doing lookup on a numpy array (`sorted(points, key=lambda x: res[x[1], x[0]])`) is very slow for large arrays due to repeated Python-to-C overhead and function calls.
**Action:** Use numpy's vectorized `np.argsort()` to get sorted indices first, then apply them to the coordinate arrays and convert to list (`loc_x[sorted_indices].tolist()`) before zipping. This prevents Python-level sorting overhead and yields a >2x speedup.
## 2025-03-10 - Fast Coordinate Sorting in Image Template Matching
**Learning:** Using Python's built-in `sorted(points, key=lambda x: res[x[1], x[0]])` on a list of tuples derived from a numpy array causes severe performance issues in tight algorithms like image template matching, because the lambda lookup executes python-to-C overhead for every single item repeatedly.
**Action:** Always replace lambda-based array lookups with numpy's vectorized tools. Use `loc_y, loc_x = np.where(res >= threshold)`, get scores directly via `scores = res[loc_y, loc_x]`, sort indices via `np.argsort(scores)[::-1]`, and extract the sorted axes using index mapping and `.tolist()` before zipping.
## 2025-02-14 - Vectorized Sorting in Template Match Results
**Learning:** When sorting coordinate points derived from a NumPy array (like OpenCV template matching results), using Python's built-in `sorted()` with a lambda key is a major bottleneck because lambda lookups over NumPy arrays introduce massive execution overhead.
**Action:** Use vectorized sorting via `np.argsort()` on the scores and extract indices into coordinates. This resulted in a ~2x faster extraction in large arrays.
## 2025-03-10 - Cache File I/O for Image Template Loads
**Learning:** Sequential calls to `auto.find_element()` (or similar CV wrapper functions) often repeatedly load the exact same template image files from disk via `Image.open`, creating massive underlying I/O overhead.
**Action:** Implement an in-memory dictionary or LRU cache for image asset loading (e.g., in `ImageUtils.load_image`), keyed by the path, resize parameters, and window size, to return the cached Numpy arrays instead of reading from disk on every template match call.
## 2024-08-01 - [Cache Corruption via Mutable Data Structures]
**Learning:** Caching results of computationally expensive loads (like reading images into numpy arrays with `cv2` or `PIL`) using `@functools.lru_cache` can introduce subtle state corruption bugs if the cached objects are mutable (`np.ndarray`). If any calling code edits the returned object in-place, the cached instance is mutated for all future calls.
**Action:** Always return a `.copy()` of the object when exposing a cached mutable instance. Encapsulate the cache in an internal function (e.g., `_load_image_cached`) and handle copying in the public wrapper function (e.g., `load_image`). Also, monitor the memory footprint of cached objects and keep `maxsize` conservative.

## 2024-05-30 - [Optimize File I/O for Image Assets]
**Learning:** In computer vision automation, repeatedly calling `ImageUtils.load_image` in tight loops results in heavy disk I/O and costly array conversions/resizing for identical templates, severely degrading performance during scanning tasks.
**Action:** Implemented `@functools.lru_cache` to cache loaded image template arrays in memory based on file path, window size, and active translation paths. Essential to ensure the public wrapper method returns `.copy()` so subsequent localized processing operations don't mutate the cached singleton.
