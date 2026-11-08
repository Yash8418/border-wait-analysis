from border_wait.charts import ALL_CHARTS, RESULTS


def test_every_chart_renders(tmp_path):
    for chart in ALL_CHARTS:
        path = chart(RESULTS, tmp_path)
        assert path.exists()
        assert path.stat().st_size > 10_000  # a real image, not an empty canvas
