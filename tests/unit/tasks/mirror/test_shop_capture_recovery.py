from unittest.mock import patch

import pytest

from tasks.mirror.in_shop import Shop


@patch(
    "tasks.mirror.in_shop.wait_for_screenshot",
    side_effect=RuntimeError("等待截图超时"),
)
@patch("tasks.mirror.in_shop.auto")
def test_heal_sinner_stops_after_bounded_capture_failure(
    mock_auto, mock_wait_for_screenshot
):
    mock_auto.take_screenshot.side_effect = [
        None,
        AssertionError("unbounded screenshot retry"),
    ]
    shop = object.__new__(Shop)

    with pytest.raises(RuntimeError, match="等待截图超时"):
        shop.heal_sinner()

    mock_wait_for_screenshot.assert_called_once_with()
    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()
