## 2025-02-14 - Constant Folding in List Memberships
**Learning:** Checking for membership against lists `["val1", "val2"]` is slightly slower than using sets `{"val1", "val2"}`.
**Action:** Use set literals when checking for membership in fixed collections to optimize speed with constant folding.
