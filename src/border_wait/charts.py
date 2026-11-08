"""Static charts for the README, built from data/results/*.csv.

Usage:
    python -m border_wait.charts
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no display needed
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "results"
CHARTS = ROOT / "docs" / "charts"

# Colors validated for colorblind separation and contrast on the light surface.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e4e3df"
CROSSING_COLORS = {"Ambassador Bridge": "#2a78d6", "Detroit-Windsor Tunnel": "#eb6834"}
BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#f2f7fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def style(ax, title: str, subtitle: str | None = None) -> None:
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=13, color=INK, fontweight="bold", pad=22 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9.5, color=INK_SECONDARY)


def save(fig, name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def weekday_hour_heatmap(results: Path = RESULTS, out_dir: Path = CHARTS) -> Path:
    grid = pd.read_csv(results / "weekday_hour.csv")
    bridge = grid[grid.crossing == "Ambassador Bridge"].pivot(index="weekday", columns="hour", values="pct_hours_delayed")

    fig, ax = plt.subplots(figsize=(10, 3.6))
    image = ax.imshow(bridge.values, cmap=BLUES, aspect="auto", vmin=0)
    style(ax, "Friday evening is the worst time to cross",
          "Ambassador Bridge, Canada-bound travellers: % of hours with any delay, 2010–2019")
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_yticks(range(7), WEEKDAYS)
    ax.set_xticks(range(0, 24, 3), [f"{h:02d}:00" for h in range(0, 24, 3)])
    bar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    bar.outline.set_visible(False)
    bar.ax.tick_params(labelsize=8, colors=INK_SECONDARY, length=0)
    bar.set_label("% of hours delayed", fontsize=8, color=INK_SECONDARY)

    peak = bridge.stack().idxmax()
    ax.annotate(f"{bridge.loc[peak]:.0f}%", xy=(peak[1], peak[0] - 1), ha="center", va="center",
                fontsize=8, color="#ffffff", fontweight="bold")
    return save(fig, "weekday_hour_heatmap", out_dir)


def monthly_pattern(results: Path = RESULTS, out_dir: Path = CHARTS) -> Path:
    data = pd.read_csv(results / "by_month.csv")
    fig, ax = plt.subplots(figsize=(8, 3.8))
    style(ax, "Summer brings three times the delays of winter", "% of hours with any delay, by month, 2010–2019")
    ends = {}
    for crossing, color in CROSSING_COLORS.items():
        rows = data[data.crossing == crossing]
        ax.plot(rows.month, rows.pct_hours_delayed, color=color, linewidth=2, marker="o", markersize=4)
        ends[crossing] = rows.iloc[-1].pct_hours_delayed
    # Direct labels at the line ends, nudged apart when the lines finish close together.
    upper, lower = sorted(ends, key=ends.get, reverse=True)
    gap = max(0, 1.2 - (ends[upper] - ends[lower])) / 2
    for crossing, nudge in ((upper, gap), (lower, -gap)):
        ax.annotate(crossing.replace("Detroit-Windsor ", ""), xy=(12, ends[crossing] + nudge), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=INK_SECONDARY)
    ax.set_xticks(range(1, 13), [m[:3] for m in data.month_name.unique()])
    top = data.pct_hours_delayed.max()
    ax.set_yticks(range(0, int(top) + 4, 3))
    ax.set_ylim(0, top * 1.08)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    return save(fig, "monthly_pattern", out_dir)


def bridge_vs_tunnel(results: Path = RESULTS, out_dir: Path = CHARTS) -> Path:
    data = pd.read_csv(results / "bridge_vs_tunnel.csv")
    fig, ax = plt.subplots(figsize=(9, 3.8))
    style(ax, "When one crossing is slower, which is it?",
          "Hours when both crossings reported a wait: % of those hours each one was faster (the rest were tied)")
    width = 0.4
    ax.bar(data.hour - width / 2 - 0.02, data.pct_bridge_faster, width, color=CROSSING_COLORS["Ambassador Bridge"],
           label="Bridge faster")
    ax.bar(data.hour + width / 2 + 0.02, data.pct_tunnel_faster, width,
           color=CROSSING_COLORS["Detroit-Windsor Tunnel"], label="Tunnel faster")
    ax.set_xticks(range(0, 24, 3), [f"{h:02d}:00" for h in range(0, 24, 3)])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_SECONDARY, loc="upper left")
    return save(fig, "bridge_vs_tunnel", out_dir)


def service_standard_trend(results: Path = RESULTS, out_dir: Path = CHARTS) -> Path:
    data = pd.read_csv(results / "service_standard_trend.csv", parse_dates=["month"])
    fig, ax = plt.subplots(figsize=(9, 3.8))
    style(ax, "Since reopening, waits meet the service standard less often",
          "% of each month CBSA met its wait-time service standard, Apr 2019 – Oct 2025")
    ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2021-11-01"), color="#f0efec", zorder=0)
    ax.text(pd.Timestamp("2020-09-01"), 0.03, "Border restrictions", transform=ax.get_xaxis_transform(),
            fontsize=8.5, color=INK_SECONDARY, ha="center")
    for crossing, color in CROSSING_COLORS.items():
        rows = data[data.crossing == crossing]
        ax.plot(rows.month, rows.pct_met_service_standard, color=color, linewidth=2, label=crossing)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_SECONDARY, loc="lower right")
    return save(fig, "service_standard_trend", out_dir)


def holiday_effect(results: Path = RESULTS, out_dir: Path = CHARTS, top: int = 10) -> Path:
    data = pd.read_csv(results / "holiday_effect.csv").dropna(subset=["times_usual"])
    data = data[data.hours_reported >= 200]
    # Names like "Thanksgiving (Canada)" already say the country.
    data["label"] = [name if "(" in name else f"{name} ({country})" for name, country in zip(data.holiday, data.country)]
    data = data.sort_values("times_usual").tail(top)

    fig, ax = plt.subplots(figsize=(8, 4.4))
    style(ax, "Long weekends that slow the border most",
          "Delays on each holiday's long weekend vs. a normal day of the same weekday (1.0 = usual)")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.barh(data.label, data.times_usual, color=CROSSING_COLORS["Ambassador Bridge"], height=0.6)
    ax.axvline(1, color=MUTED, linewidth=1, linestyle="--")
    for y, value in enumerate(data.times_usual):
        ax.text(value + 0.03, y, f"{value:.2f}×", va="center", fontsize=8.5, color=INK_SECONDARY)
    ax.set_xlim(0, data.times_usual.max() * 1.15)
    return save(fig, "holiday_effect", out_dir)


ALL_CHARTS = (weekday_hour_heatmap, monthly_pattern, bridge_vs_tunnel, service_standard_trend, holiday_effect)


def main() -> None:
    for chart in ALL_CHARTS:
        print(f"Wrote {chart().relative_to(ROOT)}")


if __name__ == "__main__":
    main()
