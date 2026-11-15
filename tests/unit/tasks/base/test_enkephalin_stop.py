from unittest.mock import patch

import pytest

from module.my_error.my_error import userStopError
from tasks.base.make_enkephalin_module import (
    MAX_ENKEPHALIN_POPUP_RECOVERIES,
    EnkephalinPreparationError,
    EnkephalinPreparationTimeout,
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


def test_enkephalin_panel_timeout_raises_after_warning():
    with patch(
        "tasks.base.make_enkephalin_module.ENKEPHALIN_PREPARATION_TIMEOUT_SECONDS",
        0,
    ), patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch("time.time", return_value=10.0), patch(
        "app.mediator"
    ) as mediator:
        cfg.skip_enkephalin = False
        auto.get_restore_time.return_value = None

        with pytest.raises(
            EnkephalinPreparationTimeout, match="资源面板确认超时"
        ):
            make_enkephalin_module(skip=False)

    mediator.link_start.emit.assert_called_once_with()
    mediator.warning.emit.assert_called_once()
    auto.take_screenshot.assert_not_called()
    auto.click_element.assert_not_called()


def test_enkephalin_popup_recovery_failure_stops_preparation():
    with patch("time.time", side_effect=[0.0, 0.0, 10.0]), patch(
        "tasks.base.make_enkephalin_module.auto"
    ) as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.back_init_menu.back_init_menu", return_value=False
    ) as back_init_menu:
        cfg.skip_enkephalin = False
        auto.get_restore_time.return_value = None
        auto.take_screenshot.return_value = object()
        auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target in {"base/update_close_assets.png", "home/drive_assets.png"}
        )

        with pytest.raises(
            EnkephalinPreparationError, match="弹窗恢复失败"
        ):
            make_enkephalin_module(skip=False)

    back_init_menu.assert_called_once_with()


def test_enkephalin_popup_recovery_does_not_reset_preparation_deadline():
    with patch("time.time", side_effect=[0.0, 0.0, 40.0, 61.0]), patch(
        "tasks.base.make_enkephalin_module.auto"
    ) as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.back_init_menu.back_init_menu", return_value=True
    ) as back_init_menu, patch(
        "tasks.base.make_enkephalin_module.log"
    ):
        cfg.skip_enkephalin = False
        auto.get_restore_time.return_value = None
        auto.take_screenshot.return_value = object()
        auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target in {"base/update_close_assets.png", "home/drive_assets.png"}
        )

        with pytest.raises(
            EnkephalinPreparationTimeout, match="资源面板确认超时"
        ):
            make_enkephalin_module(skip=False)

    back_init_menu.assert_called_once_with()


def test_enkephalin_popup_recovery_count_is_bounded():
    clock_values = [
        0.0,
        0.0,
        *[float(value) for value in range(10, 10 * (MAX_ENKEPHALIN_POPUP_RECOVERIES + 2), 10)],
    ]
    with patch("time.time", side_effect=clock_values), patch(
        "tasks.base.make_enkephalin_module.auto"
    ) as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.back_init_menu.back_init_menu", return_value=True
    ) as back_init_menu, patch(
        "tasks.base.make_enkephalin_module.log"
    ):
        cfg.skip_enkephalin = False
        auto.get_restore_time.return_value = None
        auto.take_screenshot.return_value = object()
        auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target in {"base/update_close_assets.png", "home/drive_assets.png"}
        )

        with pytest.raises(
            EnkephalinPreparationError, match="弹窗恢复次数超限"
        ):
            make_enkephalin_module(skip=False)

    assert back_init_menu.call_count == MAX_ENKEPHALIN_POPUP_RECOVERIES


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
