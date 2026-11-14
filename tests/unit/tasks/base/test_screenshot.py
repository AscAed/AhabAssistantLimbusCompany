from unittest.mock import patch

import pytest

from tasks.base.screenshot import wait_for_screenshot


def test_wait_for_screenshot_returns_first_frame():
    frame = object()
    with patch("tasks.base.screenshot.auto") as mock_auto:
        mock_auto.take_screenshot.side_effect = [None, frame]

        assert wait_for_screenshot(max_attempts=3) is frame

    assert mock_auto.take_screenshot.call_count == 2


def test_wait_for_screenshot_raises_after_attempt_limit():
    with patch("tasks.base.screenshot.auto") as mock_auto:
        mock_auto.take_screenshot.return_value = None

        with pytest.raises(RuntimeError, match="等待截图超时"):
            wait_for_screenshot(max_attempts=2)

    assert mock_auto.take_screenshot.call_count == 2
