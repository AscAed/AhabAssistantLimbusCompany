from module.automation import auto
from module.logger import log

DEFAULT_SCREENSHOT_ATTEMPTS = 300


def wait_for_screenshot(
    max_attempts: int = DEFAULT_SCREENSHOT_ATTEMPTS, *, automation=None
):
    """Wait for a usable screenshot, then fail after a bounded number of attempts."""
    screenshot_source = automation if automation is not None else auto
    for _ in range(max_attempts):
        screenshot = screenshot_source.take_screenshot()
        if screenshot is not None:
            return screenshot
    log.error("等待截图超时")
    raise RuntimeError("等待截图超时")
