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

        select_theme_pack()

    assert mock_wait.call_count == _MAX_THEME_PACK_ITERATIONS
    assert sum(call.args[0] == hard_asset for call in mock_auto.click_element.call_args_list) == (
        _MAX_THEME_PACK_ITERATIONS
    )
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

        select_theme_pack()

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
    mock_auto.find_element.return_value = None
    mock_auto.find_element.side_effect = lambda target, **kwargs: (
        [(100, 200)]
        if target == "mirror/theme_pack/theme_pack_features.png"
        else None
    )
    mock_auto.find_text_element.return_value = ["normal"]
    mock_auto.click_element.return_value = False
    mock_image_utils.get_bbox.return_value = (10, 20, 30, 40)
    mock_cfg.select_event_pack = True

    select_theme_pack(hard_switch=True, floor=4)

    mock_auto.find_text_element.assert_called_once()
    mock_auto.mouse_click.assert_called_once_with(20, 30)
    mock_auto.mouse_drag_down.assert_called_once_with(100, 200)
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

    select_theme_pack()

    assert screenshot_attempts == 32
    assert mock_auto.find_text_element.call_count == 5
    assert mock_image_utils.get_bbox.call_count == 10
    mock_back_init_menu.assert_called_once_with()
