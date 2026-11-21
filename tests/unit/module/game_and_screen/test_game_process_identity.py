from unittest.mock import Mock, patch

import pytest

from module.game_and_screen.game import Game


@pytest.mark.parametrize(
    ("process_name", "running_process_name", "expected"),
    [
        ("LimbusCompany.exe", "NotLimbusCompany.exe", False),
        ("LimbusCompany.exe", "limbuscompany.EXE", True),
    ],
)
def test_check_game_alive_requires_case_insensitive_exact_name(
    process_name, running_process_name, expected
):
    game = object.__new__(Game)
    game.process_name = process_name
    game.log = Mock()
    process = Mock(info={"name": running_process_name}, pid=123)

    with patch("module.game_and_screen.game.psutil.process_iter", return_value=[process]):
        assert game.check_game_alive() is expected


def test_check_game_alive_ignores_missing_process_names():
    game = object.__new__(Game)
    game.process_name = "LimbusCompany.exe"
    game.log = Mock()
    unnamed_process = Mock(info={"name": None}, pid=123)

    with patch(
        "module.game_and_screen.game.psutil.process_iter",
        return_value=[unnamed_process],
    ):
        assert game.check_game_alive() is False
