"""Tests for `Axis` runtime behavior."""

import pytest

from flepimop2.axis import Axis


@pytest.mark.parametrize(
    ("axis", "expected_edges", "expected_bins", "expected_points"),
    [
        (
            Axis(
                name="time",
                kind="continuous",
                size=4,
                domain=(0.0, 10.0),
                spacing="linear",
            ),
            (0.0, 2.5, 5.0, 7.5, 10.0),
            ((0.0, 2.5), (2.5, 5.0), (5.0, 7.5), (7.5, 10.0)),
            (1.25, 3.75, 6.25, 8.75),
        ),
        (
            Axis(
                name="r_eff",
                kind="continuous",
                size=4,
                domain=(-2.0, 2.0),
                spacing="linear",
            ),
            (-2.0, -1.0, 0.0, 1.0, 2.0),
            ((-2.0, -1.0), (-1.0, 0.0), (0.0, 1.0), (1.0, 2.0)),
            (-1.5, -0.5, 0.5, 1.5),
        ),
        (
            Axis(
                name="viral_load",
                kind="continuous",
                size=3,
                domain=(1.0, 1000.0),
                spacing="log",
            ),
            pytest.approx((1.0, 10.0, 100.0, 1000.0)),
            (
                pytest.approx((1.0, 10.0)),
                pytest.approx((10.0, 100.0)),
                pytest.approx((100.0, 1000.0)),
            ),
            pytest.approx((3.16227766, 31.6227766, 316.22776602)),
        ),
    ],
)
def test_continuous_axis_supports_helpers(
    axis: Axis,
    expected_edges: tuple[float, ...],
    expected_bins: tuple[tuple[float, float], ...],
    expected_points: tuple[float, ...],
) -> None:
    """Continuous axes should expose consistent bin and point helpers."""
    assert axis.bin_edges() == expected_edges
    assert axis.bins() == expected_bins
    assert axis.points() == expected_points


def test_categorical_axis_rejects_continuous_helpers() -> None:
    """Categorical axes should not expose continuous point/bin helpers."""
    axis = Axis(
        name="age",
        kind="categorical",
        size=3,
        labels=("0-17", "18-64", "65+"),
    )

    with pytest.raises(TypeError):
        axis.points()
