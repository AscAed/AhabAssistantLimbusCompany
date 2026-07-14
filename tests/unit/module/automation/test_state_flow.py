import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from module.automation.automation import Automation, GameState, PageStateDispatcher
from tasks.mirror.mirror import Mirror
from module.config import TeamSetting

@pytest.fixture
def mock_automation():
    with patch("module.automation.automation.cfg") as mock_cfg, \
         patch("module.automation.automation.ocr") as mock_ocr:
        mock_cfg.set_win_size = 1440
        mock_cfg.memory_protection = False
        
        # Initialise automation instance with a mock title
        auto = Automation("test_title")
        auto.screenshot = MagicMock()
        auto.location_cache = {}
        auto.img_cache = {}
        yield auto

def test_wait_until_appear(mock_automation):
    # Mock find_element to fail first two times, then succeed
    mock_automation.take_screenshot = MagicMock(return_value=MagicMock())
    mock_automation.find_element = MagicMock(side_effect=[None, None, (100, 200)])

    with patch("time.sleep") as mock_sleep:
        pos = mock_automation.wait_until_appear("test_element", timeout=2, poll_interval=0.1)
        assert pos == (100, 200)
        assert mock_automation.find_element.call_count == 3
        mock_sleep.assert_called_with(0.1)

def test_page_state_dispatcher(mock_automation):
    dispatcher = PageStateDispatcher(mock_automation)

    # Mock find_element to return True for battle assets
    mock_automation.take_screenshot = MagicMock()
    mock_automation.find_element = MagicMock(side_effect=lambda target, **kwargs: target == "battle/in_mirror_assets.png")

    state = dispatcher.detect_state()
    assert state == GameState.BATTLE

    # Mock another state (Shop)
    mock_automation.find_element = MagicMock(side_effect=lambda target, **kwargs: target == "mirror/shop/shop_coins_assets.png")
    state = dispatcher.detect_state()
    assert state == GameState.SHOP

    # Unknown state
    mock_automation.find_element = MagicMock(return_value=None)
    state = dispatcher.detect_state()
    assert state == GameState.UNKNOWN

@patch("tasks.mirror.mirror.auto")
@patch("module.config.cfg")
def test_check_and_recover_process(mock_cfg, mock_auto):
    # Initialise a mock TeamSetting object
    team_setting = MagicMock()
    team_setting.sinner_order = []
    team_setting.team_number = 1
    team_setting.team_system = 0
    team_setting.avoid_skill_3 = False
    team_setting.opening_bonus = []
    team_setting.use_starlight = False
    team_setting.reward_cards = False
    team_setting.reward_cards_select = []
    team_setting.opening_items = False
    team_setting.opening_items_select = []
    team_setting.opening_items_system = 0
    team_setting.re_formation_each_floor = False
    team_setting.second_system = False
    team_setting.second_system_select = 0
    team_setting.second_system_setting = 0
    team_setting.observe_ego_gift = False
    team_setting.observe_ego_gift_selected = []
    team_setting.defense_first_round = False
    team_setting.use_custom_theme_pack_weight = False
    team_setting.shop_strategy = 0
    team_setting.fixed_team_use = False
    team_setting.do_not_heal = False

    mirror = Mirror(team_setting, 1)

    # 1. Test case when game is not running (crashed)
    with patch("utils.utils.check_game_running", return_value=False), \
         patch("tasks.base.retry.kill_game") as mock_kill, \
         patch("tasks.base.retry.restart_game") as mock_restart, \
         patch.object(mirror, "road_to_mir") as mock_road:
        
        recovered = mirror.check_and_recover_process()
        assert recovered is True
        mock_kill.assert_called_once()
        mock_restart.assert_called_once()
        mock_road.assert_called_once()

    # 2. Test case when game is running and no issues
    with patch("utils.utils.check_game_running", return_value=True):
        mock_auto.find_element.return_value = None
        recovered = mirror.check_and_recover_process()
        assert recovered is False

    # 3. Test case when network connection issue is detected
    with patch("utils.utils.check_game_running", return_value=True), \
         patch("tasks.base.retry.retry", return_value=True) as mock_retry, \
         patch.object(mirror, "road_to_mir") as mock_road:
        
        # Mock auto.find_element to detect "base/retry.png"
        mock_auto.find_element.side_effect = lambda target, **kwargs: target == "base/retry.png"
        recovered = mirror.check_and_recover_process()
        assert recovered is True
        mock_retry.assert_called_once()
