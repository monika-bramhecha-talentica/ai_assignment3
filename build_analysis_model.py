#!/usr/bin/env python3
"""Build analysis views/tables from raw SQLite tables.

Run:
    python build_analysis_model.py

Optional:
    python build_analysis_model.py --db-path analytics.db
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "analytics.db"

CAUSE_ACTIONS = {
    "stockout": "Tighten inventory checks; add backup stock and substitute rules.",
    "warehouse_delay": "Staff up or re-slot fast movers; monitor pick-pack SLA.",
    "dispatch_lag": "Tighter handoff SOP; create cut-off alerts.",
    "traffic": "Dynamic routing and slot re-allocation during congestion.",
    "weather": "Pre-alert customers, buffer ETAs, and prioritize essentials.",
    "event": "Create blackout/slowdown plans for strikes/holidays.",
    "address_issue": "Pre-ship address validation and driver assistance.",
    "vehicle_issue": "Maintain spare vehicles; enforce pre-trip checks.",
    "late_delivery": "Improve ETA promises; increase visibility with live tracking.",
    "poor_comm": "Automated status updates and proactive delay messaging.",
}


def _create_analysis_view(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS v_external_best;
        CREATE VIEW v_external_best AS
        WITH ranked AS (
            SELECT
                order_id,
                traffic_condition,
                weather_condition,
                event_type,
                recorded_at,
                CASE
                    WHEN lower(coalesce(traffic_condition, '')) = 'heavy' THEN 2
                    WHEN lower(coalesce(traffic_condition, '')) = 'moderate' THEN 1
                    ELSE 0
                END AS traffic_score,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id
                    ORDER BY
                        CASE
                            WHEN lower(coalesce(traffic_condition, '')) = 'heavy' THEN 2
                            WHEN lower(coalesce(traffic_condition, '')) = 'moderate' THEN 1
                            ELSE 0
                        END DESC,
                        recorded_at ASC
                ) AS rn
            FROM raw_external_factors
        )
        SELECT
            order_id,
            traffic_condition,
            weather_condition,
            event_type,
            traffic_score
        FROM ranked
        WHERE rn = 1;

        DROP VIEW IF EXISTS v_feedback_summary;
        CREATE VIEW v_feedback_summary AS
        SELECT
            order_id,
            AVG(CAST(rating AS REAL)) AS feedback_rating_avg,
            MAX(sentiment) AS feedback_sentiment_top,
            GROUP_CONCAT(lower(coalesce(feedback_text, '')), ' || ') AS feedback_text_concat
        FROM raw_feedback
        GROUP BY order_id;

        DROP VIEW IF EXISTS fact_order_analysis;
        CREATE VIEW fact_order_analysis AS
        SELECT
            o.order_id,
            o.client_id,
            c.client_name,
            o.customer_name,
            o.city,
            o.state,
            o.status,
            o.payment_mode,
            CAST(o.amount AS REAL) AS amount,
            o.failure_reason,
            o.order_date,
            o.promised_delivery_date,
            o.actual_delivery_date,
            wl.warehouse_id,
            w.warehouse_name,
            w.city AS warehouse_city,
            w.state AS warehouse_state,
            fl.driver_id,
            fl.vehicle_number,
            fl.route_code,
            fl.gps_delay_notes,
            wl.notes AS warehouse_notes,
            ex.traffic_condition,
            ex.weather_condition,
            ex.event_type,
            ex.traffic_score,
            fb.feedback_rating_avg,
            fb.feedback_sentiment_top,
            fb.feedback_text_concat,
            ((julianday(coalesce(o.actual_delivery_date, o.promised_delivery_date)) - julianday(o.promised_delivery_date)) * 24.0) AS delay_hours,
            CASE
                WHEN ((julianday(coalesce(o.actual_delivery_date, o.promised_delivery_date)) - julianday(o.promised_delivery_date)) * 24.0) > 0.01 THEN 1
                ELSE 0
            END AS is_late,
            ((julianday(fl.arrival_time) - julianday(fl.departure_time)) * 24.0) AS transit_hours,
            ((julianday(wl.picking_end) - julianday(wl.picking_start)) * 24.0 * 60.0) AS picking_minutes,
            ((julianday(wl.dispatch_time) - julianday(wl.picking_end)) * 24.0 * 60.0) AS dispatch_lag_minutes
        FROM raw_orders o
        LEFT JOIN raw_warehouse_logs wl ON wl.order_id = o.order_id
        LEFT JOIN raw_fleet_logs fl ON fl.order_id = o.order_id
        LEFT JOIN v_external_best ex ON ex.order_id = o.order_id
        LEFT JOIN v_feedback_summary fb ON fb.order_id = o.order_id
        LEFT JOIN dim_warehouses w ON w.warehouse_id = wl.warehouse_id
        LEFT JOIN dim_clients c ON c.client_id = o.client_id;
        """
    )


def _infer_causes(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []

    for _, row in df.iterrows():
        order_id = row["order_id"]
        text_blob = " ".join(
            str(v).lower()
            for v in [
                row.get("failure_reason", ""),
                row.get("gps_delay_notes", ""),
                row.get("warehouse_notes", ""),
                row.get("feedback_text_concat", ""),
            ]
            if pd.notna(v)
        )

        causes = set()
        if "stock" in text_blob:
            causes.add("stockout")
        if "slow" in text_blob or (pd.notna(row.get("picking_minutes")) and float(row["picking_minutes"]) > 30):
            causes.add("warehouse_delay")
        if pd.notna(row.get("dispatch_lag_minutes")) and float(row["dispatch_lag_minutes"]) > 45:
            causes.add("dispatch_lag")
        if "address" in text_blob:
            causes.add("address_issue")
        if "breakdown" in text_blob:
            causes.add("vehicle_issue")
        if "congestion" in text_blob or (pd.notna(row.get("traffic_score")) and float(row["traffic_score"]) >= 1):
            causes.add("traffic")
        if str(row.get("weather_condition", "")) in {"Rain", "Fog"}:
            causes.add("weather")
        if pd.notna(row.get("event_type")) and str(row.get("event_type")).strip() != "":
            causes.add("event")
        if pd.notna(row.get("is_late")) and int(row["is_late"]) == 1:
            causes.add("late_delivery")
        if "update" in text_blob or "no update" in text_blob:
            causes.add("poor_comm")

        if not causes:
            rows.append({"order_id": order_id, "cause": "unknown", "recommendation": "Inspect order logs for missing context."})
        else:
            for cause in sorted(causes):
                rows.append({
                    "order_id": order_id,
                    "cause": cause,
                    "recommendation": CAUSE_ACTIONS.get(cause, "Investigate further."),
                })

    return pd.DataFrame(rows)


def build_analysis_model(db_path: Path = DEFAULT_DB_PATH) -> dict[str, int]:
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run init_db.py first."
        )

    conn = sqlite3.connect(db_path)
    try:
        _create_analysis_view(conn)

        fact_df = pd.read_sql_query("SELECT * FROM fact_order_analysis", conn)
        causes_df = _infer_causes(fact_df)

        causes_df.to_sql("fact_order_causes", conn, if_exists="replace", index=False)

        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_fact_order_causes_order_id ON fact_order_causes(order_id);
            CREATE INDEX IF NOT EXISTS idx_fact_order_causes_cause ON fact_order_causes(cause);

            DROP VIEW IF EXISTS v_cause_summary;
            CREATE VIEW v_cause_summary AS
            SELECT
                cause,
                COUNT(*) AS cause_count
            FROM fact_order_causes
            GROUP BY cause
            ORDER BY cause_count DESC;
            """
        )
        conn.commit()

        total_orders = conn.execute("SELECT COUNT(*) FROM fact_order_analysis").fetchone()[0]
        total_cause_rows = conn.execute("SELECT COUNT(*) FROM fact_order_causes").fetchone()[0]
        unique_causes = conn.execute("SELECT COUNT(DISTINCT cause) FROM fact_order_causes").fetchone()[0]

        return {
            "fact_order_analysis_rows": int(total_orders),
            "fact_order_causes_rows": int(total_cause_rows),
            "unique_causes": int(unique_causes),
        }
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build analysis views and cause tables.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Path to SQLite DB file")
    args = parser.parse_args()

    stats = build_analysis_model(db_path=args.db_path)
    print(f"Analysis model ready on: {args.db_path}")
    for key, value in stats.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
