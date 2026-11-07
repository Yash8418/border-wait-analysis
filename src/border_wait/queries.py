"""SQL queries behind each finding. All run against the views created in db.connect()."""

from __future__ import annotations

import duckdb
import pandas as pd

QUERIES: dict[str, str] = {
    # How often each crossing had any delay, and how long delays were when they happened.
    "crossing_summary": """
        SELECT
            crossing,
            count(*) AS hours_reported,
            round(100 * avg(delayed::INT), 1) AS pct_hours_delayed,
            round(avg(wait_min) FILTER (WHERE delayed), 1) AS avg_delay_min,
            max(wait_min) AS max_wait_min
        FROM readings
        GROUP BY crossing
        ORDER BY crossing
    """,
    # Share of hours with a delay, by hour of day.
    "by_hour": """
        SELECT
            crossing,
            hour,
            round(100 * avg(delayed::INT), 1) AS pct_hours_delayed,
            round(avg(wait_min), 2) AS avg_wait_min
        FROM readings
        GROUP BY crossing, hour
        ORDER BY crossing, hour
    """,
    # Weekday x hour grid for a heatmap.
    "weekday_hour": """
        SELECT
            crossing,
            weekday,
            weekday_name,
            hour,
            round(100 * avg(delayed::INT), 1) AS pct_hours_delayed,
            round(avg(wait_min), 2) AS avg_wait_min,
            count(*) AS hours_reported
        FROM readings
        GROUP BY ALL
        ORDER BY crossing, weekday, hour
    """,
    # Seasonality: month of year.
    "by_month": """
        SELECT
            crossing,
            month,
            monthname(make_date(2000, month, 1)) AS month_name,
            round(100 * avg(delayed::INT), 1) AS pct_hours_delayed,
            round(avg(wait_min), 2) AS avg_wait_min
        FROM readings
        GROUP BY crossing, month
        ORDER BY crossing, month
    """,
    # Long-run trend by year (2010 and 2020 are partial years and excluded).
    "by_year": """
        SELECT
            crossing,
            year,
            round(100 * avg(delayed::INT), 1) AS pct_hours_delayed,
            round(avg(wait_min) FILTER (WHERE delayed), 1) AS avg_delay_min,
            count(*) AS hours_reported
        FROM readings
        WHERE year BETWEEN 2011 AND 2019
        GROUP BY crossing, year
        ORDER BY crossing, year
    """,
    # The 10 worst hours of the week across both crossings.
    "worst_hours": """
        SELECT
            crossing,
            weekday_name,
            hour,
            round(100 * avg(delayed::INT), 1) AS pct_hours_delayed,
            round(avg(wait_min), 2) AS avg_wait_min,
            count(*) AS hours_reported
        FROM readings
        GROUP BY crossing, weekday, weekday_name, hour
        HAVING count(*) >= 100
        ORDER BY avg_wait_min DESC, pct_hours_delayed DESC
        LIMIT 10
    """,
    # Head-to-head: in hours where both crossings reported, which was faster?
    "bridge_vs_tunnel": """
        WITH paired AS (
            SELECT
                b.hour,
                b.wait_min AS bridge_min,
                t.wait_min AS tunnel_min
            FROM readings b
            JOIN readings t USING (timestamp)
            WHERE b.crossing = 'Ambassador Bridge'
              AND t.crossing = 'Detroit-Windsor Tunnel'
        )
        SELECT
            hour,
            count(*) AS paired_hours,
            round(100 * avg((tunnel_min < bridge_min)::INT), 1) AS pct_tunnel_faster,
            round(100 * avg((bridge_min < tunnel_min)::INT), 1) AS pct_bridge_faster,
            round(100 * avg((bridge_min = tunnel_min)::INT), 1) AS pct_same,
            round(avg(bridge_min - tunnel_min), 2) AS avg_bridge_minus_tunnel_min
        FROM paired
        GROUP BY hour
        ORDER BY hour
    """,
    # Each holiday's long weekend vs. a normal day of the same weekday.
    "holiday_effect": """
        WITH days AS (
            SELECT DISTINCT CAST(day AS DATE) AS day, holiday, country FROM holiday_days
        ),
        usual AS (
            SELECT weekday, avg(delayed::INT) AS pct
            FROM readings
            WHERE CAST(timestamp AS DATE) NOT IN (SELECT day FROM days)
            GROUP BY weekday
        )
        SELECT
            d.holiday,
            d.country,
            count(*) AS hours_reported,
            round(100 * avg(r.delayed::INT), 1) AS pct_hours_delayed,
            round(100 * avg(u.pct), 1) AS usual_pct_hours_delayed,
            round(avg(r.delayed::INT) / nullif(avg(u.pct), 0), 2) AS times_usual
        FROM readings r
        JOIN days d ON CAST(r.timestamp AS DATE) = d.day
        LEFT JOIN usual u USING (weekday)
        GROUP BY d.holiday, d.country
        ORDER BY times_usual DESC NULLS LAST
    """,
    # Long weekends and holidays overall vs. regular days, by crossing.
    "long_weekend_vs_regular": """
        WITH days AS (SELECT DISTINCT CAST(day AS DATE) AS day FROM holiday_days)
        SELECT
            crossing,
            CASE WHEN CAST(timestamp AS DATE) IN (SELECT day FROM days)
                 THEN 'Holiday or long weekend' ELSE 'Regular day' END AS day_type,
            count(*) AS hours_reported,
            round(100 * avg(delayed::INT), 1) AS pct_hours_delayed,
            round(avg(wait_min) FILTER (WHERE delayed), 1) AS avg_delay_min
        FROM readings
        GROUP BY ALL
        ORDER BY crossing, day_type
    """,
    # 2019-2025 monthly service standard, with COVID-era labels for context.
    "service_standard_trend": """
        SELECT
            crossing,
            month,
            pct_met_service_standard,
            CASE
                WHEN month < DATE '2020-03-01' THEN 'Before COVID'
                WHEN month < DATE '2021-11-01' THEN 'Border restrictions'
                ELSE 'After reopening'
            END AS period
        FROM monthly
        ORDER BY crossing, month
    """,
}


def run(con: duckdb.DuckDBPyConnection, name: str) -> pd.DataFrame:
    return con.execute(QUERIES[name]).df()
