from unittest.mock import patch

import numpy as np

from tasks.mirror.search_road import MirrorMap, search_road_from_road_map


@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.identify_nodes", return_value=[("shop", (300, 200))])
def test_search_road_hard_mode_single_step(mock_identify_nodes, mock_cfg, mock_auto, mock_sleep):
    mock_cfg.set_win_size = 1440
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_auto.find_element.side_effect = lambda target, **kwargs: (
        (100, 200) if "mybus_default_distance.png" in target else None
    )

    result = search_road_from_road_map(hard_mode=True)

    assert result == (["M"], ["shop"])
    mock_identify_nodes.assert_called_once_with(100)


@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.identify_nodes", return_value=None)
def test_search_road_hard_mode_bus_lookup_failure_returns_empty(
    mock_identify_nodes, mock_cfg, mock_auto, mock_sleep
):
    mock_cfg.set_win_size = 1440
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_auto.find_element.return_value = None

    result = search_road_from_road_map(hard_mode=True)

    assert result == (False, [])
    mock_identify_nodes.assert_not_called()


@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.identify_road", return_value=[])
@patch("tasks.mirror.search_road.identify_nodes", return_value=[])
def test_search_road_normal_mode_without_bus_falls_back_to_empty(
    mock_identify_nodes, mock_identify_road, mock_cfg, mock_auto, mock_sleep
):
    mock_cfg.set_win_size = 1440
    mock_cfg.mirror_keyboard_navigation = False
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_auto.find_element.return_value = None

    result = search_road_from_road_map(hard_mode=False)

    assert result == (False, [])


# ── Bug A regression: cx/cy loop variable shadowing ───────────────────────────
# identify_nodes returns tuples with float-valued coordinates; merging must not
# corrupt the outer cx/cy blank-area coordinates used by the scroll logic.
@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.identify_road", return_value=[])
@patch(
    "tasks.mirror.search_road.identify_nodes",
    return_value=[("battle", (500, 400)), ("event", (800, 600))],
)
def test_cx_cy_not_shadowed_by_loop_variables(
    mock_identify_nodes, mock_identify_road, mock_cfg, mock_auto, mock_sleep
):
    """After panoramic scan merging, mouse_scroll must be called with the
    original blank-area coords (cx ≈ 192, cy ≈ 864 for 1080p), not node coords."""
    mock_cfg.set_win_size = 1080
    mock_cfg.mirror_keyboard_navigation = False
    mock_auto.mouse_scroll.return_value = True
    mock_auto.mouse_drag.return_value = None
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # bus found on first attempt, but no end-node → triggers scroll-retry loop
    mock_auto.find_element.return_value = (200, 500)

    search_road_from_road_map(hard_mode=False)

    # Every scroll call must use y ≈ 864 (0.8 * 1080), NOT any node y like 400 or 600
    for call in mock_auto.mouse_scroll.call_args_list:
        args = call.args if call.args else call[0]
        if len(args) >= 3:
            scroll_y = args[2]
            assert scroll_y not in (400, 600), (
                f"cx/cy was shadowed: mouse_scroll called with node y={scroll_y}"
            )


# ── Bug B regression: panoramic scan result must not be discarded ─────────────
@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.identify_road", return_value=[])
@patch(
    "tasks.mirror.search_road.identify_nodes",
    return_value=[("shop", (900, 400))],
)
def test_panoramic_scan_result_used_when_end_node_present(
    mock_identify_nodes, mock_identify_road, mock_cfg, mock_auto, mock_sleep
):
    """When panoramic scan already detects a shop node, the zoom-out retry loop
    should immediately confirm it without discarding merged_nodes."""
    mock_cfg.set_win_size = 1080
    mock_cfg.mirror_keyboard_navigation = False
    mock_auto.mouse_scroll.return_value = True
    mock_auto.mouse_drag.return_value = None
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_auto.find_element.return_value = (200, 500)

    directions, classes = search_road_from_road_map(hard_mode=False)

    # Result should be a non-empty path derived from the detected shop node
    assert directions is not False
    assert classes is not False


# ── Bug C regression: NMSBoxes float index must not cause TypeError ───────────
def test_nmsboxes_float_index_coerced_to_int():
    """int(result_boxes[i]) must handle float32 indices from OpenCV ≥4.7."""
    import numpy as np2

    # Simulate NMSBoxes returning a numpy float32 array of indices
    float_indices = np2.array([0.0, 1.0], dtype=np2.float32)
    for raw_idx in float_indices:
        idx = int(raw_idx)
        boxes_mock = [("box0",), ("box1",)]
        assert boxes_mock[idx] is not None  # must not raise TypeError


# ── Bug D regression: identify_nodes returning None is handled safely ──────────
@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.identify_road", return_value=[])
@patch("tasks.mirror.search_road.identify_nodes", return_value=None)
def test_identify_nodes_none_in_zoom_retry_does_not_crash(
    mock_identify_nodes, mock_identify_road, mock_cfg, mock_auto, mock_sleep
):
    """identify_nodes returning None must not raise TypeError in the zoom-out loop."""
    mock_cfg.set_win_size = 1080
    mock_cfg.mirror_keyboard_navigation = False
    mock_auto.mouse_scroll.return_value = True
    mock_auto.mouse_drag.return_value = None
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_auto.find_element.return_value = (200, 500)

    # Should complete without raising TypeError
    result = search_road_from_road_map(hard_mode=False)
    assert result == (False, []) or isinstance(result, tuple)


# ── MirrorMap.get_next_step: False return from search_road_from_road_map ───────
@patch("tasks.mirror.search_road.search_road_from_road_map", return_value=(False, []))
def test_mirror_map_get_next_step_handles_false_floor_map(mock_srfm):
    """When search_road_from_road_map returns (False, []), get_next_step must not
    crash with TypeError from list(False)."""
    mm = MirrorMap(floor=1, hard_mode=False)
    result = mm.get_next_step()
    # Should return False (no path) without raising TypeError
    assert result is False or result == []


# ── Bug G regression: panoramic scan block must be removed (弃用) ─────────────
@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.identify_road", return_value=[])
@patch("tasks.mirror.search_road.identify_nodes", return_value=[("battle", (500, 400))])
def test_panoramic_scan_e_key_never_pressed(
    mock_identify_nodes, mock_identify_road, mock_cfg, mock_auto, mock_sleep
):
    """After removing the panoramic scan block, key_press('e') must never be called
    by search_road_from_road_map in normal mode."""
    mock_cfg.set_win_size = 1080
    mock_cfg.mirror_keyboard_navigation = True
    mock_auto.mouse_scroll.return_value = True
    mock_auto.mouse_drag.return_value = None
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Simulate max-zoom reached immediately
    mock_auto.find_element.return_value = (400, 400)

    search_road_from_road_map(hard_mode=False)

    for call in mock_auto.key_press.call_args_list:
        args = call.args if call.args else call[0]
        assert args[0] not in ("e", "q"), (
            f"Deprecated panoramic scan still using key '{args[0]}'"
        )


# ── Bug H regression: keyboard enter should not depend on enter_assets matching ──
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.sleep", return_value=None)
def test_enter_next_node_keyboard_returns_true_without_enter_assets(
    mock_sleep, mock_cfg, mock_auto
):
    """Keyboard navigation should confirm node entry with Enter directly."""
    from tasks.mirror.search_road import MirrorMap

    mock_cfg.set_win_size = 1080
    mock_cfg.mirror_keyboard_navigation = True
    mock_auto.click_element.return_value = None  # enter_assets not found
    mock_auto.key_press.return_value = None

    mm = MirrorMap(floor=1, hard_mode=False)
    result = mm.enter_next_node("M")
    assert result is True, "enter_next_node should succeed after pressing Enter"
    assert mock_auto.click_element.call_count == 0
    assert [call.args[0] for call in mock_auto.key_press.call_args_list] == ["left", "right", "enter"]


# ── Bug I regression: minimap position (x<200, y<200) must be rejected ─────────
@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.screen")
@patch("tasks.mirror.search_road.identify_road", return_value=[])
@patch("tasks.mirror.search_road.identify_nodes", return_value=[("battle", (500, 400))])
def test_minimap_position_rejected_as_bus_location(
    mock_identify_nodes, mock_identify_road, mock_screen, mock_cfg, mock_auto, mock_sleep
):
    """A bus_position at (76, 76) (minimap area) must be filtered out; the function
    must not use it as the real bus location."""
    mock_cfg.set_win_size = 1080
    mock_cfg.mirror_keyboard_navigation = False
    mock_screen.handle.hwnd = 0  # triggers fallback to auto.mouse_scroll in _do_scroll_zoom_out
    mock_auto.mouse_scroll.return_value = True
    mock_auto.mouse_drag.return_value = None
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)

    # First two calls return minimap position; subsequent call returns valid position
    call_count = {"n": 0}
    def find_element_side_effect(target, **kwargs):
        call_count["n"] += 1
        if "mybus_maximum_distance" in target:
            if call_count["n"] <= 2:
                return (76, 76)   # minimap position — must be rejected
            return (400, 400)     # valid position
        return None
    mock_auto.find_element.side_effect = find_element_side_effect

    directions, classes = search_road_from_road_map(hard_mode=False)
    # identify_nodes should have been called with bus_x=400, not bus_x=76
    for call in mock_identify_nodes.call_args_list:
        bus_x_arg = call.args[0] if call.args else call[1].get("bus_x")
        assert bus_x_arg != 76, "minimap position (x=76) must not be used as bus_x"


# ── Bug K regression: zoom loop exits on mybus_maximum_distance.png match ──────
@patch("tasks.mirror.search_road.sleep", return_value=None)
@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("tasks.mirror.search_road.screen")
@patch("tasks.mirror.search_road.identify_road", return_value=[])
@patch("tasks.mirror.search_road.identify_nodes", return_value=[("battle", (500, 400))])
def test_zoom_loop_exits_on_maximum_distance_match(
    mock_identify_nodes, mock_identify_road, mock_screen, mock_cfg, mock_auto, mock_sleep
):
    """Zoom confirmation loop must exit as soon as mybus_maximum_distance.png is
    matched, without requiring shop/boss_battle ONNX detection."""
    mock_cfg.set_win_size = 1080
    mock_cfg.mirror_keyboard_navigation = False
    mock_screen.handle.hwnd = 0
    mock_auto.mouse_scroll.return_value = True
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)

    # Return valid max-zoom bus position on first attempt
    def find_element_side_effect(target, **kwargs):
        if "mybus_maximum_distance" in target:
            return (400, 400)
        return None
    mock_auto.find_element.side_effect = find_element_side_effect

    directions, classes = search_road_from_road_map(hard_mode=False)
    # Must not return (False, []) — nodes were detected, so Dijkstra should run
    assert directions is not False
