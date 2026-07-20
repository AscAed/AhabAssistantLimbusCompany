import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from tasks.mirror.in_shop import Shop
from tasks.mirror.mirror import Mirror
from tasks.mirror.search_road import identify_nodes, identify_road
from module.config import TeamSetting

@pytest.fixture
def mock_team_setting():
    setting = MagicMock()
    setting.sinner_order = [1, 2, 3]
    setting.team_number = 1
    setting.team_system = 1
    setting.avoid_skill_3 = False
    setting.opening_bonus = False
    setting.use_starlight = False
    setting.reward_cards = []
    setting.reward_cards_select = []
    setting.opening_items = []
    setting.opening_items_select = []
    setting.opening_items_system = 0
    setting.re_formation_each_floor = False
    setting.second_system = False
    setting.second_system_select = 0
    setting.second_system_setting = 0
    setting.observe_ego_gift = True
    setting.observe_ego_gift_selected = ["bleed_3_1_1"]
    setting.defense_first_round = False
    setting.use_custom_theme_pack_weight = False
    setting.shop_strategy = 0
    setting.fixed_team_use = False
    setting.do_not_heal = False
    return setting

@patch("tasks.mirror.in_shop.retry", return_value=True)
@patch("tasks.mirror.in_shop.sleep", return_value=None)
@patch("tasks.mirror.in_shop.auto")
@patch("tasks.mirror.in_shop.cfg")
@patch("tasks.mirror.in_shop.ImageUtils")
def test_shop_fusion_aggressive(mock_image_utils, mock_cfg, mock_auto, mock_sleep, mock_retry, mock_team_setting):
    mock_cfg.set_win_size = 1440
    shop = Shop(mock_team_setting)

    # fuse_label anchor at (1000, 100).
    # first_gift = (anchor_x + 95, anchor_y + 135) = (1095, 235)
    # Grid cell centres (scale=1.0):
    #   row 0, col 0-2: x = 1095, 1285, 1475 / y = 235
    # gift_bbox = [int(cx-90), int(cy-90), int(cx+90), int(cy+90)]
    LEVEL3_CELLS = {
        (1005, 145, 1185, 325): (1095, 235),
        (1195, 145, 1375, 325): (1285, 235),
        (1385, 145, 1565, 325): (1475, 235),
    }

    def find_element_side_effect(target, *args, **kwargs):
        if "fuse_label.png" in target:
            return [(1000, 100)]
        if "Level_III.png" in target:
            my_crop = kwargs.get("my_crop")
            if my_crop:
                bbox = tuple(int(v) for v in my_crop)
                if bbox in LEVEL3_CELLS:
                    return LEVEL3_CELLS[bbox]
        # Trigger the confirm break path
        if "ego_gift_get_confirm_assets.png" in target:
            return (720, 600)
        return None

    mock_auto.find_element.side_effect = find_element_side_effect
    mock_auto.take_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_auto.mouse_to_blank.return_value = None
    mock_auto.click_element.return_value = False
    mock_auto.find_language_text.return_value = None

    shop.fuse_useless_gifts_aggressive()

    # Verify it selected exactly 3 gifts — one click per Level III cell
    clicked_coords = [call.args for call in mock_auto.mouse_click.call_args_list]
    gift_clicks = [(x, y) for x, y in clicked_coords if (x, y) in LEVEL3_CELLS.values()]
    assert len(gift_clicks) == 3, f"Expected 3 gift clicks, got {len(gift_clicks)}: {clicked_coords}"

@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
@patch("tasks.mirror.mirror.ImageUtils")
def test_select_observe_ego_gift(mock_image_utils, mock_cfg, mock_auto, mock_team_setting):
    mock_cfg.set_win_size = 1440
    mirror = Mirror(mock_team_setting, 1)
    
    # Mock system/protected assets path finding
    mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (200, 100) if "observe_burn_assets.png" in target else ((500, 300) if "Level_III.png" in target else None)
    mock_auto.take_screenshot.return_value = np.zeros((1440, 2560))
    
    # gift_box bbox: [left, top, right, bottom]
    mock_image_utils.get_bbox.side_effect = lambda img: [100, 200, 1200, 1000]
    
    # Execute the method
    # Note: mirror.observe_ego_gift_selected is ['bleed_3_1_1'] (Level III, row 1, col 1)
    # The Level III anchor point is mocked at (500, 300).
    # Since level tag is Level_III, target coordinates:
    # target_x = level_p[0] + (col - 1)*166 = 500 + 0 = 500
    # target_y = level_p[1] + 80 + (row - 1)*160 = 300 + 80 + 0 = 380
    # 380 is within gift_box Y bounds (200 to 1000). Thus, it should click immediately without scrolling.
    mirror.select_observe_ego_gift()
    
    # Verify click was made near (500, 380)
    mock_auto.mouse_click.assert_any_call(500, 380)

@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
@patch("tasks.mirror.mirror.ImageUtils")
def test_select_observe_ego_gift_bleed_fallback(mock_image_utils, mock_cfg, mock_auto, mock_team_setting):
    # Tests the fallback behaviour when burn assets are missing but bleed assets are found.
    mock_cfg.set_win_size = 1440
    mirror = Mirror(mock_team_setting, 1)
    
    # Mock system/protected assets path finding:
    # observe_burn_assets.png is not found, but observe_bleed_assets.png is found at (310, 100)
    # my_scale = 1.0 (since 1440 / 1440 = 1.0)
    # expected benchmark_point = (310 - 110, 100) = (200, 100)
    mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
        None if "observe_burn_assets.png" in target 
        else ((310, 100) if "observe_bleed_assets.png" in target 
        else ((500, 300) if "Level_III.png" in target 
        else None))
    )
    mock_auto.take_screenshot.return_value = np.zeros((1440, 2560))
    
    # gift_box bbox: [left, top, right, bottom]
    mock_image_utils.get_bbox.side_effect = lambda img: [100, 200, 1200, 1000]
    
    # Execute the method
    mirror.select_observe_ego_gift()
    
    # Verify click was made near (500, 380) for the gift selection
    mock_auto.mouse_click.assert_any_call(500, 380)
    
    # And check that the system tabs are clicked correctly using the fallback benchmark point (200, 100)
    # bleed index = 1 in observe_system
    # system_index is determined by: [k for k, v in observe_system.items() if v == file_system][0]
    # for 'bleed', it is index 1.
    # So click positions should be:
    # 1. benchmark_point[0] + 110 * (system_index + 1) * my_scale -> 200 + 110 * 2 = 420
    # 2. benchmark_point[0] + 110 * (system_index - 1) * my_scale -> 200 + 110 * 0 = 200
    # 3. benchmark_point[0] + 110 * system_index * my_scale -> 200 + 110 * 1 = 310
    mock_auto.mouse_click.assert_any_call(420, 100)
    mock_auto.mouse_click.assert_any_call(200, 100)
    mock_auto.mouse_click.assert_any_call(310, 100)

@patch("tasks.mirror.search_road.auto")
@patch("tasks.mirror.search_road.cfg")
@patch("cv2.dnn.blobFromImage")
@patch("onnxruntime.InferenceSession")
def test_identify_nodes_roi(mock_onnx, mock_blob, mock_cfg, mock_auto):
    mock_cfg.set_win_size = 1440
    mock_auto.screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    # Mock ONNX run output: one detection of a shop at index 5 in CLASSES
    mock_session = MagicMock()
    # YOLO format is transposed in identify_nodes: shape (1, 11, 25200)
    # Center = (320, 320), size = (40, 40), conf of class 5 (shop) = 0.9
    mock_output = np.zeros((1, 11, 25200))
    mock_output[0, :4, 0] = [320, 320, 40, 40]
    mock_output[0, 9, 0] = 0.9 # index 5 (shop) class score. 4 (box) + 5 (class index) = 9.
    mock_session.run.return_value = [mock_output]
    mock_onnx.return_value = mock_session
    
    # Run node detection with bus_x = 100
    nodes = identify_nodes(100)
    
    # Verify that nodes were returned and adjusted for the ROI offsets
    assert nodes is not None
    assert len(nodes) > 0
    assert nodes[0][0] == "shop"
    # Adjusted coords should include ROI offsets (x_min, y_min)
    assert nodes[0][1][0] > 0
    assert nodes[0][1][1] > 0
