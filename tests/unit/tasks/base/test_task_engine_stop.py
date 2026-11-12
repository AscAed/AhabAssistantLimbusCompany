import pytest

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
