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

## 2025-03-05 - Fast multi-target image point sorting
**Learning:** Sorting an array of extracted tuples `sorted(points, key=lambda x: res[x[1], x[0]])` is very slow when there are many points, due to python lambda overhead and numpy single-element array lookup.
**Action:** Use vectorized sorting: `scores = res[loc]; sort_idx = np.argsort(scores)[::-1]` and `.tolist()` on the arrays before zipping `list(zip(loc_x[sort_idx].tolist(), loc_y[sort_idx].tolist()))` for a ~4x speedup.
## 2025-02-18 - [Vectorize Image Matching Filtering]
**Learning:** In `match_template_with_multiple_targets`, extracting matching coordinates via `np.where(res >= threshold)`, immediately zipping into Python tuples, and sorting with `sorted(points, key=lambda x: res[x[1], x[0]])` is incredibly slow for large match counts. The overhead of looking up values in the `res` NumPy array from within a Python lambda function per-item causes severe performance bottlenecks.
**Action:** Always use vectorized NumPy operations for filtering and sorting arrays before converting them to Python data structures. Use `y, x = (res >= threshold).nonzero()`, `scores = res[y, x]`, and `idx = np.argsort(scores)[::-1]` to sort coordinates directly in C, providing massive speedups for UI template matching.
## 2026-07-21 - Avoid Multiple Screenshots in UI Automation Polling
**Learning:** Sequential `auto.find_element()` calls across a block of elements (e.g. searching for very_high to very_low buttons) will capture a new screenshot each time, causing massive I/O overhead.
**Action:** Take one screenshot manually before the loop (`auto.take_screenshot()`), then pass `take_screenshot=False` to all subsequent `find_element` calls using that frame to dramatically speed up the check sequence.
## 2025-02-12 - Prevent environment pollution in tests
**Learning:** Adding a root-level `conftest.py` with heavy global mocks for Windows libraries (like `pywintypes`, `win32gui`, `ctypes`) in a shared environment can aggressively pollute the entire test suite, breaking tests that legitimately rely on OS-specific behavior in actual production.
**Action:** Always clean up temporary or root-level mock files (e.g. `conftest.py`, benchmark scripts) created for sandbox testing before committing to ensure the remote test suite is not degraded.

## 2025-03-05 - Avoid sorted() with lambda for numpy array results
**Learning:** Using Python's built-in `sorted()` with a lambda key that performs numpy array indexing (like `key=lambda x: res[x[1], x[0]]`) on a large number of coordinates is extremely slow due to the overhead of lambda calls and numpy item lookups inside a python loop.
**Action:** Use numpy's vectorized `np.argsort()` directly on the array slice (e.g. `scores = res[loc]; sort_idx = np.argsort(scores)[::-1]`), then use array indexing and `.tolist()` before zipping coordinates. This provides a ~2x to 3x speedup.
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

## 2026-07-26 - [Avoid redundant screenshots in UI polling loops]
**Learning:** In polling loops for UI automation, sequential calls to `find_element(..., take_screenshot=True)` will force a fresh screenshot on every check. When a single frame is valid for multiple conditional checks, this introduces massive unnecessary I/O and processing overhead.
**Action:** Take a screenshot once at the start of the loop (`auto.take_screenshot()`), and remove `take_screenshot=True` from subsequent `find_element` calls within that iteration to reuse the cached frame.

## 2025-02-12 - Prevent redundant numpy conversions of PIL images
**Learning:** Found a major performance bottleneck where `np.array(self.screenshot)` was called repeatedly for a PIL Image inside tight find_element/automation loops. Since `np.array()` on a 1920x1080 PIL Image takes around ~1.2ms to ~11ms (depending on memory state/system), doing this multiple times per automation tick accumulates massive micro-stuttering overhead.
**Action:** When a global state object (like a screenshot in UI automation) requires multiple formats (e.g., PIL for OCR, NumPy for OpenCV template matching), cache both formats at the point of capture rather than converting on-demand within iteration loops.
## 2026-08-16 - [Avoid find_feature_element loops for UI nodes]
**Learning:** Calling `auto.find_feature_element` iteratively within a loop (e.g., node evaluation) causes massive CPU spikes because it executes multi-scale resizing and Canny edge detection. Furthermore, it inherently does not cache the screen state.
**Action:** Use `auto.find_element(target, take_screenshot=False, roi=...)` for sequential checks against static templates to reuse a single screenshot and leverage direct 1:1 OpenCV template matching.

## 2026-07-28 - [Fast Binary Mask Bounding Box]
**Learning:** In computer vision (e.g. `get_bbox`), creating a mask using `(max_c > threshold).astype(np.uint8)` is significantly slower than using OpenCV's `cv2.threshold` for generating binary arrays.
**Action:** Replace numpy boolean casting `mask = (img > thresh).astype(np.uint8)` with OpenCV thresholding `_, mask = cv2.threshold(img, thresh, 1, cv2.THRESH_BINARY)` for ~30x faster bounding box computations.
## 2026-08-15 - File I/O Optimization in existing_image_paths
**Learning:** Repeated `os.path.exists` calls in hot loops like `detect_state()` cause significant disk I/O bottlenecks. Caching them requires carefully injecting dynamic global properties (like `path_manager.pic_path` and `current_language`) into the cache key by making them hashable tuples.
**Action:** When adding `lru_cache` to utility methods handling dynamic lists, create a static helper that takes hashable representations (tuples) of the state. Always ensure cached functions returning lists actually return copies (or use tuples and convert back to lists) to prevent mutability-induced cache corruption.

## 2026-08-15 - Fast path multi-scale feature matching
**Learning:** In `find_feature_element`, running `cv2.resize` and `cv2.matchTemplate` sequentially across scales `[0.85, 1.0, 1.15]` performs unnecessary and extremely costly computations if the element already natively matches at the 1.0 scale (which it does 90%+ of the time).
**Action:** Reorder scales to prioritize `[1.0, 0.85, 1.15]` and implement an early exit `break` when the match threshold is met. This skips massive image resizing overhead when the native scale is sufficient.
## 2025-03-10 - O(N) Spatial Hashing for Image Template Coordinates
**Learning:** In multi-target image matching, filtering out overlapping coordinates by checking each point against all kept points with an O(N^2) nested loop creates a massive bottleneck when thousands of points are matched.
**Action:** Replace the nested distance check loop with an O(N) Spatial Hashing grid (`grid = {}`; `cell = (int(x//dist), int(y//dist))`). This yields a >100x speedup (~4.3s down to ~0.03s for 5000 points) by only checking adjacent grid cells.
## 2023-11-20 - [Spatial Hashing for Multi-Target Optimization]
**Learning:** When filtering large sets of 2D coordinates (like OpenCV template matches) to remove overlaps, using an O(N^2) nested distance check loop against all previously kept points creates a massive bottleneck for dense match arrays.
**Action:** Use an O(N) Spatial Hashing grid (`cell = (int(x//dist), int(y//dist))`) to bucket retained points, and only check against the immediate 3x3 neighboring cells. This transforms filtering from a nested O(N^2) loop into an O(1) neighbor check, yielding up to 90x speedup for large result sets.
## 2026-07-17 - Add Screen Bounds Checking for Minitouch Input

**Learning:** When developing screen simulation components (like minitouch), it's important to pass screen max coordinate limits downwards into the builder layer so that logic bounds logic can evaluate whether the `x` and `y` offsets exceed display parameters locally before commands are pushed onto device stacks and potentially crash.
**Action:** Always retrieve and supply `max_x`, `max_y` limit configuration parameters into underlying structural components during their instantiation, and ensure explicit boundary exceptions are raised directly instead of silently clipping to improve failure visibility.
## 2025-03-10 - Duplicate NMS code loops
**Learning:** Found massive duplicate code blocks from a bad merge conflict in `match_template_with_multiple_targets` where the NMS algorithm was executed entirely using O(N^2) lists, and then subsequently overwritten by a second identical thresholding pass doing an O(N) Spatial Hash.
**Action:** Always inspect the entire method before optimizing. Removing redundant arrays and dead loops entirely provides a massive performance boost over trying to micro-optimize the duplicate blocks.
