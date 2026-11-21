from unittest.mock import patch

import pytest


def test_theme_pack_selection_bounds_repeated_difficulty_clicks():
    from tasks.mirror.select_theme_pack import (
        _MAX_THEME_PACK_ITERATIONS,
        select_theme_pack,
    )

    feature_asset = "mirror/theme_pack/theme_pack_features.png"
    hard_asset = "mirror/theme_pack/hard_assets.png"
    with (
        patch("tasks.mirror.select_theme_pack.cfg") as mock_cfg,
        patch("tasks.mirror.select_theme_pack.theme_list") as mock_theme_list,
        patch("tasks.mirror.select_theme_pack.path_manager") as mock_path_manager,
        patch("tasks.mirror.select_theme_pack.ImageUtils"),
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.select_theme_pack.sleep"),
        patch("tasks.mirror.select_theme_pack.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.set_win_size = 1080
        mock_path_manager.current_language = "zh_cn"
        mock_theme_list.get_effective_theme_pack_list.return_value = {}
        mock_auto.find_element.side_effect = lambda target, **kwargs: (
            (10, 10) if target in (feature_asset, hard_asset) else None
        )
        mock_auto.click_element.side_effect = lambda target, **kwargs: target == hard_asset

        result = select_theme_pack()

    assert result is False
    assert mock_wait.call_count == _MAX_THEME_PACK_ITERATIONS
    assert sum(call.args[0] == hard_asset for call in mock_auto.click_element.call_args_list) == (
        _MAX_THEME_PACK_ITERATIONS
    )
    mock_back_init_menu.assert_called_once_with()


def test_theme_pack_selection_returns_success_when_already_on_road_map():
    from tasks.mirror.select_theme_pack import select_theme_pack

    road_map_asset = "mirror/road_in_mir/legend_assets.png"
    with (
        patch("tasks.mirror.select_theme_pack.cfg") as mock_cfg,
        patch("tasks.mirror.select_theme_pack.theme_list") as mock_theme_list,
        patch("tasks.mirror.select_theme_pack.path_manager") as mock_path_manager,
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.select_theme_pack.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.set_win_size = 1080
        mock_path_manager.current_language = "zh_cn"
        mock_theme_list.get_effective_theme_pack_list.return_value = {}
        mock_auto.find_element.side_effect = lambda target, **kwargs: (
            target == road_map_asset
        )

        result = select_theme_pack()

    assert result is True
    mock_wait.assert_not_called()
    mock_back_init_menu.assert_not_called()


def test_theme_pack_selection_returns_success_when_road_map_appears_during_ocr():
    from tasks.mirror.select_theme_pack import (
        _MAX_THEME_PACK_ITERATIONS,
        select_theme_pack,
    )

    with (
        patch("tasks.mirror.select_theme_pack.cfg") as mock_cfg,
        patch("tasks.mirror.select_theme_pack.theme_list") as mock_theme_list,
        patch("tasks.mirror.select_theme_pack.path_manager") as mock_path_manager,
        patch("tasks.mirror.select_theme_pack.ImageUtils") as mock_image_utils,
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.select_theme_pack.sleep"),
        patch("tasks.mirror.select_theme_pack.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.set_win_size = 1080
        mock_path_manager.current_language = "zh_cn"
        mock_theme_list.get_effective_theme_pack_list.return_value = {}

        def find_element(target, **kwargs):
            if target == "mirror/theme_pack/feature_theme_pack_assets.png":
                return (10, 10)
            if target == "mirror/road_in_mir/legend_assets.png":
                return True
            return None

        mock_auto.find_element.side_effect = find_element
        mock_auto.find_text_element.return_value = False
        mock_image_utils.get_bbox.return_value = (10, 20, 30, 40)

        result = select_theme_pack()

    assert result is True
    assert mock_wait.call_count < _MAX_THEME_PACK_ITERATIONS
    mock_back_init_menu.assert_not_called()


def test_theme_pack_selection_returns_failure_after_menu_recovery():
    from tasks.mirror.select_theme_pack import select_theme_pack

    with (
        patch("tasks.mirror.select_theme_pack.cfg") as mock_cfg,
        patch("tasks.mirror.select_theme_pack.theme_list") as mock_theme_list,
        patch("tasks.mirror.select_theme_pack.path_manager") as mock_path_manager,
        patch("tasks.mirror.select_theme_pack.ImageUtils"),
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot"),
        patch("tasks.mirror.select_theme_pack.sleep"),
        patch("tasks.mirror.select_theme_pack.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.set_win_size = 1080
        mock_path_manager.current_language = "zh_cn"
        mock_theme_list.get_effective_theme_pack_list.return_value = {}
        mock_auto.find_element.side_effect = lambda target, **kwargs: (
            [] if target.endswith("theme_pack_features.png") else (10, 10)
        )
        mock_auto.click_element.return_value = False

        result = select_theme_pack()

    assert result is False
    mock_back_init_menu.assert_called_once_with()


@pytest.mark.parametrize(
    ("road_map_results", "capture_error", "expected_result"),
    [
        ([None, (500, 400)], None, True),
        ([None] * 60, None, False),
        ([], RuntimeError("capture timeout"), False),
    ],
)
def test_theme_pack_selection_confirms_road_map_after_low_weight_fallback(
    road_map_results, capture_error, expected_result
):
    from tasks.mirror.select_theme_pack import (
        _THEME_PACK_UNCHANGED_ATTEMPTS,
        select_theme_pack,
    )

    refresh_clicks = 0
    road_map_lookups = 0
    wait_calls_at_road_map = []
    wait_calls_at_drag = []
    post_drag_capture_failures = 1
    feature_asset = "mirror/theme_pack/theme_pack_features.png"
    road_map_asset = "mirror/road_in_mir/legend_assets.png"

    def wait_for_screenshot():
        nonlocal post_drag_capture_failures
        if capture_error is not None and mock_auto.mouse_drag_down.called:
            post_drag_capture_failures -= 1
            if post_drag_capture_failures >= 0:
                raise capture_error

    def click_element(target, **kwargs):
        nonlocal refresh_clicks
        if target == "mirror/theme_pack/refresh_assets.png":
            refresh_clicks += 1
            return refresh_clicks <= 4
        return False

    def find_element(target, **kwargs):
        nonlocal road_map_lookups
        if target == feature_asset:
            if expected_result and road_map_lookups > 0:
                return None
            return [(100, 200)]
        if target in (
            "mirror/theme_pack/normal_assets.png",
            "mirror/theme_pack/hard_assets.png",
        ):
            if expected_result and road_map_lookups > 0:
                return None
            return (10, 10)
        if target == road_map_asset:
            wait_calls_at_road_map.append(mock_wait.call_count)
            result = road_map_results[road_map_lookups]
            road_map_lookups += 1
            return result
        return None

    with (
        patch("tasks.mirror.select_theme_pack.cfg") as mock_cfg,
        patch("tasks.mirror.select_theme_pack.theme_list") as mock_theme_list,
        patch("tasks.mirror.select_theme_pack.path_manager") as mock_path_manager,
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.select_theme_pack.retry", return_value=None) as mock_retry,
        patch("tasks.mirror.select_theme_pack.sleep"),
        patch("tasks.mirror.select_theme_pack.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.set_win_size = 1080
        mock_path_manager.current_language = "zh_cn"
        mock_theme_list.get_effective_theme_pack_list.return_value = {}
        mock_theme_list.preferred_thresholds = 0
        mock_auto.find_element.side_effect = find_element
        mock_auto.find_language_text.return_value = False
        mock_auto.click_element.side_effect = click_element
        mock_auto.mouse_drag_down.side_effect = (
            lambda *args, **kwargs: wait_calls_at_drag.append(mock_wait.call_count)
        )
        mock_wait.side_effect = wait_for_screenshot

        result = select_theme_pack()

    assert result is expected_result
    assert refresh_clicks == 4
    mock_auto.mouse_drag_down.assert_called_once_with(100, 200)
    assert len(wait_calls_at_drag) == 1
    assert road_map_lookups == min(
        len(road_map_results), _THEME_PACK_UNCHANGED_ATTEMPTS
    )
    mock_retry.assert_called_once_with(allow_restart=False)
    mock_back_init_menu.assert_not_called()
    if road_map_results:
        assert wait_calls_at_road_map[0] == wait_calls_at_drag[0] + 1
        assert all(
            next_count == previous_count + 1
            for previous_count, next_count in zip(
                wait_calls_at_road_map, wait_calls_at_road_map[1:]
            )
        )
    else:
        assert mock_wait.call_count == wait_calls_at_drag[0] + 1


def test_theme_pack_transition_can_take_longer_than_five_frames():
    from tasks.mirror.select_theme_pack import _confirm_road_map_after_selection

    road_map_results = iter([None] * 6 + [(500, 400)])

    def find_element(target, **_kwargs):
        if target == "mirror/road_in_mir/legend_assets.png":
            return next(road_map_results)
        return None

    with (
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.retry", return_value=None) as mock_retry,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.select_theme_pack.sleep"),
    ):
        mock_auto.find_element.side_effect = find_element

        result = _confirm_road_map_after_selection()

    assert result is True
    assert mock_wait.call_count == 7
    mock_retry.assert_called_once_with(allow_restart=False)


def test_theme_pack_selection_failure_is_bounded_when_drag_does_not_exit_page():
    from tasks.mirror.select_theme_pack import (
        _THEME_PACK_UNCHANGED_ATTEMPTS,
        _confirm_road_map_after_selection,
    )

    def find_element(target, **_kwargs):
        if target == "mirror/theme_pack/theme_pack_features.png":
            return [(100, 200)]
        return None

    with (
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.retry", return_value=None),
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.select_theme_pack.sleep"),
    ):
        mock_auto.find_element.side_effect = find_element

        result = _confirm_road_map_after_selection()

    assert result is False
    assert mock_wait.call_count == _THEME_PACK_UNCHANGED_ATTEMPTS


@pytest.mark.parametrize(
    "selection_indicator",
    [
        "mirror/theme_pack/feature_theme_pack_assets.png",
        "mirror/theme_pack/normal_assets.png",
        "mirror/theme_pack/hard_assets.png",
        "mirror/theme_pack/theme_pack_features.png",
    ],
)
def test_theme_pack_does_not_confirm_road_map_while_selection_indicator_is_visible(
    selection_indicator,
):
    from tasks.mirror.select_theme_pack import _confirm_road_map_after_selection

    selection_visible = True

    def advance_frame():
        nonlocal selection_visible
        if mock_wait.call_count > 1:
            selection_visible = False

    def find_element(target, **_kwargs):
        if target == selection_indicator and selection_visible:
            return (100, 200)
        if target == "mirror/road_in_mir/legend_assets.png":
            return (500, 400)
        return None

    with (
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.retry", return_value=None),
        patch(
            "tasks.mirror.select_theme_pack.wait_for_screenshot",
            side_effect=advance_frame,
        ) as mock_wait,
        patch("tasks.mirror.select_theme_pack.sleep"),
    ):
        mock_auto.find_element.side_effect = find_element

        result = _confirm_road_map_after_selection()

    assert result is True
    assert mock_wait.call_count == 2


def test_theme_pack_selection_returns_failure_after_empty_fallback():
    from tasks.mirror.select_theme_pack import select_theme_pack

    refresh_clicks = 0

    def click_element(target, **kwargs):
        nonlocal refresh_clicks
        if target == "mirror/theme_pack/refresh_assets.png":
            refresh_clicks += 1
            return refresh_clicks <= 4
        return False

    with (
        patch("tasks.mirror.select_theme_pack.cfg") as mock_cfg,
        patch("tasks.mirror.select_theme_pack.theme_list") as mock_theme_list,
        patch("tasks.mirror.select_theme_pack.path_manager") as mock_path_manager,
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot"),
        patch("tasks.mirror.select_theme_pack.sleep"),
        patch("tasks.mirror.select_theme_pack.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.set_win_size = 1080
        mock_path_manager.current_language = "zh_cn"
        mock_theme_list.get_effective_theme_pack_list.return_value = {}
        mock_auto.find_element.side_effect = lambda target, **kwargs: (
            []
            if target == "mirror/theme_pack/theme_pack_features.png"
            else (10, 10)
        )
        mock_auto.click_element.side_effect = click_element

        result = select_theme_pack()

    assert result is False
    assert refresh_clicks == 4
    mock_auto.mouse_drag_down.assert_not_called()
    mock_back_init_menu.assert_called_once_with()


def test_theme_pack_selection_bounds_repeated_recognition_errors():
    from tasks.mirror.select_theme_pack import (
        _MAX_THEME_PACK_ITERATIONS,
        select_theme_pack,
    )

    feature_asset = "mirror/theme_pack/theme_pack_features.png"
    hard_asset = "mirror/theme_pack/hard_assets.png"
    with (
        patch("tasks.mirror.select_theme_pack.cfg") as mock_cfg,
        patch("tasks.mirror.select_theme_pack.theme_list") as mock_theme_list,
        patch("tasks.mirror.select_theme_pack.path_manager") as mock_path_manager,
        patch("tasks.mirror.select_theme_pack.ImageUtils"),
        patch("tasks.mirror.select_theme_pack.auto") as mock_auto,
        patch("tasks.mirror.select_theme_pack.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.select_theme_pack.sleep"),
        patch("tasks.mirror.select_theme_pack.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.set_win_size = 1080
        mock_path_manager.current_language = "zh_cn"
        mock_theme_list.get_effective_theme_pack_list.return_value = {}

        def find_element(target, **kwargs):
            if target == feature_asset and not kwargs.get("take_screenshot"):
                raise RuntimeError("recognition failed")
            if target in (feature_asset, hard_asset):
                return (10, 10)
            return None

        mock_auto.find_element.side_effect = find_element
        mock_auto.click_element.return_value = False

        result = select_theme_pack()

    assert result is False
    assert mock_wait.call_count == _MAX_THEME_PACK_ITERATIONS
    mock_back_init_menu.assert_called_once_with()


@patch("tasks.mirror.select_theme_pack.sleep", return_value=None)
@patch("tasks.mirror.select_theme_pack.back_init_menu")
@patch("tasks.mirror.select_theme_pack.wait_for_screenshot", return_value=None)
@patch("tasks.mirror.select_theme_pack.auto")
@patch("tasks.mirror.select_theme_pack.ImageUtils")
@patch("tasks.mirror.select_theme_pack.path_manager")
@patch("tasks.mirror.select_theme_pack.theme_list")
@patch("tasks.mirror.select_theme_pack.cfg")
def test_theme_pack_difficulty_ocr_accepts_text_list(
    mock_cfg,
    mock_theme_list,
    mock_path_manager,
    mock_image_utils,
    mock_auto,
    _wait,
    mock_back_init_menu,
    _sleep,
):
    from tasks.mirror.select_theme_pack import select_theme_pack

    mock_cfg.set_win_size = 1080
    mock_path_manager.current_language = "zh_cn"
    mock_theme_list.get_effective_theme_pack_list.return_value = {}

    road_map_lookups = 0
    wait_calls_at_road_map = []

    def find_element(target, **kwargs):
        nonlocal road_map_lookups
        if target == "mirror/theme_pack/theme_pack_features.png":
            return [] if mock_auto.mouse_drag_down.called else [(100, 200)]
        if target == "mirror/road_in_mir/legend_assets.png":
            road_map_lookups += 1
            wait_calls_at_road_map.append(_wait.call_count)
            return (500, 400) if road_map_lookups > 1 else None
        return None

    mock_auto.find_element.side_effect = find_element
    mock_auto.find_text_element.return_value = ["normal"]
    mock_auto.click_element.return_value = False
    mock_image_utils.get_bbox.return_value = (10, 20, 30, 40)
    mock_cfg.select_event_pack = True

    with patch("tasks.mirror.select_theme_pack.retry", return_value=None):
        result = select_theme_pack(hard_switch=True, floor=4)

    assert result is True
    mock_auto.find_text_element.assert_called_once()
    mock_auto.mouse_click.assert_called_once_with(20, 30)
    mock_auto.mouse_drag_down.assert_called_once_with(100, 200)
    assert road_map_lookups == 2
    assert wait_calls_at_road_map[0] == 0
    assert wait_calls_at_road_map[1] > wait_calls_at_road_map[0]
    assert wait_calls_at_road_map[1] == _wait.call_count
    mock_back_init_menu.assert_not_called()


@pytest.mark.parametrize("ocr_result", [False, []])
@patch("tasks.mirror.select_theme_pack.sleep", return_value=None)
@patch("tasks.mirror.select_theme_pack.back_init_menu")
@patch("tasks.mirror.select_theme_pack.wait_for_screenshot")
@patch("tasks.mirror.select_theme_pack.auto")
@patch("tasks.mirror.select_theme_pack.ImageUtils")
@patch("tasks.mirror.select_theme_pack.path_manager")
@patch("tasks.mirror.select_theme_pack.theme_list")
@patch("tasks.mirror.select_theme_pack.cfg")
def test_theme_pack_difficulty_ocr_failure_is_bounded(
    mock_cfg,
    mock_theme_list,
    mock_path_manager,
    mock_image_utils,
    mock_auto,
    mock_wait,
    mock_back_init_menu,
    _sleep,
    ocr_result,
):
    from tasks.mirror.select_theme_pack import select_theme_pack

    screenshot_attempts = 0

    def wait_for_screenshot():
        nonlocal screenshot_attempts
        screenshot_attempts += 1
        if screenshot_attempts > 32:
            raise AssertionError("theme-pack selection exceeded its retry limit")

    mock_cfg.set_win_size = 1080
    mock_path_manager.current_language = "zh_cn"
    mock_theme_list.get_effective_theme_pack_list.return_value = {}
    mock_auto.find_element.return_value = None
    mock_auto.click_element.return_value = False
    mock_auto.find_text_element.return_value = ocr_result
    mock_image_utils.get_bbox.return_value = (10, 20, 30, 40)
    mock_wait.side_effect = wait_for_screenshot

    result = select_theme_pack()

    assert result is False
    assert screenshot_attempts == 32
    assert mock_auto.find_text_element.call_count == 5
    assert mock_image_utils.get_bbox.call_count == 10
    mock_back_init_menu.assert_called_once_with()
