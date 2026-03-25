#!/usr/bin/env python3
"""Initialize SQLite database and load all sample CSV files into tables.

Run:
    python init_db.py

Optional:
    python init_db.py --db-path analytics.db --data-dir third-assignment-sample-data-set
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "third-assignment-sample-data-set"
DEFAULT_DB_PATH = BASE_DIR / "analytics.db"

TABLE_FILE_MAP = {
    "raw_orders": "orders.csv",
    "raw_fleet_logs": "fleet_logs.csv",
    "raw_warehouse_logs": "warehouse_logs.csv",
    "raw_external_factors": "external_factors.csv",
    "raw_feedback": "feedback.csv",
    "dim_warehouses": "warehouses.csv",
    "dim_clients": "clients.csv",
    "dim_drivers": "drivers.csv",
}

DATE_COLUMNS = {
    "raw_orders": ["order_date", "promised_delivery_date", "actual_delivery_date", "created_at"],
    "raw_fleet_logs": ["departure_time", "arrival_time", "created_at"],
    "raw_warehouse_logs": ["picking_start", "picking_end", "dispatch_time"],
    "raw_external_factors": ["recorded_at"],
    "raw_feedback": ["created_at"],
    "dim_warehouses": ["created_at"],
    "dim_clients": ["created_at"],
    "dim_drivers": ["created_at"],
}


def _load_csv(path: Path, parse_dates: list[str]) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, parse_dates=parse_dates)


def _normalize_columns(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    out = df.copy()
    date_cols = DATE_COLUMNS.get(table_name, [])
    for col in date_cols:
        if col not in out.columns:
            continue

        raw = out[col]
        parsed = pd.to_datetime(raw, errors="coerce")

        # If values are numeric-like epochs, parse explicitly as nanoseconds.
        if parsed.isna().all():
            numeric = pd.to_numeric(raw, errors="coerce")
            parsed = pd.to_datetime(numeric, unit="ns", errors="coerce")

        out[col] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
        out[col] = out[col].where(parsed.notna(), None)
    return out


def _create_indexes(conn: sqlite3.Connection) -> None:
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_raw_orders_order_id ON raw_orders(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_orders_client_id ON raw_orders(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_fleet_logs_order_id ON raw_fleet_logs(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_warehouse_logs_order_id ON raw_warehouse_logs(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_external_factors_order_id ON raw_external_factors(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_feedback_order_id ON raw_feedback(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_warehouse_logs_warehouse_id ON raw_warehouse_logs(warehouse_id)",
    ]
    for sql in index_statements:
        conn.execute(sql)


def _validate_row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLE_FILE_MAP:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        counts[table] = int(count)
    return counts


def initialize_database(db_path: Path = DEFAULT_DB_PATH, data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, int]:
    data_dir = Path(data_dir)
    db_path = Path(db_path)

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    conn = sqlite3.connect(db_path)
    try:
        for table, filename in TABLE_FILE_MAP.items():
            csv_path = data_dir / filename
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing source file: {csv_path}")

            df = _load_csv(csv_path, DATE_COLUMNS.get(table, []))
            df = _normalize_columns(df, table)
            df.to_sql(table, conn, if_exists="replace", index=False)

        _create_indexes(conn)
        conn.commit()
        return _validate_row_counts(conn)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create analytics DB and load all CSV data into tables.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Path to SQLite DB file")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Directory containing input CSV files")
    args = parser.parse_args()

    counts = initialize_database(db_path=args.db_path, data_dir=args.data_dir)
    print(f"Database ready: {args.db_path}")
    print("Loaded tables:")
    for table, count in counts.items():
        print(f"- {table}: {count}")


if __name__ == "__main__":
    main()
