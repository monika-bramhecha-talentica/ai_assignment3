"""Lightweight analytics helper to correlate delivery failures/delays.

This script reads the sample data set in `third-assignment-sample-data-set`
and prints narrative answers for common operational questions:
- Why were deliveries delayed in a city/date range?
- Why did a client's orders fail in a period?
- What are top failure drivers for a warehouse or city pair?
- What to expect during peak/festival periods.

Run:
    python analyze_deliveries.py

Optional flags:
    --data-dir /path/to/third-assignment-sample-data-set
    --city "Bengaluru"
    --warehouse "Warehouse 8"
    --client "Saini LLC"
    --start-date 2025-08-01 --end-date 2025-08-31
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "third-assignment-sample-data-set"


# ---------- Data loading and enrichment ----------
def load_dataset(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    date_cols = {
        "orders": ["order_date", "promised_delivery_date", "actual_delivery_date", "created_at"],
        "fleet_logs": ["departure_time", "arrival_time", "created_at"],
        "warehouse_logs": ["picking_start", "picking_end", "dispatch_time"],
        "external_factors": ["recorded_at"],
        "feedback": ["created_at"],
        "warehouses": ["created_at"],
        "drivers": ["created_at"],
        "clients": ["created_at"],
    }

    def read_csv(name: str) -> pd.DataFrame:
        path = data_dir / f"{name}.csv"
        return pd.read_csv(path, parse_dates=date_cols.get(name, []), dtype=str)

    dfs = {name: read_csv(name) for name in [
        "orders",
        "fleet_logs",
        "warehouse_logs",
        "external_factors",
        "feedback",
        "warehouses",
        "drivers",
        "clients",
    ]}

    # Cast numeric-like columns that we need for calculations.
    dfs["orders"]["amount"] = dfs["orders"]["amount"].astype(float)
    for col in ("driver_id",):
        dfs["fleet_logs"][col] = dfs["fleet_logs"][col].astype(int)
    return dfs


def _aggregate_external_factors(df: pd.DataFrame) -> pd.DataFrame:
    severity = {"Heavy": 2, "Moderate": 1, "Clear": 0}

    def pick_best(group: pd.DataFrame) -> pd.Series:
        # Pick the row with the worst traffic; keep earliest record time.
        group = group.copy()
        group["traffic_score"] = group["traffic_condition"].map(severity).fillna(0)
        best = group.sort_values(["traffic_score", "recorded_at"], ascending=[False, True]).iloc[0]
        return pd.Series(
            {
                "traffic_condition": best["traffic_condition"],
                "weather_condition": best["weather_condition"],
                "event_type": best["event_type"],
                "traffic_score": best["traffic_score"],
            }
        )

    return df.groupby("order_id", as_index=False).apply(pick_best)


def _aggregate_feedback(df: pd.DataFrame) -> pd.DataFrame:
    keywords = {
        "late": "late_delivery",
        "delay": "late_delivery",
        "slow": "late_delivery",
        "address": "address_issue",
        "wrong address": "address_issue",
        "cancel": "cancellation",
        "stock": "stock_issue",
        "update": "poor_comm",
    }

    def summarize(group: pd.DataFrame) -> pd.Series:
        sentiments = Counter(group["sentiment"].fillna("Unknown"))
        rating_avg = pd.to_numeric(group["rating"], errors="coerce").mean()
        buckets = []
        for text in group["feedback_text"].dropna():
            text_lower = text.lower()
            for needle, label in keywords.items():
                if needle in text_lower:
                    buckets.append(label)
        return pd.Series(
            {
                "feedback_sentiment_top": sentiments.most_common(1)[0][0] if sentiments else np.nan,
                "feedback_rating_avg": rating_avg,
                "feedback_tags": list(set(buckets)),
            }
        )

    return df.groupby("order_id", as_index=False).apply(summarize)


def enrich_orders(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = dfs["orders"].copy()
    # Merge warehouse mapping (one row per order assumed).
    wh = dfs["warehouse_logs"].copy()
    wh["picking_minutes"] = (wh["picking_end"] - wh["picking_start"]).dt.total_seconds() / 60
    wh["dispatch_lag_minutes"] = (wh["dispatch_time"] - wh["picking_end"]).dt.total_seconds() / 60
    wh = wh.groupby("order_id", as_index=False).first()

    fleet = dfs["fleet_logs"].copy()
    fleet["transit_hours"] = (fleet["arrival_time"] - fleet["departure_time"]).dt.total_seconds() / 3600
    fleet = fleet.groupby("order_id", as_index=False).first()

    external = _aggregate_external_factors(dfs["external_factors"])
    feedback = _aggregate_feedback(dfs["feedback"])

    orders = (
        orders.merge(wh, on="order_id", how="left", suffixes=("", "_wh"))
        .merge(fleet, on="order_id", how="left", suffixes=("", "_fleet"))
        .merge(external, on="order_id", how="left")
        .merge(feedback, on="order_id", how="left")
        .merge(dfs["warehouses"][["warehouse_id", "warehouse_name", "city", "state"]].rename(
            columns={"city": "warehouse_city", "state": "warehouse_state"}
        ), on="warehouse_id", how="left")
        .merge(dfs["clients"][["client_id", "client_name"]], on="client_id", how="left")
    )

    orders["promised_delivery_date"] = pd.to_datetime(orders["promised_delivery_date"])
    orders["actual_delivery_date"] = pd.to_datetime(orders["actual_delivery_date"])
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    orders["delay_hours"] = (
        (orders["actual_delivery_date"] - orders["promised_delivery_date"])
        .dt.total_seconds()
        / 3600
    )
    orders["delay_hours"] = orders["delay_hours"].fillna(0)
    orders["is_late"] = orders["delay_hours"] > 0.01
    return orders


# ---------- Cause inference ----------
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


def infer_causes(row: pd.Series) -> List[str]:
    causes: list[str] = []
    text_fields = " ".join(
        str(x).lower()
        for x in [
            row.get("failure_reason", ""),
            row.get("gps_delay_notes", ""),
            row.get("notes", ""),
        ]
        if pd.notna(x)
    )

    if "stock" in text_fields:
        causes.append("stockout")
    if "slow" in text_fields or (row.get("picking_minutes") and row["picking_minutes"] > 30):
        causes.append("warehouse_delay")
    if row.get("dispatch_lag_minutes") and row["dispatch_lag_minutes"] > 45:
        causes.append("dispatch_lag")
    if "address" in text_fields:
        causes.append("address_issue")
    if "breakdown" in text_fields:
        causes.append("vehicle_issue")
    if "congestion" in text_fields or (row.get("traffic_score", 0) and row["traffic_score"] >= 1):
        causes.append("traffic")
    if row.get("weather_condition") in {"Rain", "Fog"}:
        causes.append("weather")
    if pd.notna(row.get("event_type")) and row["event_type"] != "":
        causes.append("event")
    if row.get("is_late"):
        causes.append("late_delivery")
    tags = row.get("feedback_tags")
    if isinstance(tags, (list, tuple, set)):
        causes.extend(tags)
    return sorted(set(causes))


# ---------- Analytics helpers ----------
@dataclass
class Insight:
    scope: str
    orders_considered: int
    late_rate: float
    top_causes: list[tuple[str, int]]
    recommendations: list[str]
    sample_orders: list[int]


def build_insight(orders: pd.DataFrame, scope: str) -> Insight:
    if orders.empty:
        return Insight(scope, 0, 0.0, [], [], [])

    orders = orders.copy()
    orders["causes"] = orders.apply(infer_causes, axis=1)
    exploded = orders.explode("causes")
    cause_counts = exploded["causes"].value_counts().to_dict()
    top_causes = sorted(cause_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]

    recommendations = []
    for cause, _ in top_causes:
        action = CAUSE_ACTIONS.get(cause)
        if action:
            recommendations.append(f"{cause}: {action}")

    sample_orders = (
        exploded.sort_values("delay_hours", ascending=False)["order_id"].dropna().astype(int).head(5).tolist()
    )

    late_rate = float((orders["is_late"].mean() * 100).round(2))
    return Insight(
        scope=scope,
        orders_considered=len(orders),
        late_rate=late_rate,
        top_causes=top_causes,
        recommendations=recommendations,
        sample_orders=sample_orders,
    )


def filter_orders(
    orders: pd.DataFrame,
    city: Optional[str] = None,
    client: Optional[str] = None,
    warehouse: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    df = orders.copy()
    if city:
        df = df[df["city"].str.lower() == city.lower()]
    if client:
        df = df[df["client_name"].str.contains(client, case=False, na=False)]
    if warehouse:
        df = df[df["warehouse_name"].str.contains(warehouse, case=False, na=False)]
    if start_date:
        df = df[df["order_date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["order_date"] <= pd.to_datetime(end_date)]
    return df


# ---------- Demo runner ----------
def demo(orders: pd.DataFrame) -> None:
    scenarios = [
        ("City delayed yesterday (example: Bengaluru)", dict(city="Bengaluru")),
        ("Client X failures last 7 days (example: Saini LLC)", dict(client="Saini LLC")),
        ("Warehouse B August issues (example: Warehouse 2)", dict(warehouse="Warehouse 2", start_date="2025-08-01", end_date="2025-08-31")),
        ("Compare City A vs City B (example: Pune vs Chennai)", dict()),  # handled separately
        ("Festival/peak period outlook (Oct 2025)", dict(start_date="2025-10-01", end_date="2025-10-31")),
        ("Onboarding Client Y risk model (~20k orders)", dict()),
    ]

    for title, params in scenarios:
        if "Compare City A" in title:
            compare_cities(orders, "Pune", "Chennai", "2025-08-01", "2025-08-31")
            continue
        if "Client Y" in title:
            onboarding_risk(orders, "Client Y (hypothetical)")
            continue
        print("\n" + "=" * 70)
        print(title)
        scoped = filter_orders(orders, **params)
        insight = build_insight(scoped, scope=title)
        print_insight(insight)


def compare_cities(orders: pd.DataFrame, city_a: str, city_b: str, start: str, end: str) -> None:
    print("\n" + "=" * 70)
    print(f"Compare {city_a} vs {city_b} ({start} to {end})")
    for city in (city_a, city_b):
        scoped = filter_orders(orders, city=city, start_date=start, end_date=end)
        insight = build_insight(scoped, scope=city)
        print_insight(insight)


def onboarding_risk(orders: pd.DataFrame, client_name: str) -> None:
    print("\n" + "=" * 70)
    print(f"Onboarding risk outlook for {client_name}")
    # Use overall top causes as proxy risk; scale by expected volume.
    insight = build_insight(orders, scope="network baseline")
    volume = 20000
    print(f"Baseline late rate: {insight.late_rate}% | projected delayed orders per month: ~{int(volume * insight.late_rate / 100)}")
    print("Top network risks to mitigate before launch:")
    for cause, count in insight.top_causes:
        action = CAUSE_ACTIONS.get(cause, "")
        print(f"- {cause}: {count} occurrences | {action}")
    print("Operational playbook:")
    print("- Stagger rollout by city/warehouse; start with top-performing lanes.")
    print("- Holdback 5% capacity as surge buffer; pre-book extra vehicles.")
    print("- Enforce address validation + customer contactability checks on day 1.")


def print_insight(insight: Insight) -> None:
    if insight.orders_considered == 0:
        print("No orders matched the filter.")
        return
    print(f"Scope: {insight.scope}")
    print(f"Orders analyzed: {insight.orders_considered}")
    print(f"Late/failed rate: {insight.late_rate}%")
    print("Top causes:")
    for cause, count in insight.top_causes:
        print(f"- {cause}: {count}")
    if insight.recommendations:
        print("Recommendations:")
        for rec in insight.recommendations:
            print(f"- {rec}")
    if insight.sample_orders:
        print(f"Sample impacted order_ids: {insight.sample_orders}")


def main():
    dfs = load_dataset()
    orders = enrich_orders(dfs)
    demo(orders)


if __name__ == "__main__":
    main()

