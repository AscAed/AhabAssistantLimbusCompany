from unittest.mock import patch

import pytest

from tasks.daily.get_prize import get_mail_prize, get_pass_prize
from tasks.daily.luxcavation import EXP_luxcavation, thread_luxcavation


@pytest.mark.parametrize(
    ("task", "waiter_path", "auto_path"),
    [
        (
            get_pass_prize,
            "tasks.daily.get_prize.wait_for_screenshot",
            "tasks.daily.get_prize.auto",
        ),
        (
            get_mail_prize,
            "tasks.daily.get_prize.wait_for_screenshot",
            "tasks.daily.get_prize.auto",
        ),
        (
            EXP_luxcavation,
            "tasks.daily.luxcavation.wait_for_screenshot",
            "tasks.daily.luxcavation.auto",
        ),
        (
            thread_luxcavation,
            "tasks.daily.luxcavation.wait_for_screenshot",
            "tasks.daily.luxcavation.auto",
        ),
    ],
)
def test_daily_task_stops_when_screenshot_wait_fails(task, waiter_path, auto_path):
    with patch(
        waiter_path, side_effect=RuntimeError("screenshot wait exhausted")
    ) as waiter:
        with patch(auto_path) as mock_auto:
            with pytest.raises(RuntimeError, match="screenshot wait exhausted"):
                task()

    waiter.assert_called_once_with()
    mock_auto.find_element.assert_not_called()
    mock_auto.click_element.assert_not_called()


@patch("tasks.daily.get_prize.retry", return_value=False)
@patch("tasks.daily.get_prize.wait_for_screenshot")
@patch("tasks.daily.get_prize.auto")
def test_pass_prizes_stop_after_retry_restarts_game(
    mock_auto, _wait_for_screenshot, _retry
):
    mock_auto.find_element.return_value = [(10, 20), (30, 40)]

    assert get_pass_prize() is False

    mock_auto.mouse_click.assert_called_once_with(10, 20)
    mock_auto.click_element.assert_not_called()


@patch("tasks.daily.get_prize.sleep", return_value=None)
@patch("tasks.daily.get_prize.retry", side_effect=[None, False])
@patch("tasks.daily.get_prize.wait_for_screenshot")
@patch("tasks.daily.get_prize.auto")
def test_mail_prizes_stop_after_retry_restarts_game(
    mock_auto, _wait_for_screenshot, _retry, _sleep
):
    mock_auto.click_element.side_effect = lambda target, *args, **kwargs: (
        target == "mail/claim_all_assets.png"
    )

    assert get_mail_prize() is False

    assert mock_auto.click_element.call_args_list == [
        (("mail/get_mail_prize_confirm.png",), {}),
        (("mail/claim_all_assets.png",), {}),
    ]
