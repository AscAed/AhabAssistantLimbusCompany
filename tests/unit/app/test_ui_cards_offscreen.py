import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.farming_interface import FarmingInterfaceLeft
from app.page_card import PageMirror
from app.team_setting_card import CustomizeSettingsModule, ObserveEgoGiftModule, TeamSettingCard


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def test_page_mirror_constructs_offscreen(app):
    widget = PageMirror()
    assert widget is not None
    assert widget.hard_mirror is not None
    assert widget.mirror_keyboard_navigation is not None
    widget.deleteLater()


def test_farming_interface_left_constructs_offscreen(app):
    widget = FarmingInterfaceLeft()
    assert widget is not None
    assert widget.mirror is not None
    assert widget.resonate_with_Ahab is not None
    widget.deleteLater()


def test_team_setting_card_constructs_offscreen(app):
    widget = TeamSettingCard(team_num=1)
    assert widget is not None
    assert widget.sinner_YiSang is not None
    assert widget.sinner_Gregor is not None
    assert widget.burn is not None
    assert widget.blunt is not None
    widget.deleteLater()


def test_customize_settings_module_constructs_offscreen(app):
    widget = CustomizeSettingsModule(team_num=1)
    assert widget is not None
    assert len(widget.starlight_cards) == 10
    assert widget.starlight_1 is widget.starlight_cards[0]
    assert widget.starlight_10 is widget.starlight_cards[-1]
    widget.deleteLater()


def test_observe_ego_gift_module_constructs_offscreen(app):
    widget = ObserveEgoGiftModule(team_num=1)
    assert widget is not None
    assert len(widget.observe_systems) == 11
    assert widget.observe_systems[-1][0] == "general"
    assert len(widget._system_buttons) == 11
    widget.deleteLater()
