from unittest.mock import Mock, patch

import numpy as np
import pytest
from PIL import Image
from rapidocr.utils.output import RapidOCROutput

from module.ocr.ocr import OCR, OCRExecutionError
from tasks.base import script_task_scheme
from tasks.base.make_enkephalin_module import get_current_enkephalin
from tasks.tools.production_module import ProductionWork


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
