// Windsor–Detroit border dashboard. Reads data/dashboard.json (built by `python -m border_wait.export`).
const COLORS = { "Ambassador Bridge": "var(--bridge)", "Detroit-Windsor Tunnel": "var(--tunnel)" };
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const hourLabel = (hour) => {
  const suffix = hour < 12 ? "am" : "pm";
  return `${hour % 12 || 12} ${suffix}`;
};

function stat(value, label, crossing) {
  const swatch = crossing ? `<span class="swatch" style="background:${COLORS[crossing]}" aria-hidden="true"></span>` : "";
  return `<div class="stat"><span class="stat__value">${value}</span><span class="stat__label">${swatch}${label}</span></div>`;
}

function renderStats(data) {
  const summary = Object.fromEntries(data.summary.map((row) => [row.crossing, row]));
  const worst = data.weekday_hour.reduce((a, b) => (b.pct_hours_delayed > a.pct_hours_delayed ? b : a));
  const holidays = data.long_weekend_vs_regular.filter((row) => row.crossing === "Detroit-Windsor Tunnel");
  const holiday = holidays.find((row) => row.day_type !== "Regular day");
  const regular = holidays.find((row) => row.day_type === "Regular day");

  document.getElementById("stats").innerHTML = [
    stat(`${summary["Ambassador Bridge"].pct_hours_delayed}%`, "of hours had a delay at the Ambassador Bridge", "Ambassador Bridge"),
    stat(`${summary["Detroit-Windsor Tunnel"].pct_hours_delayed}%`, "of hours had a delay at the Tunnel", "Detroit-Windsor Tunnel"),
    stat(
      `${DAYS[worst.weekday - 1]} ${hourLabel(worst.hour)}`,
      `worst hour of the week — delayed ${worst.pct_hours_delayed}% of the time at the ${worst.crossing.replace("Detroit-Windsor ", "")}`,
    ),
    stat(
      `${(holiday.pct_hours_delayed / regular.pct_hours_delayed).toFixed(1)}×`,
      "more often delayed at the Tunnel on holidays and long weekends",
    ),
  ].join("");
}

// Sequential blue ramp (light -> dark), validated for contrast on the light surface.
const RAMP = ["#f2f7fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];
const tooltip = document.getElementById("tooltip");

function rampColor(value, max) {
  const step = Math.min(RAMP.length - 1, Math.floor((value / max) * RAMP.length));
  return RAMP[step];
}

function showTooltip(event, html) {
  tooltip.innerHTML = html;
  tooltip.hidden = false;
  const { clientX: x, clientY: y } = event;
  const box = tooltip.getBoundingClientRect();
  const left = Math.min(x + 14, window.innerWidth - box.width - 8);
  const top = y + 16 + box.height > window.innerHeight ? y - box.height - 12 : y + 16;
  tooltip.style.transform = `translate(${left}px, ${top}px)`;
}

function renderHeatmap(data, crossing) {
  const cells = data.weekday_hour.filter((c) => c.crossing === crossing);
  const max = Math.max(...data.weekday_hour.map((c) => c.pct_hours_delayed)); // shared scale for both crossings
  const byKey = Object.fromEntries(cells.map((c) => [`${c.weekday}-${c.hour}`, c]));

  let html = '<div class="heatmap__corner"></div>';
  for (let hour = 0; hour < 24; hour += 1) {
    html += `<div class="heatmap__hour">${hour % 3 === 0 ? hourLabel(hour) : ""}</div>`;
  }
  DAYS.forEach((day, i) => {
    html += `<div class="heatmap__day">${day}</div>`;
    for (let hour = 0; hour < 24; hour += 1) {
      const cell = byKey[`${i + 1}-${hour}`];
      const pct = cell?.pct_hours_delayed ?? 0;
      const label = `${day} ${hourLabel(hour)}: delayed ${pct}% of hours, average wait ${cell?.avg_wait_min ?? 0} min`;
      html += `<div class="heatmap__cell" style="background:${rampColor(pct, max)}" data-day="${day}" data-hour="${hour}"
        data-pct="${pct}" data-avg="${cell?.avg_wait_min ?? 0}" aria-label="${label}"></div>`;
    }
  });
  const grid = document.getElementById("heatmap");
  grid.innerHTML = html;
  grid.setAttribute("aria-label", `Heatmap of delays at ${crossing}`);

  document.getElementById("heatmap-legend").innerHTML =
    `<span>0%</span>${RAMP.map((c) => `<i style="background:${c}"></i>`).join("")}<span>${Math.round(max)}% of hours delayed</span>`;

  document.getElementById("heatmap-table").innerHTML = `<table>
    <caption>${crossing}: % of hours delayed</caption>
    <thead><tr><th scope="col">Hour</th>${DAYS.map((d) => `<th scope="col">${d}</th>`).join("")}</tr></thead>
    <tbody>${Array.from({ length: 24 }, (_, hour) => `<tr><th scope="row">${hourLabel(hour)}</th>${DAYS.map(
      (_, i) => `<td>${byKey[`${i + 1}-${hour}`]?.pct_hours_delayed ?? "–"}</td>`,
    ).join("")}</tr>`).join("")}</tbody></table>`;
}

function setupHeatmap(data) {
  const grid = document.getElementById("heatmap");
  grid.addEventListener("mousemove", (event) => {
    const cell = event.target.closest(".heatmap__cell");
    if (!cell) return void (tooltip.hidden = true);
    const { day, hour, pct, avg } = cell.dataset;
    showTooltip(
      event,
      `<strong>${day} ${hourLabel(Number(hour))}</strong><br>Delayed ${pct}% of hours<br>Average wait ${Number(avg).toFixed(1)} min`,
    );
  });
  grid.addEventListener("mouseleave", () => (tooltip.hidden = true));

  const buttons = document.querySelectorAll(".toggle button");
  buttons.forEach((button) =>
    button.addEventListener("click", () => {
      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
      renderHeatmap(data, button.dataset.crossing);
    }),
  );
  renderHeatmap(data, "Ambassador Bridge");
}

async function main() {
  try {
    const response = await fetch("data/dashboard.json");
    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();
    renderStats(data);
    setupHeatmap(data);
  } catch {
    document.getElementById("stats").innerHTML =
      '<p class="status status--error">The data couldn\'t load. Refresh the page to try again.</p>';
  }
}

main();
