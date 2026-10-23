import pytest
from analysis.reference import closest_distance_xz, compare_with_reference


def test_point_to_polyline():
    line = [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
    assert closest_distance_xz([5.0, 0.0, 3.0], line) == pytest.approx(3.0)
    assert closest_distance_xz([12.0, 0.0, 0.0], line) == pytest.approx(2.0)


def test_reference_comparison():
    result = compare_with_reference(
        [[5.0, 0.0, 3.0], [10.0, 0.0, 0.0]],
        [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]],
    )
    assert result["evaluated_points"] == 2
    assert result["mean_distance_m"] == 1.5
    assert result["per_point_distance_m"] == [3.0, 0.0]
