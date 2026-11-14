from unittest.mock import Mock

import numpy as np
import pytest

from utils.image_utils import ImageUtils


@pytest.mark.parametrize(
    ("screenshot_shape", "template_shape", "bbox"),
    [
        ((40, 60), (80, 90), None),
        ((100, 100), (80, 80), (50, 50, 51, 51)),
    ],
    ids=("template-larger-than-screenshot", "template-larger-than-bbox"),
)
def test_match_template_skips_opencv_when_template_exceeds_search_area(
    monkeypatch, screenshot_shape, template_shape, bbox
):
    match_template = Mock(side_effect=AssertionError("OpenCV matching should not run"))
    monkeypatch.setattr("utils.image_utils.cv2.matchTemplate", match_template)
    screenshot = np.zeros(screenshot_shape, dtype=np.uint8)
    template = np.zeros(template_shape, dtype=np.uint8)

    assert ImageUtils.match_template(screenshot, template, bbox) == (None, 0.0)
    match_template.assert_not_called()
