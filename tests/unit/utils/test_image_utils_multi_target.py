import numpy as np

from utils.image_utils import ImageUtils


def _run_nms(monkeypatch, candidates, *, template_shape=(3, 7), min_dist=10):
    """Run NMS with a controlled match map; candidates are (x, y, score)."""
    height = max((y for _, y, _ in candidates), default=0) + 1
    width = max((x for x, _, _ in candidates), default=0) + 1
    response = np.zeros((height, width), dtype=np.float32)
    for x, y, score in candidates:
        response[y, x] = score

    monkeypatch.setattr("utils.image_utils.cv2.matchTemplate", lambda *_args: response)
    screenshot = np.zeros((height + template_shape[0], width + template_shape[1]), dtype=np.uint8)
    template = np.zeros(template_shape, dtype=np.uint8)
    return ImageUtils.match_template_with_multiple_targets(screenshot, template, threshold=0.5, min_dist=min_dist)


def test_multi_target_nms_keeps_highest_score_and_suppresses_exact_radius(monkeypatch):
    matches = _run_nms(
        monkeypatch,
        [(1, 1, 0.95), (6, 1, 0.85), (10, 1, 0.80)],
        min_dist=5,
    )

    # (1, 1) and (6, 1) are exactly five pixels apart, so the lower score is suppressed.
    assert matches == [(4, 2), (13, 2)]


def test_multi_target_nms_checks_neighbor_cells_for_fractional_radius(monkeypatch):
    matches = _run_nms(
        monkeypatch,
        [(9, 0, 0.95), (10, 1, 0.85), (11, 0, 0.80)],
        min_dist=1.5,
    )

    # (9, 0) and (10, 1) are in neighboring cells and within 1.5 pixels.
    assert matches == [(12, 1), (14, 1)]


def test_multi_target_nms_accepts_zero_radius_and_returns_rectangular_template_centers(monkeypatch):
    matches = _run_nms(
        monkeypatch,
        [(0, 0, 0.9), (2, 1, 0.8)],
        template_shape=(3, 7),
        min_dist=0,
    )

    assert matches == [(3, 1), (5, 2)]


def test_multi_target_nms_returns_empty_when_no_location_meets_threshold(monkeypatch):
    monkeypatch.setattr(
        "utils.image_utils.cv2.matchTemplate",
        lambda *_args: np.array([[0.1, 0.2]], dtype=np.float32),
    )
    screenshot = np.zeros((4, 9), dtype=np.uint8)
    template = np.zeros((3, 7), dtype=np.uint8)

    assert ImageUtils.match_template_with_multiple_targets(screenshot, template, threshold=0.5) == []
