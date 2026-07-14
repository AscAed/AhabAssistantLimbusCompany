## 2024-07-14 - Fix Bare Except
**Learning:** Replaced bare `except:` with `except Exception:` to prevent unintended catching of system-level exceptions like `KeyboardInterrupt` or `SystemExit`.
**Action:** Always use `except Exception:` instead of bare `except:` to ensure system exceptions propagate properly.
