from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pytest
from PIL import Image
from rapidocr.utils.output import RapidOCROutput

from module.my_error.my_error import userStopError
from module.ocr.ocr import OCR, OCRExecutionError
from tasks.base import script_task_scheme
from tasks.base.make_enkephalin_module import get_current_enkephalin
from tasks.tools.production_module import ProductionModule, ProductionWork


@patch("utils.image_utils.ImageUtils.crop", return_value=np.zeros((4, 4), dtype=np.uint8))
@patch("utils.image_utils.ImageUtils.get_bbox", return_value=(0, 0, 4, 4))
@patch("utils.image_utils.ImageUtils.load_image", return_value=object())
@patch("tasks.base.make_enkephalin_module.auto")
def test_get_current_enkephalin_stops_after_bounded_capture_failures(
    mock_auto, _load_image, _get_bbox, _crop
):
    mock_auto.take_screenshot.side_effect = [None] * 5 + [
        AssertionError("unbounded screenshot retry")
    ]
    mock_auto.screenshot = None
    with patch.object(OCR, "run", return_value=RapidOCROutput()):
        assert get_current_enkephalin() is None

    assert mock_auto.take_screenshot.call_count == 5


@patch("utils.image_utils.ImageUtils.crop", return_value=np.zeros((4, 4), dtype=np.uint8))
@patch("utils.image_utils.ImageUtils.get_bbox", return_value=(0, 0, 4, 4))
@patch("utils.image_utils.ImageUtils.load_image", return_value=object())
@patch("tasks.base.make_enkephalin_module.auto")
def test_get_current_enkephalin_propagates_screenshot_failure(
    mock_auto, _load_image, _get_bbox, _crop
):
    error = RuntimeError("screenshot failed")
    mock_auto.take_screenshot.side_effect = error

    with patch.object(OCR, "run") as mock_ocr:
        with pytest.raises(RuntimeError) as raised:
            get_current_enkephalin()

    assert raised.value is error
    mock_auto.take_screenshot.assert_called_once_with()
    mock_ocr.assert_not_called()


@patch("utils.image_utils.ImageUtils.crop", return_value=np.zeros((4, 4), dtype=np.uint8))
@patch("utils.image_utils.ImageUtils.get_bbox", return_value=(0, 0, 4, 4))
@patch("utils.image_utils.ImageUtils.load_image", return_value=object())
@patch("tasks.base.make_enkephalin_module.auto")
def test_get_current_enkephalin_propagates_ocr_execution_failure(
    mock_auto, _load_image, _get_bbox, _crop
):
    mock_auto.take_screenshot.return_value = Image.new("L", (4, 4), color=0)
    mock_auto.screenshot = Image.new("L", (4, 4), color=0)
    error = OCRExecutionError("engine failed")

    with patch.object(OCR, "run", side_effect=error):
        with pytest.raises(OCRExecutionError) as raised:
            get_current_enkephalin()

    assert raised.value is error


def test_production_worker_reports_ocr_execution_failure():
    worker = ProductionWork()
    worker._set_win = Mock()
    worker._back_init_menu_with_tool_policy = Mock(return_value=True)
    errors = []
    worker.error_occurred.connect(errors.append)

    with patch.object(script_task_scheme, "init_game"), patch(
        "tasks.tools.production_module.make_enkephalin_module"
    ), patch(
        "tasks.tools.production_module.get_current_enkephalin",
        side_effect=OCRExecutionError("engine failed"),
    ), patch("tasks.tools.production_module.auto") as mock_auto:
        mock_auto.find_element.return_value = True
        worker.run()

    assert worker.production_running is False
    assert len(errors) == 1
    assert "OCR" in errors[0]
    assert worker.failure_message == errors[0]


def test_production_worker_reports_screenshot_capture_failure():
    worker = ProductionWork()
    worker._set_win = Mock()
    worker._back_init_menu_with_tool_policy = Mock(return_value=True)
    errors = []
    worker.error_occurred.connect(errors.append)
    capture_error = RuntimeError("后台模式连续截图失败，已安全停止")

    with patch.object(script_task_scheme, "init_game"), patch(
        "tasks.tools.production_module.make_enkephalin_module"
    ), patch(
        "tasks.tools.production_module.get_current_enkephalin",
        side_effect=capture_error,
    ), patch("tasks.tools.production_module.auto") as mock_auto:
        mock_auto.find_element.return_value = True
        worker.run()

    assert worker.production_running is False
    assert errors == [f"自动换饼执行失败: {capture_error}"]
    assert worker.failure_message == errors[0]


def test_production_worker_stops_after_lunacy_asset_wait_timeout():
    worker = ProductionWork()
    worker._set_win = Mock()
    worker._back_init_menu_with_tool_policy = Mock(return_value=True)
    errors = []
    worker.error_occurred.connect(errors.append)

    with patch.object(script_task_scheme, "init_game"), patch(
        "tasks.tools.production_module.make_enkephalin_module"
    ), patch("tasks.tools.production_module.auto") as mock_auto, patch(
        "tasks.tools.production_module.monotonic", side_effect=[0.0, 0.0, 91.0]
    ):
        mock_auto.find_element.side_effect = [False, False, AssertionError("unbounded wait")]
        worker.run()

    assert worker.production_running is False
    assert worker.failure_message == "自动换饼执行失败: lunacy 资源页面确认超时（90秒）"
    assert errors == [worker.failure_message]
    assert mock_auto.find_element.call_count == 2
    mock_auto.click_element.assert_called_once_with("enkephalin/use_lunacy_assets.png")
    mock_auto.sleep_with_stop_check.assert_called_once_with(0.5)


def test_production_worker_stop_during_lunacy_asset_wait_prevents_retry_click():
    worker = ProductionWork()
    worker._set_win = Mock()
    worker._back_init_menu_with_tool_policy = Mock(return_value=True)
    errors = []
    worker.error_occurred.connect(errors.append)

    def stop_worker(_seconds):
        worker.stop()
        raise userStopError("stop requested")

    with patch.object(script_task_scheme, "init_game"), patch(
        "tasks.tools.production_module.make_enkephalin_module"
    ), patch("tasks.tools.production_module.auto") as mock_auto:
        mock_auto.find_element.return_value = False
        mock_auto.sleep_with_stop_check.side_effect = stop_worker
        worker.run()

    assert worker.is_stop is True
    assert worker.production_running is False
    mock_auto.click_element.assert_not_called()
    assert errors == []
    assert worker.failure_message is None


def test_production_finished_keeps_terminal_error_status():
    failure_message = "自动换饼执行失败: 后台模式连续截图失败，已安全停止"
    window = SimpleNamespace(
        worker=SimpleNamespace(failure_message=failure_message),
        log_text=Mock(),
        start_msg="开始任务",
        start_stop_button=Mock(),
        kill_game_box=Mock(),
        status_label=Mock(),
    )

    with patch("tasks.tools.production_module.cfg") as mock_cfg, patch(
        "tasks.tools.production_module.auto"
    ):
        mock_cfg.set_reduce_miscontact = False
        ProductionModule.on_error_occurred(window, failure_message)
        ProductionModule.on_production_finished(window)

    last_status = window.status_label.setText.call_args.args[0]
    assert last_status.startswith("状态：错误 - ")
    assert "后台模式连续截图失败" in last_status
