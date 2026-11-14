from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from ruamel.yaml import YAML

from module.config.config import Config
from module.config.config_typing import ConfigModel

LEGACY_AFTER_COMPLETION_VERSION = 1772205659


def _upgrade_without_legacy_backup_files(
    config, loaded_config, version=LEGACY_AFTER_COMPLETION_VERSION
):
    with patch.object(Path, "exists", return_value=False):
        config._old_version_cfg_upgrade(version, loaded_config)


def _config_with_current_defaults():
    config = object.__new__(Config)
    config.config = SimpleNamespace(
        after_completion_actions=[],
        after_completion_power_action="none",
        set_win_position="right_bottom",
        teams_be_select=[],
    )
    return config


@pytest.mark.parametrize(
    ("legacy_value", "expected_actions", "expected_power_action"),
    [
        (0, [], "none"),
        (3, [], "shutdown"),
        (4, ["exit_game"], "none"),
        (6, ["exit_game", "exit_aalc"], "none"),
    ],
)
def test_legacy_after_completion_migrates_loaded_value(
    legacy_value, expected_actions, expected_power_action
):
    config = _config_with_current_defaults()
    loaded_config = {"after_completion": legacy_value}

    _upgrade_without_legacy_backup_files(config, loaded_config)

    assert loaded_config["after_completion_actions"] == expected_actions
    assert loaded_config["after_completion_power_action"] == expected_power_action


def test_legacy_migration_preserves_existing_new_values():
    config = _config_with_current_defaults()
    loaded_config = {
        "after_completion": 3,
        "after_completion_actions": ["exit_aalc"],
        "after_completion_power_action": "hibernate",
    }

    _upgrade_without_legacy_backup_files(config, loaded_config)

    assert loaded_config["after_completion_actions"] == ["exit_aalc"]
    assert loaded_config["after_completion_power_action"] == "hibernate"


def test_legacy_migration_only_fills_missing_new_field():
    config = _config_with_current_defaults()
    loaded_config = {
        "after_completion": 4,
        "after_completion_actions": ["exit_aalc"],
    }

    _upgrade_without_legacy_backup_files(config, loaded_config)

    assert loaded_config["after_completion_actions"] == ["exit_aalc"]
    assert loaded_config["after_completion_power_action"] == "none"


@pytest.mark.parametrize("legacy_value", [True, False])
def test_legacy_boolean_window_position_migrates_to_free(legacy_value):
    example_path = Path(__file__).resolve().parents[4] / "assets/config/config.example.yaml"
    loaded_config = YAML().load(example_path.read_text(encoding="utf-8"))
    loaded_config["set_win_position"] = legacy_value
    config = object.__new__(Config)

    _upgrade_without_legacy_backup_files(config, loaded_config, version=0)

    assert loaded_config["set_win_position"] == "free"
    ConfigModel(**loaded_config)


def test_legacy_migration_preserves_window_position_preset():
    config = object.__new__(Config)
    loaded_config = {"set_win_position": "center"}

    _upgrade_without_legacy_backup_files(config, loaded_config, version=0)

    assert loaded_config["set_win_position"] == "center"


def test_legacy_history_migrates_every_selected_team():
    config = _config_with_current_defaults()
    loaded_config = {
        "teams_be_select": [False, False, True],
        "team3_setting": {"choose_opening_bonus": False},
        "team3_remark_name": "three",
        "team3_history": {
            "total_mirror_time_hard": [100, 200, 300, 400],
            "mirror_hard_count": 4,
            "total_mirror_time_normal": [10, 20, 30, 40],
            "mirror_normal_count": 4,
            "other_history": "preserved",
        },
    }

    _upgrade_without_legacy_backup_files(config, loaded_config, version=0)

    team = loaded_config["teams"]["3"]
    assert team["total_mirror_time_hard"] == [250, 250, 250]
    assert team["total_mirror_time_normal"] == [25, 25, 25]
    assert team["mirror_hard_count"] == 4
    assert team["mirror_normal_count"] == 4
    assert team["other_history"] == "preserved"
