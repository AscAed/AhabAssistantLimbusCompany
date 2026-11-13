import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image

from module.automation.automation import Automation
from module.automation.input_handlers import AbstractInput
from module.my_error.my_error import userStopError
from tasks.base.task_engine import Task, TaskEngine, TaskStatus


def test_task_engine_marks_user_stop_as_stopped():
    class StopTask(Task):
        def run(self, engine):
            raise userStopError("用户主动终止程序")

    class FakeThread:
        is_stop = False

    engine = TaskEngine(thread=FakeThread())
    task = StopTask("stop", [])
    engine.add_task(task)
    engine.dispatcher.detect_state = lambda: task.allowed_start_states[0]

    with pytest.raises(userStopError):
        engine.run()

    assert task.status == TaskStatus.STOPPED


def test_task_engine_stop_context_does_not_cancel_another_thread():
    main_worker = SimpleNamespace(is_stop=True)
    automation = object.__new__(Automation)
    automation.screenshot = None
    automation.screenshot_np = None
    automation.last_screenshot_time = 0
    engine = object.__new__(TaskEngine)
    engine.thread = main_worker
    engine._original_take_screenshot = None
    engine._previous_thread_stop_check = None
    engine._thread_stop_check_installed = False
    frame = Image.new("L", (4, 4), color=0)
    results = []
    errors = []

    def other_thread_capture():
        previous = automation._push_thread_stop_check(lambda: False)
        try:
            results.append(automation.take_screenshot())
        except BaseException as exc:
            errors.append(exc)
        finally:
            automation._restore_thread_stop_check(previous)

    with patch("tasks.base.task_engine.auto", automation), patch(
        "module.automation.automation.cfg"
    ) as cfg, patch(
        "module.automation.automation.ScreenShot.take_screenshot", return_value=frame
    ), patch("module.automation.automation.time.sleep"):
        cfg.operation_mode = "foreground_mouse"
        cfg.screenshot_interval = 0.1
        engine._setup_screenshot_hook()
        main_stop_check = automation._get_thread_stop_check()
        assert main_stop_check is not None and main_stop_check() is True

        worker_thread = threading.Thread(target=other_thread_capture)
        worker_thread.start()
        worker_thread.join(timeout=2)
        engine._restore_screenshot_hook()

    assert not worker_thread.is_alive()
    assert results == [frame]
    assert errors == []
    assert automation._get_thread_stop_check() is None


def test_pause_wait_observes_worker_stop_request():
    automation = object.__new__(Automation)
    automation.input_handler = AbstractInput()
    automation.input_handler.is_pause = True
    previous = automation._push_thread_stop_check(lambda: True)
    try:
        with pytest.raises(userStopError):
            automation.input_handler.wait_pause()
    finally:
        automation._restore_thread_stop_check(previous)

    assert automation._get_thread_stop_check() is None
    assert not hasattr(automation.input_handler._stop_context, "callback")


def test_task_engine_records_recovery_failure_without_masking_task_error():
    class FailedTask(Task):
        def run(self, _engine):
            raise ValueError("task failure")

    engine = TaskEngine()
    task = FailedTask("failure", ["MAIN_MENU"])
    engine.add_task(task)
    engine.dispatcher.detect_state = lambda: "MAIN_MENU"
    recovery_error = RuntimeError("recovery failure")

    with patch(
        "tasks.base.back_init_menu.back_init_menu",
        side_effect=recovery_error,
    ):
        with pytest.raises(ValueError, match="task failure"):
            engine.run()

    assert task.error.args == ("task failure",)
    assert task.recovery_error is recovery_error


def test_task_engine_stops_after_task_returns_failure():
    ran = []

    class FailedTask(Task):
        def run(self, _engine):
            ran.append(self.name)
            return False

    class LaterTask(Task):
        def run(self, _engine):
            ran.append(self.name)
            return True

    engine = TaskEngine()
    first = FailedTask("failure", ["MAIN_MENU"])
    engine.add_task(first)
    engine.add_task(LaterTask("later", ["MAIN_MENU"]))
    engine.dispatcher.detect_state = lambda: "MAIN_MENU"

    with patch("tasks.base.back_init_menu.back_init_menu"):
        with pytest.raises(RuntimeError, match="failure"):
            engine.run()

    assert ran == ["failure"]
    assert first.status == TaskStatus.FAILED
