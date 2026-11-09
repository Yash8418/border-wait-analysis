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

async function main() {
  try {
    const response = await fetch("data/dashboard.json");
    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();
    renderStats(data);
  } catch {
    document.getElementById("stats").innerHTML =
      '<p class="status status--error">The data couldn\'t load. Refresh the page to try again.</p>';
  }
}

main();
