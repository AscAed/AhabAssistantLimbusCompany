from unittest.mock import patch

from module.config.config_typing import TeamSetting
from tasks import all_systems
from tasks.mirror.in_shop import Shop, _is_protected_coordinate, wait_for_screenshot


def test_shop_constructor_builds_sell_list_from_team_setting():
    team = TeamSetting(team_system=0, system_bleed=True, system_charge=True)
    shop = Shop(team)

    assert shop.system == all_systems[0]
    assert "bleed" in shop.shop_sell_list
    assert "charge" in shop.shop_sell_list


def test_shop_constructor_keeps_team_system_out_of_sell_list():
    team = TeamSetting(team_system=0, system_burn=True)
    shop = Shop(team)

    assert all_systems[0] not in shop.shop_sell_list


def test_wait_for_screenshot_retries_until_success():
    with patch("tasks.mirror.in_shop.auto") as mock_auto:
        expected = object()
        mock_auto.take_screenshot.side_effect = [None, None, expected]

        assert wait_for_screenshot() is expected

    assert mock_auto.take_screenshot.call_count == 3


def test_wait_for_screenshot_raises_after_bounded_attempts():
    with patch("tasks.mirror.in_shop.auto") as mock_auto:
        mock_auto.take_screenshot.return_value = None

        try:
            wait_for_screenshot(max_attempts=2)
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected RuntimeError")

    assert mock_auto.take_screenshot.call_count == 2


def test_is_protected_coordinate_honors_scale_and_offset():
    assert _is_protected_coordinate((150, 100), (100, 100), scale=1.0, x_offset=50)
    assert not _is_protected_coordinate((250, 100), (100, 100), scale=1.0, x_offset=50)


def test_processing_coordinates_sorts_dedupes_and_filters_aggressive_rows():
    team = TeamSetting(team_system=0)
    shop = Shop(team)
    shop.fuse_aggressive_switch = True
    shop.the_first_line_position = 200

    points = [(300, 100), (100, 400), (104, 404), (200, 500)]
    with patch("tasks.mirror.in_shop.cfg") as mock_cfg:
        mock_cfg.set_win_size = 1440
        result = shop._processing_coordinates(points)

    assert (100, 400) in result
    assert (104, 404) not in result
    assert (200, 500) in result
    assert (300, 100) not in result


@patch("tasks.mirror.in_shop.retry", return_value=True)
@patch("tasks.mirror.in_shop.sleep", return_value=None)
@patch("tasks.mirror.in_shop.auto")
@patch("tasks.mirror.in_shop.cfg")
def test_fuse_useless_gifts_no_gifts_returns_cleanly(mock_cfg, mock_auto, mock_sleep, mock_retry):
    mock_cfg.set_win_size = 1440
    mock_auto.take_screenshot.return_value = object()
    mock_auto.find_element.return_value = None

    team = TeamSetting(team_system=0)
    shop = Shop(team)
    shop.fuse_useless_gifts()

    mock_auto.mouse_click_blank.assert_called_once_with(times=3)
