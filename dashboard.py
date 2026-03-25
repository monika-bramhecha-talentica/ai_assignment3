#!/usr/bin/env python3
"""Simple Streamlit dashboard for delivery analysis queries.

Run:
    streamlit run dashboard.py
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from build_analysis_model import build_analysis_model
from init_db import initialize_database

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "analytics.db"
DATA_DIR = BASE_DIR / "third-assignment-sample-data-set"

SAMPLE_PROBLEMS = {
    "city_delayed_date_range": "Why were deliveries delayed in city X for a selected date range?",
    "client_failures_past_week": "Why did Client X's orders fail in the past week?",
    "warehouse_august_reasons": "Explain the top reasons for delivery failures linked to Warehouse B in August?",
    "city_vs_city_last_month": "Compare delivery failure causes between City A and City B last month?",
    "festival_period_risks": "What are the likely causes of delivery failures during the festival period, and how should we prepare?",
    "client_onboarding_risk": "If we onboard Client Y with ~20,000 extra monthly orders, what new failure risks should we expect and how do we mitigate them?",
}

CAUSE_ACTIONS = {
    "stockout": "Strengthen stock planning and keep substitute SKUs ready.",
    "warehouse_delay": "Increase pick-pack staffing and monitor warehouse SLA breaches.",
    "dispatch_lag": "Add dispatch cut-off alerts and improve handoff controls.",
    "traffic": "Use dynamic route changes and peak-hour slot management.",
    "weather": "Buffer ETAs and pre-alert customers during weather disruptions.",
    "event": "Create city-event contingency plans and temporary reroutes.",
    "address_issue": "Improve address validation and delivery confirmation workflows.",
    "vehicle_issue": "Run stronger preventive maintenance and pre-trip checks.",
    "late_delivery": "Tighten promise windows and escalate at-risk orders early.",
    "poor_comm": "Send proactive order status updates when delays are detected.",
}


def run_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)


def ensure_database_ready() -> tuple[dict[str, int], dict[str, int]]:
    load_stats = initialize_database(db_path=DB_PATH, data_dir=DATA_DIR)
    model_stats = build_analysis_model(db_path=DB_PATH)
    return load_stats, model_stats


def fetch_filter_options(conn: sqlite3.Connection) -> tuple[list[str], list[str], list[str]]:
    cities = run_query(conn, "SELECT DISTINCT city FROM fact_order_analysis WHERE city IS NOT NULL ORDER BY city")
    clients = run_query(conn, "SELECT DISTINCT client_name FROM fact_order_analysis WHERE client_name IS NOT NULL ORDER BY client_name")
    warehouses = run_query(conn, "SELECT DISTINCT warehouse_name FROM fact_order_analysis WHERE warehouse_name IS NOT NULL ORDER BY warehouse_name")
    return (
        cities["city"].dropna().tolist(),
        clients["client_name"].dropna().tolist(),
        warehouses["warehouse_name"].dropna().tolist(),
    )


def fetch_date_ranges(conn: sqlite3.Connection) -> dict[str, str | None]:
    summary = run_query(
        conn,
        """
        SELECT
            MIN(date(order_date)) AS order_min_date,
            MAX(date(COALESCE(actual_delivery_date, promised_delivery_date))) AS order_max_date
        FROM fact_order_analysis
        """,
    )
    full_dataset = run_query(
        conn,
        """
        SELECT MIN(min_date) AS dataset_min_date, MAX(max_date) AS dataset_max_date
        FROM (
            SELECT MIN(date(created_at)) AS min_date, MAX(date(created_at)) AS max_date FROM dim_warehouses
            UNION ALL
            SELECT MIN(date(created_at)) AS min_date, MAX(date(created_at)) AS max_date FROM dim_clients
            UNION ALL
            SELECT MIN(date(created_at)) AS min_date, MAX(date(created_at)) AS max_date FROM dim_drivers
            UNION ALL
            SELECT MIN(date(order_date)) AS min_date, MAX(date(COALESCE(actual_delivery_date, promised_delivery_date))) AS max_date FROM raw_orders
            UNION ALL
            SELECT MIN(date(departure_time)) AS min_date, MAX(date(arrival_time)) AS max_date FROM raw_fleet_logs
            UNION ALL
            SELECT MIN(date(picking_start)) AS min_date, MAX(date(dispatch_time)) AS max_date FROM raw_warehouse_logs
            UNION ALL
            SELECT MIN(date(recorded_at)) AS min_date, MAX(date(recorded_at)) AS max_date FROM raw_external_factors
            UNION ALL
            SELECT MIN(date(created_at)) AS min_date, MAX(date(created_at)) AS max_date FROM raw_feedback
        )
        """,
    )
    return {
        "order_min_date": summary.iloc[0]["order_min_date"] if not summary.empty else None,
        "order_max_date": summary.iloc[0]["order_max_date"] if not summary.empty else None,
        "dataset_min_date": full_dataset.iloc[0]["dataset_min_date"] if not full_dataset.empty else None,
        "dataset_max_date": full_dataset.iloc[0]["dataset_max_date"] if not full_dataset.empty else None,
    }


def _has_missing_date_ranges(date_ranges: dict[str, str | None]) -> bool:
    return not all(
        [
            date_ranges.get("order_min_date"),
            date_ranges.get("order_max_date"),
            date_ranges.get("dataset_min_date"),
            date_ranges.get("dataset_max_date"),
        ]
    )


def _safe_to_date(value: str | None) -> dt.date:
    if not value:
        return dt.date.today()
    return pd.to_datetime(value).date()


def _last_month_window(conn: sqlite3.Connection) -> tuple[str, str]:
    max_date_df = run_query(conn, "SELECT MAX(date(order_date)) AS max_order_date FROM fact_order_analysis")
    max_date = _safe_to_date(max_date_df.iloc[0]["max_order_date"] if not max_date_df.empty else None)
    first_this_month = max_date.replace(day=1)
    last_prev_month = first_this_month - dt.timedelta(days=1)
    first_prev_month = last_prev_month.replace(day=1)
    return str(first_prev_month), str(last_prev_month)


def _kpi_for_where(conn: sqlite3.Connection, where_sql: str, params: tuple) -> dict[str, float | int]:
    kpi_sql = f"""
        SELECT
            COUNT(*) AS total_orders,
            AVG(is_late) * 100.0 AS late_rate,
            AVG(CASE WHEN lower(coalesce(status, '')) = 'failed' THEN 1.0 ELSE 0.0 END) * 100.0 AS failed_rate
        FROM fact_order_analysis
        WHERE {where_sql}
    """
    kpi_df = run_query(conn, kpi_sql, params)
    return {
        "total_orders": int(kpi_df.iloc[0]["total_orders"] or 0),
        "late_rate": float(kpi_df.iloc[0]["late_rate"] or 0.0),
        "failed_rate": float(kpi_df.iloc[0]["failed_rate"] or 0.0),
    }


def _causes_for_where(conn: sqlite3.Connection, where_sql: str, params: tuple, limit: int = 10) -> pd.DataFrame:
    causes_sql = f"""
        SELECT
            c.cause,
            COUNT(*) AS cause_count
        FROM fact_order_causes c
        JOIN fact_order_analysis a ON a.order_id = c.order_id
        WHERE {where_sql}
        GROUP BY c.cause
        ORDER BY cause_count DESC
        LIMIT {limit}
    """
    return run_query(conn, causes_sql, params)


def _samples_for_where(conn: sqlite3.Connection, where_sql: str, params: tuple, limit: int = 10) -> pd.DataFrame:
    samples_sql = f"""
        SELECT
            order_id,
            city,
            client_name,
            warehouse_name,
            ROUND(delay_hours, 2) AS delay_hours,
            status
        FROM fact_order_analysis
        WHERE {where_sql}
        ORDER BY delay_hours DESC
        LIMIT {limit}
    """
    return run_query(conn, samples_sql, params)


def _recommendations_from_causes(causes_df: pd.DataFrame) -> list[str]:
    recs: list[str] = []
    if causes_df.empty:
        return recs
    for cause in causes_df["cause"].tolist()[:3]:
        action = CAUSE_ACTIONS.get(str(cause), "Investigate with additional context.")
        recs.append(f"{cause}: {action}")
    return recs


def map_question_to_template(question: str) -> tuple[str, str]:
    q = question.lower().strip()
    if ("compare" in q or "vs" in q) and "city" in q:
        return "city_vs_city_last_month", "Detected city comparison intent for a monthly window."
    if "warehouse" in q and ("aug" in q or "month" in q or "reason" in q):
        return "warehouse_august_reasons", "Detected warehouse root-cause summary intent."
    if "client" in q and ("fail" in q or "failed" in q or "week" in q):
        return "client_failures_past_week", "Detected client failure analysis intent over a recent period."
    if "festival" in q or "peak" in q or "holiday" in q:
        return "festival_period_risks", "Detected seasonal or festival risk analysis intent."
    if "onboard" in q or "20,000" in q or "risk" in q:
        return "client_onboarding_risk", "Detected onboarding risk simulation intent."
    if "city" in q and ("yesterday" in q or "date range" in q or "delay" in q or "delayed" in q):
        return "city_delayed_date_range", "Detected city-level delay analysis intent."
    return "city_delayed_date_range", "Mapped to closest supported template: city delay analysis."


def run_template_analysis(
    conn: sqlite3.Connection,
    template_id: str,
    city: str,
    client: str,
    warehouse: str,
    city_b: str,
    guided_start_date: str,
    guided_end_date: str,
) -> dict[str, object]:
    today_df = run_query(conn, "SELECT MAX(date(order_date)) AS max_order_date FROM fact_order_analysis")
    max_order_date = _safe_to_date(today_df.iloc[0]["max_order_date"] if not today_df.empty else None)
    last_week_start = max_order_date - dt.timedelta(days=7)
    month_start, month_end = _last_month_window(conn)

    result: dict[str, object] = {
        "title": SAMPLE_PROBLEMS.get(template_id, "Analysis"),
        "scope": "",
        "kpis": {},
        "causes": pd.DataFrame(),
        "samples": pd.DataFrame(),
        "compare": pd.DataFrame(),
        "recommendations": [],
        "explanation": "",
    }

    if template_id == "city_delayed_date_range":
        where_sql = "date(a.order_date) BETWEEN ? AND ? AND a.city = ?"
        params = (guided_start_date, guided_end_date, city)
        result["scope"] = f"City={city}, Date Range={guided_start_date} to {guided_end_date}"
        result["kpis"] = _kpi_for_where(conn, "date(order_date) BETWEEN ? AND ? AND city = ?", params)
        result["causes"] = _causes_for_where(conn, where_sql, params)
        result["samples"] = _samples_for_where(conn, "date(order_date) BETWEEN ? AND ? AND city = ?", params)
        result["recommendations"] = _recommendations_from_causes(result["causes"])
        result["explanation"] = "This answer filters orders in the selected city and date range, then ranks root causes by frequency."

    elif template_id == "client_failures_past_week":
        where_sql = "date(a.order_date) BETWEEN ? AND ? AND a.client_name = ? AND lower(coalesce(a.status, '')) = 'failed'"
        params = (str(last_week_start), str(max_order_date), client)
        result["scope"] = f"Client={client}, Period={last_week_start} to {max_order_date}, Failed orders only"
        result["kpis"] = _kpi_for_where(conn, "date(order_date) BETWEEN ? AND ? AND client_name = ?", (str(last_week_start), str(max_order_date), client))
        result["causes"] = _causes_for_where(conn, where_sql, params)
        result["samples"] = _samples_for_where(conn, "date(order_date) BETWEEN ? AND ? AND client_name = ?", (str(last_week_start), str(max_order_date), client))
        result["recommendations"] = _recommendations_from_causes(result["causes"])
        result["explanation"] = "This answer focuses on one client over the last 7 days and highlights failure-related causes and impacted orders."

    elif template_id == "warehouse_august_reasons":
        where_sql = "strftime('%Y-%m', a.order_date) = '2025-08' AND a.warehouse_name = ?"
        params = (warehouse,)
        result["scope"] = f"Warehouse={warehouse}, Month=2025-08"
        result["kpis"] = _kpi_for_where(conn, "strftime('%Y-%m', order_date) = '2025-08' AND warehouse_name = ?", params)
        result["causes"] = _causes_for_where(conn, where_sql, params)
        result["samples"] = _samples_for_where(conn, "strftime('%Y-%m', order_date) = '2025-08' AND warehouse_name = ?", params)
        result["recommendations"] = _recommendations_from_causes(result["causes"])
        result["explanation"] = "This answer filters to August operations for the selected warehouse and reports the dominant cause buckets."

    elif template_id == "city_vs_city_last_month":
        params = (month_start, month_end, city, city_b)
        compare_sql = """
            SELECT
                a.city,
                c.cause,
                COUNT(*) AS cause_count
            FROM fact_order_causes c
            JOIN fact_order_analysis a ON a.order_id = c.order_id
            WHERE date(a.order_date) BETWEEN ? AND ?
              AND a.city IN (?, ?)
            GROUP BY a.city, c.cause
            ORDER BY a.city, cause_count DESC
        """
        result["scope"] = f"Cities={city} vs {city_b}, Period={month_start} to {month_end}"
        result["compare"] = run_query(conn, compare_sql, params)
        result["kpis"] = {
            "city_a_orders": int(run_query(conn, "SELECT COUNT(*) AS n FROM fact_order_analysis WHERE date(order_date) BETWEEN ? AND ? AND city = ?", (month_start, month_end, city)).iloc[0]["n"]),
            "city_b_orders": int(run_query(conn, "SELECT COUNT(*) AS n FROM fact_order_analysis WHERE date(order_date) BETWEEN ? AND ? AND city = ?", (month_start, month_end, city_b)).iloc[0]["n"]),
        }
        result["recommendations"] = [
            "Focus first on the top non-common cause between the two cities.",
            "Apply city-specific SLA controls where cause distribution diverges.",
        ]
        result["explanation"] = "This answer compares cause distributions across two cities for the previous full month."

    elif template_id == "festival_period_risks":
        where_sql = "strftime('%Y-%m', a.order_date) = '2025-10'"
        params: tuple = ()
        result["scope"] = "Festival window assumed as October 2025"
        result["kpis"] = _kpi_for_where(conn, "strftime('%Y-%m', order_date) = '2025-10'", params)
        result["causes"] = _causes_for_where(conn, where_sql, params)
        result["samples"] = _samples_for_where(conn, "strftime('%Y-%m', order_date) = '2025-10'", params)
        result["recommendations"] = _recommendations_from_causes(result["causes"])
        result["explanation"] = "This answer uses the festival month slice to estimate likely delay and failure drivers before peak season."

    elif template_id == "client_onboarding_risk":
        kpis = _kpi_for_where(conn, "1=1", ())
        projected = int(20000 * float(kpis.get("late_rate", 0.0)) / 100.0)
        causes = _causes_for_where(conn, "1=1", (), limit=5)
        result["scope"] = "Network baseline + projected 20,000 additional monthly orders"
        result["kpis"] = {**kpis, "projected_delayed_orders": projected}
        result["causes"] = causes
        result["recommendations"] = _recommendations_from_causes(causes)
        result["explanation"] = "This answer uses current network late rate and cause mix as a baseline to estimate onboarding risk impact."

    return result


def render_guided_result(result: dict[str, object]) -> None:
    if not result:
        return

    st.markdown("### Analysis Answer")
    st.write(f"**Question:** {result.get('title', 'N/A')}")
    st.write(f"**Scope analyzed:** {result.get('scope', 'N/A')}")
    st.write(f"**How answer was generated:** {result.get('explanation', 'N/A')}")

    kpis = result.get("kpis", {}) or {}
    if kpis:
        cols = st.columns(min(4, len(kpis)))
        for idx, (k, v) in enumerate(kpis.items()):
            label = str(k).replace("_", " ").title()
            value = f"{v:.2f}%" if isinstance(v, float) and "rate" in str(k) else str(v)
            cols[idx % len(cols)].metric(label, value)

    compare_df = result.get("compare", pd.DataFrame())
    if isinstance(compare_df, pd.DataFrame) and not compare_df.empty:
        st.markdown("#### City Comparison (Cause Distribution)")
        st.dataframe(compare_df, use_container_width=True)
    else:
        causes_df = result.get("causes", pd.DataFrame())
        if isinstance(causes_df, pd.DataFrame) and not causes_df.empty:
            col_c1, col_c2 = st.columns([2, 1])
            col_c1.markdown("#### Top Causes")
            col_c1.dataframe(causes_df, use_container_width=True)
            col_c2.bar_chart(causes_df.set_index("cause"))

    samples_df = result.get("samples", pd.DataFrame())
    if isinstance(samples_df, pd.DataFrame) and not samples_df.empty:
        st.markdown("#### Sample Impacted Orders")
        st.dataframe(samples_df, use_container_width=True)

    recommendations = result.get("recommendations", []) or []
    if recommendations:
        st.markdown("#### Recommended Actions")
        for rec in recommendations:
            st.write(f"- {rec}")


def render_dashboard() -> None:
    st.set_page_config(page_title="Delivery Analysis Dashboard", layout="wide")
    st.title("Delivery Failure Root-Cause Dashboard")
    st.caption("Table-first analytics over sample logistics data")

    with st.sidebar:
        st.header("Data Setup")
        if st.button("Initialize/Refresh Tables + Models", type="primary"):
            with st.spinner("Loading CSVs into tables and building analysis views..."):
                load_stats, model_stats = ensure_database_ready()
            st.success("Database and analysis model refreshed")
            st.write("Loaded tables:")
            st.json(load_stats)
            st.write("Model stats:")
            st.json(model_stats)

        st.markdown("---")
        st.write(f"DB path: {DB_PATH}")

    if not DB_PATH.exists():
        st.warning("Database not found yet. Click 'Initialize/Refresh Tables + Models' in sidebar.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        # If the analysis view is missing (e.g. init ran but model build didn't), build it now.
        view_exists = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='view' AND name='fact_order_analysis'"
        ).fetchone()[0]
        if not view_exists:
            conn.close()
            with st.spinner("Building analysis model for the first time..."):
                build_analysis_model(db_path=DB_PATH)
            conn = sqlite3.connect(DB_PATH)

        cities, clients, warehouses = fetch_filter_options(conn)
        date_ranges = fetch_date_ranges(conn)

        # If date ranges are missing, bootstrap data/model once and recompute.
        if _has_missing_date_ranges(date_ranges):
            conn.close()
            with st.spinner("Date ranges not available yet. Loading dataset and rebuilding analysis model..."):
                ensure_database_ready()
            conn = sqlite3.connect(DB_PATH)
            cities, clients, warehouses = fetch_filter_options(conn)
            date_ranges = fetch_date_ranges(conn)
        min_date = _safe_to_date(date_ranges.get("order_min_date"))
        max_date = _safe_to_date(date_ranges.get("order_max_date"))
        if min_date > max_date:
            min_date, max_date = max_date, min_date

        st.subheader("Available Data")
        col_d1, col_d2 = st.columns(2)
        col_d1.metric(
            "Order Activity Range",
            f"{date_ranges['order_min_date'] or 'N/A'} to {date_ranges['order_max_date'] or 'N/A'}",
        )
        col_d2.metric(
            "Full Dataset Range",
            f"{date_ranges['dataset_min_date'] or 'N/A'} to {date_ranges['dataset_max_date'] or 'N/A'}",
        )

        st.subheader("Sample Problem Statements")
        question_options = [SAMPLE_PROBLEMS[k] for k in SAMPLE_PROBLEMS]
        key_to_question = {v: k for k, v in SAMPLE_PROBLEMS.items()}
        selected_question = st.selectbox("Choose a sample question", options=question_options)
        selected_template = key_to_question[selected_question]

        default_city = cities[0] if cities else ""
        default_city_b = cities[1] if len(cities) > 1 else default_city
        default_client = clients[0] if clients else ""
        default_warehouse = warehouses[0] if warehouses else ""

        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        q_city = col_q1.selectbox("City A", options=cities or [""], index=0 if cities else 0, key="guided_city")
        q_city_b = col_q2.selectbox("City B", options=cities or [""], index=1 if len(cities) > 1 else 0, key="guided_city_b")
        q_client = col_q3.selectbox("Client", options=clients or [""], index=0 if clients else 0, key="guided_client")
        q_warehouse = col_q4.selectbox("Warehouse", options=warehouses or [""], index=0 if warehouses else 0, key="guided_warehouse")

        guided_date_range = st.date_input(
            "Guided Analysis Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="guided_date_range",
        )
        if isinstance(guided_date_range, tuple) and len(guided_date_range) == 2:
            guided_start, guided_end = guided_date_range
        else:
            guided_start, guided_end = min_date, max_date

        run_cols = st.columns([1, 3])
        if run_cols[0].button("Run Analysis", type="primary"):
            guided_result = run_template_analysis(
                conn,
                selected_template,
                q_city or default_city,
                q_client or default_client,
                q_warehouse or default_warehouse,
                q_city_b or default_city_b,
                str(guided_start),
                str(guided_end),
            )
            st.session_state["guided_result"] = guided_result

        if "guided_result" in st.session_state:
            render_guided_result(st.session_state["guided_result"])

        st.markdown("#### Ask Similar Question")
        question_text = st.text_input(
            "Type a similar business question",
            placeholder="Example: Compare delay causes between Pune and Chennai last month",
        )
        if st.button("Analyze Similar Question"):
            mapped_template, mapping_reason = map_question_to_template(question_text)
            st.info(f"Mapped to template: {SAMPLE_PROBLEMS[mapped_template]} | {mapping_reason}")
            similar_result = run_template_analysis(
                conn,
                mapped_template,
                q_city or default_city,
                q_client or default_client,
                q_warehouse or default_warehouse,
                q_city_b or default_city_b,
                str(guided_start),
                str(guided_end),
            )
            st.session_state["guided_result"] = similar_result
            render_guided_result(similar_result)

        st.subheader("Filters")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        city = col_f1.selectbox("City", options=["All"] + cities)
        client = col_f2.selectbox("Client", options=["All"] + clients)
        warehouse = col_f3.selectbox("Warehouse", options=["All"] + warehouses)

        date_range = col_f4.date_input("Order Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date

        where_clauses = ["date(order_date) BETWEEN ? AND ?"]
        params: list[str] = [str(start_date), str(end_date)]

        if city != "All":
            where_clauses.append("city = ?")
            params.append(city)
        if client != "All":
            where_clauses.append("client_name = ?")
            params.append(client)
        if warehouse != "All":
            where_clauses.append("warehouse_name = ?")
            params.append(warehouse)

        where_sql = " AND ".join(where_clauses)

        kpi_sql = f"""
            SELECT
                COUNT(*) AS total_orders,
                AVG(is_late) * 100.0 AS late_rate,
                AVG(CASE WHEN lower(coalesce(status, '')) = 'failed' THEN 1.0 ELSE 0.0 END) * 100.0 AS failed_rate
            FROM fact_order_analysis
            WHERE {where_sql}
        """
        kpi_df = run_query(conn, kpi_sql, tuple(params))

        total_orders = int(kpi_df.iloc[0]["total_orders"] or 0)
        late_rate = float(kpi_df.iloc[0]["late_rate"] or 0.0)
        failed_rate = float(kpi_df.iloc[0]["failed_rate"] or 0.0)

        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Orders Analyzed", f"{total_orders}")
        col_k2.metric("Late Rate", f"{late_rate:.2f}%")
        col_k3.metric("Failed Rate", f"{failed_rate:.2f}%")

        st.subheader("Top Causes")
        causes_sql = f"""
            SELECT
                c.cause,
                COUNT(*) AS cause_count
            FROM fact_order_causes c
            JOIN fact_order_analysis a ON a.order_id = c.order_id
            WHERE {where_sql}
            GROUP BY c.cause
            ORDER BY cause_count DESC
            LIMIT 10
        """
        causes_df = run_query(conn, causes_sql, tuple(params))

        if causes_df.empty:
            st.info("No cause data found for selected filters.")
        else:
            col_c1, col_c2 = st.columns([2, 1])
            col_c1.dataframe(causes_df, use_container_width=True)
            col_c2.bar_chart(causes_df.set_index("cause"))

        st.subheader("Sample Impacted Orders")
        samples_sql = f"""
            SELECT
                order_id,
                city,
                client_name,
                warehouse_name,
                round(delay_hours, 2) AS delay_hours,
                status
            FROM fact_order_analysis
            WHERE {where_sql}
            ORDER BY delay_hours DESC
            LIMIT 20
        """
        sample_df = run_query(conn, samples_sql, tuple(params))
        st.dataframe(sample_df, use_container_width=True)

        st.subheader("Recommendations by Cause")
        rec_df = run_query(
            conn,
            """
            SELECT DISTINCT cause, recommendation
            FROM fact_order_causes
            WHERE cause <> 'unknown'
            ORDER BY cause
            """,
        )
        st.dataframe(rec_df, use_container_width=True)

        st.subheader("Simple Query Runner")
        default_sql = """
SELECT city, COUNT(*) AS total_orders, ROUND(AVG(is_late) * 100, 2) AS late_rate_pct
FROM fact_order_analysis
GROUP BY city
ORDER BY late_rate_pct DESC
LIMIT 10;
""".strip()
        custom_sql = st.text_area("Run a read-only SELECT query", value=default_sql, height=150)

        if st.button("Run Query"):
            sql_trim = custom_sql.strip().lower()
            if not sql_trim.startswith("select"):
                st.error("Only SELECT queries are allowed.")
            else:
                try:
                    result_df = run_query(conn, custom_sql)
                    st.dataframe(result_df, use_container_width=True)
                except Exception as exc:
                    st.error(f"Query failed: {exc}")

    finally:
        conn.close()


if __name__ == "__main__":
    render_dashboard()
