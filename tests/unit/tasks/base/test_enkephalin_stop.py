from unittest.mock import patch

import pytest

from module.my_error.my_error import userStopError
from tasks.base.make_enkephalin_module import (
    lunacy_to_enkephalin,
    make_enkephalin_module,
)


def test_enkephalin_stop_after_capture_prevents_follow_up_input():
    stop_requested = False
    screenshot_count = 0

    def check_stop(_seconds):
        if stop_requested:
            raise userStopError("stop requested")

    def take_screenshot():
        nonlocal screenshot_count, stop_requested
        screenshot_count += 1
        if screenshot_count == 1:
            stop_requested = True
            return object()
        raise userStopError("stop requested")

    with patch("tasks.base.make_enkephalin_module.auto") as auto:
        auto.get_restore_time.return_value = None
        auto.take_screenshot.side_effect = take_screenshot
        auto.find_element.return_value = False
        auto.click_element.return_value = False
        auto.sleep_with_stop_check.side_effect = check_stop

        with pytest.raises(userStopError, match="stop requested"):
            make_enkephalin_module(skip=False)

    auto.mouse_to_blank.assert_not_called()
    auto.click_element.assert_not_called()


def test_lunacy_stop_after_preparation_prevents_lunacy_click():
    stop_requested = False

    def request_stop_after_prepare(*_args, **_kwargs):
        nonlocal stop_requested
        stop_requested = True

    def check_stop(_seconds):
        if stop_requested:
            raise userStopError("stop requested")

    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.make_enkephalin_module"
    ) as prepare_mock:
        prepare_mock.side_effect = request_stop_after_prepare
        auto.sleep_with_stop_check.side_effect = check_stop

        with pytest.raises(userStopError, match="stop requested"):
            lunacy_to_enkephalin(times=0)

    prepare_mock.assert_called_once_with(
        cancel=False, skip=False, task_name="狂气换体"
    )
    auto.click_element.assert_not_called()


def test_lunacy_stop_during_grandet_wait_prevents_confirmation_click():
    def check_stop(seconds):
        if seconds == 2:
            raise userStopError("stop requested")

    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.make_enkephalin_module.make_enkephalin_module"
    ), patch(
        "tasks.base.make_enkephalin_module.get_the_timing", return_value=False
    ):
        cfg.Dr_Grandet_mode = True
        auto.take_screenshot.return_value = object()
        auto.find_element.side_effect = [True, False]
        auto.sleep_with_stop_check.side_effect = check_stop

        with pytest.raises(userStopError, match="stop requested"):
            lunacy_to_enkephalin(times=1)

    auto.click_element.assert_called_once_with("enkephalin/use_lunacy_assets.png")
