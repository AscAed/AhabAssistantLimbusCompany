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
