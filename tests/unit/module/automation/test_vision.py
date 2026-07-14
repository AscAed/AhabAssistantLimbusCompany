import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from module.automation.automation import Automation

@pytest.fixture
def mock_automation():
    with patch("module.automation.automation.cfg") as mock_cfg, \
         patch("module.automation.automation.ocr") as mock_ocr:
        mock_cfg.set_win_size = 1440
        mock_cfg.memory_protection = False

        from utils.path_manager import path_manager
        path_manager.current_theme = "default"
        path_manager.current_language = "zh_cn"

        auto = Automation("test_title")
        auto.screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
        auto.location_cache = {}
        auto.img_cache = {}

        # Remove any instance-level method overrides injected by previous tests.
        # Previous tests (e.g. test_wait_until_appear) replace instance methods via
        # `auto.find_element = MagicMock()`, leaving stale entries in the singleton's
        # __dict__ that shadow the real class methods for subsequent tests.
        for attr in ("find_element", "take_screenshot", "_find_element_by_type", "find_image_element"):
            auto.__dict__.pop(attr, None)

        yield auto


def test_get_default_roi(mock_automation):
    # Test shop grids/commodities ROI
    roi_shop = mock_automation.get_default_roi("mirror/shop/buy_icon.png")
    assert roi_shop is not None
    # X from 10% to 95%, Y from 15% to 85% of 1440h / 2560w
    # w = 2560, h = 1440
    # w*0.10 = 256, h*0.15 = 216, w*0.95 = 2432, h*0.85 = 1224
    assert roi_shop == [256, 216, 2432, 1224]

    # Test road nodes ROI
    roi_road = mock_automation.get_default_roi("mirror/road_in_mir/node.png")
    assert roi_road is not None
    assert roi_road == [0, 144, 2560, 1296]

    # Test unknown element
    assert mock_automation.get_default_roi("unknown_target.png") is None

@patch("module.automation.automation.ImageUtils")
def test_location_matching_cache(mock_image_utils, mock_automation):
    target = "test_button.png"

    # Patch _find_element_by_type at the class level — instance-level patching doesn't
    # work reliably with Singleton instances because Python resolves method calls through
    # the class MRO, not the instance __dict__ for bound methods.
    with patch.object(Automation, "_find_element_by_type", autospec=True) as mock_dispatch:

        # First call: cache miss → dispatch returns (100, 200), cache populated.
        mock_dispatch.return_value = (100, 200)
        pos = mock_automation.find_element(target, find_type="image", threshold=0.8)
        assert pos == (100, 200)
        assert mock_automation.location_cache[target] == (100, 200)

        # Second call: cache hit → micro-ROI dispatch still returns a match.
        mock_dispatch.return_value = (100, 200)
        pos2 = mock_automation.find_element(target, find_type="image", threshold=0.8)
        assert pos2 == (100, 200)
        assert mock_automation.location_cache[target] == (100, 200)

        # Third call: micro-ROI dispatch fails, fallback dispatch succeeds → (150, 250).
        mock_dispatch.side_effect = [None, (150, 250)]
        pos3 = mock_automation.find_element(target, find_type="image", threshold=0.8)
        assert pos3 == (150, 250)
        assert mock_automation.location_cache[target] == (150, 250)

        # Fourth call: both dispatches fail → cache entry evicted, returns None.
        mock_dispatch.side_effect = [None, None]
        pos4 = mock_automation.find_element(target, find_type="image", threshold=0.8)
        assert pos4 is None
        assert target not in mock_automation.location_cache

@patch("module.automation.automation.ImageUtils")
def test_find_feature_element_optimization(mock_image_utils, mock_automation):
    target = "mirror/road_in_mir/shop.png"
    # Mock template image load
    mock_image_utils.load_image.return_value = np.zeros((20, 20), dtype=np.uint8)
    
    # We patch cv2.matchTemplate inside the test
    with patch("cv2.matchTemplate") as mock_match, \
         patch("cv2.minMaxLoc") as mock_min_max:
        
        # Mock max correlation value above threshold (e.g., 0.85)
        mock_match.return_value = np.zeros((5, 5))
        mock_min_max.return_value = (0.1, 0.85, (0, 0), (2, 2))
        
        # Should return the center coordinate
        pos = mock_automation.find_feature_element(target)
        assert pos is not None
        # Center = max_loc (2,2) + half-template size (10, 10) = (12, 12) but scale 0.85 is evaluated first
        assert pos == (10, 10)

        # If match value is below threshold (e.g., 0.5) and Canny matching also fails
        mock_min_max.side_effect = [(0.1, 0.5, (0, 0), (2, 2))] * 3 + [(0.1, 0.2, (0, 0), (2, 2))] * 3
        pos_fail = mock_automation.find_feature_element(target)
        assert pos_fail is None
