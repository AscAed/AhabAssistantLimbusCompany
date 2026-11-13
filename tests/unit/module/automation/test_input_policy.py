from unittest.mock import Mock, call, patch

import numpy as np
import pytest

from module.automation.automation import Automation
from module.automation.input_handlers.simulator import insert_swipe


def _automation():
    auto = object.__new__(Automation)
    auto.screenshot = None
    auto.screenshot_np = np.zeros((600, 800), dtype=np.uint8)
    auto.last_click_time = 100
    for operation in ("mouse_click", "mouse_drag", "mouse_drag_down", "mouse_scroll"):
        setattr(auto, operation, Mock())
    return auto


@pytest.mark.parametrize("offset", [True, False])
def test_calculate_click_position_preserves_detected_coordinates(offset):
    auto = _automation()

    with patch("module.automation.automation.np.random.normal", return_value=4):
        assert auto.calculate_click_position((100, 200), offset=offset) == (100, 200)


def test_mouse_action_interval_is_deterministic():
    auto = _automation()
    with patch("module.automation.automation.cfg") as mock_cfg, patch(
        "module.automation.automation.time.time", return_value=100
    ), patch("module.automation.automation.time.sleep") as sleep:
        mock_cfg.mouse_action_interval = 0.2

        auto.mouse_action_with_pos((100, 200), offset=False)
        auto.mouse_action_with_pos((100, 200), offset=False)

    assert sleep.call_args_list == [call(0.2), call(0.2)]
    assert auto.mouse_click.call_args_list == [call(100, 200, times=1), call(100, 200, times=1)]


def test_insert_swipe_is_repeatable_and_preserves_endpoints():
    first = insert_swipe((20, 30), (620, 430))
    second = insert_swipe((20, 30), (620, 430))

    assert first == second
    assert first[0] == [20, 30]
    assert first[-1] == [620, 430]


def test_insert_swipe_respects_minimum_spacing():
    points = insert_swipe((0, 0), (100, 0), speed=2, min_distance=10)

    assert points[0] == [0, 0]
    assert points[-1] == [100, 0]
    assert all(
        (second[0] - first[0]) ** 2 + (second[1] - first[1]) ** 2 >= 100
        for first, second in zip(points, points[1:])
    )


def test_insert_swipe_keeps_short_path_endpoints():
    assert insert_swipe((1, 2), (2, 3), min_distance=10) == [[1, 2], [2, 3]]
