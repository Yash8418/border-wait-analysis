import json
import math

from border_wait.export import RESULTS, build_dashboard


def test_dashboard_has_every_section():
    data = build_dashboard(RESULTS)
    for key in ("summary", "weekday_hour", "by_month", "bridge_vs_tunnel", "holiday_effect", "service_standard"):
        assert data[key], key
    assert data["crossings"] == ["Ambassador Bridge", "Detroit-Windsor Tunnel"]


def test_heatmap_is_complete():
    grid = build_dashboard(RESULTS)["weekday_hour"]
    assert len(grid) == 2 * 7 * 24
    assert {cell["weekday"] for cell in grid} == set(range(1, 8))


def test_output_is_strict_json():
    text = json.dumps(build_dashboard(RESULTS), allow_nan=False)
    for value in json.loads(text)["holiday_effect"]:
        assert not (isinstance(value["times_usual"], float) and math.isnan(value["times_usual"]))
