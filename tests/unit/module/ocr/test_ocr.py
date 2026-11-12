from unittest.mock import Mock

import pytest
from PIL import Image
from rapidocr.utils.output import RapidOCROutput

from module.ocr.ocr import OCR, OCRExecutionError


def _ocr_instance(engine) -> OCR:
    instance = object.__new__(OCR)
    instance.engine = engine
    instance.logger = Mock()
    return instance


def test_ocr_empty_text_returns_empty_output():
    empty_output = RapidOCROutput()
    ocr = _ocr_instance(Mock(return_value=empty_output))

    result = ocr.run(Image.new("L", (16, 16), color=0))

    assert result is empty_output
    assert result.txts in (None, [])


def test_ocr_engine_failure_raises_with_original_cause():
    engine_error = ValueError("engine failed")
    ocr = _ocr_instance(Mock(side_effect=engine_error))

    with pytest.raises(OCRExecutionError, match="OCR execution failed") as exc_info:
        ocr.run(Image.new("L", (16, 16), color=0))

    assert exc_info.value.__cause__ is engine_error


def test_ocr_invalid_image_raises_with_original_cause():
    ocr = _ocr_instance(Mock())

    with pytest.raises(OCRExecutionError, match="OCR execution failed") as exc_info:
        ocr.run(object())

    assert isinstance(exc_info.value.__cause__, ValueError)
