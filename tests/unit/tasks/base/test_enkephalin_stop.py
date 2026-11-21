from unittest.mock import patch

import pytest

from module.my_error.my_error import userStopError
from tasks.base.make_enkephalin_module import (
    MAX_ENKEPHALIN_POPUP_RECOVERIES,
    MAX_LUNACY_SCREENSHOT_ATTEMPTS,
    EnkephalinPreparationError,
    EnkephalinPreparationTimeout,
    _wait_for_grandet_timing,
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

    back_init_menu.assert_called_once_with(allow_restart=False)


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

    back_init_menu.assert_called_once_with(allow_restart=False)
    auto.take_screenshot.assert_called_once()


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
    assert all(
        call.kwargs == {"allow_restart": False}
        for call in back_init_menu.call_args_list
    )


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


def test_lunacy_capture_failure_is_bounded_and_stops_before_confirmation():
    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.make_enkephalin_module"
    ) as prepare:
        auto.take_screenshot.return_value = None

        with pytest.raises(
            EnkephalinPreparationError, match="连续截图失败"
        ):
            lunacy_to_enkephalin(times=1)

    prepare.assert_called_once_with(
        cancel=False, skip=False, task_name="狂气换体"
    )
    assert auto.take_screenshot.call_count == MAX_LUNACY_SCREENSHOT_ATTEMPTS
    sleep_durations = [
        call.args[0] for call in auto.sleep_with_stop_check.call_args_list
    ]
    assert sleep_durations.count(0.1) == MAX_LUNACY_SCREENSHOT_ATTEMPTS - 1
    assert auto.click_element.call_count == 1
    assert auto.click_element.call_args.args[0] == "enkephalin/use_lunacy_assets.png"


def test_lunacy_capture_recovers_after_transient_failures():
    confirm_asset = "enkephalin/enkephalin_confirm_assets.png"
    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.make_enkephalin_module.make_enkephalin_module"
    ):
        cfg.Dr_Grandet_mode = False
        auto.take_screenshot.side_effect = [None, None, object()]
        auto.find_element.side_effect = lambda target: (
            target == "enkephalin/lunacy_spend_26_assets.png"
        )

        lunacy_to_enkephalin(times=1)

    assert auto.take_screenshot.call_count == 3
    sleep_durations = [
        call.args[0] for call in auto.sleep_with_stop_check.call_args_list
    ]
    assert sleep_durations.count(0.1) == 2
    auto.click_element.assert_any_call(confirm_asset)


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


def test_grandet_wait_has_a_total_timeout_for_persistent_not_ready_timer():
    sleep_calls = 0

    def sleep(seconds):
        nonlocal sleep_calls
        if seconds == 2:
            sleep_calls += 1
            if sleep_calls >= 2:
                raise AssertionError("unbounded Grandet timing wait")

    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.get_the_timing", return_value=False
    ), patch("time.monotonic", side_effect=[0.0, 0.0, 91.0]):
        auto.sleep_with_stop_check.side_effect = sleep

        with pytest.raises(
            EnkephalinPreparationTimeout, match="葛朗台模式等待体力计时器超时"
        ):
            _wait_for_grandet_timing(already_qualified=False)

    assert sleep_calls == 1


def test_grandet_does_not_require_a_second_timer_read_after_qualification():
    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.get_the_timing"
    ) as get_timing:
        assert _wait_for_grandet_timing(already_qualified=True) is True

    auto.sleep_with_stop_check.assert_called_once_with(0)
    get_timing.assert_not_called()


@pytest.mark.parametrize(
    ("times", "spend_asset", "expected_confirmations"),
    [
        (1, "enkephalin/lunacy_spend_26_assets.png", 1),
        (2, "enkephalin/lunacy_spend_26_assets.png", 2),
        (3, "enkephalin/lunacy_spend_26_assets.png", 3),
        (2, "enkephalin/lunacy_spend_52_assets.png", 1),
        (3, "enkephalin/lunacy_spend_78_assets.png", 1),
    ],
)
def test_lunacy_spending_respects_configured_purchase_count(
    times, spend_asset, expected_confirmations
):
    confirm_asset = "enkephalin/enkephalin_confirm_assets.png"
    spend_checks = 0

    def find_element(target, *_args, **_kwargs):
        nonlocal spend_checks
        if target != spend_asset:
            return False
        spend_checks += 1
        if spend_checks > expected_confirmations:
            raise AssertionError("spending exceeded configured purchase count")
        return True

    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.make_enkephalin_module.make_enkephalin_module"
    ) as prepare:
        cfg.Dr_Grandet_mode = False
        auto.take_screenshot.return_value = object()
        auto.find_element.side_effect = find_element

        lunacy_to_enkephalin(times=times)

    assert [
        call.args[0]
        for call in auto.click_element.call_args_list
        if call.args[0] == confirm_asset
    ] == [confirm_asset] * expected_confirmations
    prepare.assert_any_call(cancel=False, skip=False, task_name="狂气换体")
    prepare.assert_any_call(skip=False)


@pytest.mark.parametrize(
    ("times", "spend_asset"),
    [
        (1, "enkephalin/lunacy_spend_26_assets.png"),
        (2, "enkephalin/lunacy_spend_52_assets.png"),
        (3, "enkephalin/lunacy_spend_78_assets.png"),
    ],
)
def test_lunacy_grandet_waits_for_qualified_timer_before_confirmation(
    times, spend_asset
):
    timer_readings = iter([False, False, True])
    spend_asset_seen = False
    confirm_asset = "enkephalin/enkephalin_confirm_assets.png"

    def find_element(target, *_args, **_kwargs):
        nonlocal spend_asset_seen
        if target == spend_asset and not spend_asset_seen:
            spend_asset_seen = True
            return True
        return False

    def read_timing():
        assert not any(
            call.args[0] == confirm_asset
            for call in auto.click_element.call_args_list
        )
        return next(timer_readings)

    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.make_enkephalin_module.make_enkephalin_module"
    ) as prepare, patch(
        "tasks.base.make_enkephalin_module.get_the_timing", side_effect=read_timing
    ) as get_timing:
        cfg.Dr_Grandet_mode = True
        auto.take_screenshot.return_value = object()
        auto.find_element.side_effect = find_element
        auto.click_element.side_effect = lambda target, *_args, **_kwargs: (
            target == confirm_asset
        )

        lunacy_to_enkephalin(times=times)

    assert get_timing.call_count == 3
    auto.click_element.assert_any_call(confirm_asset)
    prepare.assert_any_call(cancel=False, skip=False, task_name="狂气换体")
    prepare.assert_any_call(skip=False)


@pytest.mark.parametrize(
    ("times", "spend_asset"),
    [
        (1, "enkephalin/lunacy_spend_26_assets.png"),
        (2, "enkephalin/lunacy_spend_52_assets.png"),
        (3, "enkephalin/lunacy_spend_78_assets.png"),
    ],
)
def test_lunacy_grandet_stops_when_timer_anchor_is_missing(times, spend_asset):
    spend_asset_seen = False
    confirm_asset = "enkephalin/enkephalin_confirm_assets.png"

    def find_element(target, *_args, **_kwargs):
        nonlocal spend_asset_seen
        if target == spend_asset and not spend_asset_seen:
            spend_asset_seen = True
            return True
        return False

    with patch("tasks.base.make_enkephalin_module.auto") as auto, patch(
        "tasks.base.make_enkephalin_module.cfg"
    ) as cfg, patch(
        "tasks.base.make_enkephalin_module.make_enkephalin_module"
    ) as prepare, patch(
        "tasks.base.make_enkephalin_module.get_the_timing", return_value=None
    ):
        cfg.Dr_Grandet_mode = True
        auto.take_screenshot.return_value = object()
        auto.find_element.side_effect = find_element

        with pytest.raises(EnkephalinPreparationError, match="计时器"):
            lunacy_to_enkephalin(times=times)

    auto.click_element.assert_called_once_with("enkephalin/use_lunacy_assets.png")
    assert all(call.args[0] != confirm_asset for call in auto.click_element.call_args_list)
    prepare.assert_called_once_with(
        cancel=False, skip=False, task_name="狂气换体"
    )
