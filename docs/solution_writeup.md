# Delivery Failure Root-Cause Analysis Solution Document

## 1. Executive Summary
This solution addresses the logistics challenge of explaining why deliveries fail or get delayed across siloed systems. The implementation uses a table-first architecture:

1. Load all sample CSV files into SQL tables.
2. Build an enriched analysis view over those tables.
3. Infer likely root causes using transparent business rules.
4. Surface answers through a simple Streamlit dashboard with guided problem statements and explainable outputs.

The system supports all requested sample use cases, including city and client diagnostics, warehouse-specific failure reasons, city comparisons, festival-risk analysis, and onboarding risk simulation.

## 2. Problem Context
Delivery failures are influenced by multiple factors that live in different systems:

- Orders and promised vs actual delivery timelines
- Fleet execution notes and transit movement
- Warehouse processing bottlenecks
- External disruptions (traffic/weather/events)
- Customer feedback and sentiment

Manual investigation across these systems is slow and reactive. The objective is to generate fast, human-readable root-cause insights and action recommendations.

## 3. Data Sources and Model
Data folder: `third-assignment-sample-data-set/`

### 3.1 Source Files
- `orders.csv`
- `fleet_logs.csv`
- `warehouse_logs.csv`
- `external_factors.csv`
- `feedback.csv`
- `warehouses.csv`
- `clients.csv`
- `drivers.csv`

### 3.2 Table Mapping
- `orders.csv` -> `raw_orders`
- `fleet_logs.csv` -> `raw_fleet_logs`
- `warehouse_logs.csv` -> `raw_warehouse_logs`
- `external_factors.csv` -> `raw_external_factors`
- `feedback.csv` -> `raw_feedback`
- `warehouses.csv` -> `dim_warehouses`
- `clients.csv` -> `dim_clients`
- `drivers.csv` -> `dim_drivers`

### 3.3 Join Logic
- Primary key: `order_id`
- Secondary keys: `client_id`, `warehouse_id`, `driver_id`

## 4. Solution Architecture

### 4.1 Data Ingestion Layer
Implemented in `init_db.py`:

- Creates a local SQLite database (`analytics.db`)
- Loads all sample CSV files into corresponding tables
- Normalizes datetime columns into SQL-compatible text format
- Adds indexes on critical join keys
- Validates row counts for all loaded tables

### 4.2 Analysis Modeling Layer
Implemented in `build_analysis_model.py`:

- Builds `fact_order_analysis` view by joining raw and dimension tables
- Computes reusable metrics:
  - `delay_hours`
  - `is_late`
  - `transit_hours`
  - `picking_minutes`
  - `dispatch_lag_minutes`
  - `traffic_score`
- Aggregates feedback context and external factors per order
- Generates `fact_order_causes` table with inferred cause labels and mapped recommendations

### 4.3 Dashboard and Query Layer
Implemented in `dashboard.py`:

- Displays data availability ranges
- Supports filter-based analysis (city/client/warehouse/date range)
- Shows KPI cards, top causes, impacted samples, and recommendations
- Includes sample-problem templates from the assignment
- Provides one-click guided analysis and explainable answer section
- Supports user-entered "similar questions" with template intent mapping

## 5. Root-Cause Inference Method
The system uses transparent rule-based logic (easy to explain during demo):

- `stockout`: stock-related keywords in failure/notes/feedback
- `warehouse_delay`: slow-packing notes or high picking time
- `dispatch_lag`: high dispatch lag threshold breach
- `traffic`: traffic severity or congestion notes
- `weather`: rain/fog conditions
- `event`: strike/holiday/event markers
- `address_issue`: address-related complaint patterns
- `vehicle_issue`: breakdown-related signals
- `late_delivery`: delay exceeds threshold
- `poor_comm`: communication-gap language (for example, "no update")

Multiple causes may be assigned to a single order when evidence supports it.

## 6. Supported Business Questions
The implementation supports the required questions:

1. Why were deliveries delayed in city X (now using selected date range)?
2. Why did Client X's orders fail in the past week?
3. Top reasons for delivery failures linked to Warehouse B in August.
4. Compare delivery failure causes between City A and City B last month.
5. Likely causes during festival period and preparation recommendations.
6. Onboarding Client Y (+20,000 monthly orders) risk and mitigations.

## 7. Dashboard Explanation Output
For each selected question, the dashboard returns:

- Scope analyzed
- KPI summary
- Top cause distribution
- Sample impacted orders
- Action recommendations
- Explanation text of how the answer was derived

This satisfies the need for human-readable, decision-oriented outputs.

## 8. Date Range Availability in Current Dataset
Validated from the loaded tables:

- Order activity range: `2025-01-01` to `2025-09-19`
- Full dataset range (including master data): `2020-01-01` to `2025-09-19`

## 9. How to Run

```bash
cd /Users/monika/projects/ai_assignemnts
source .venv/bin/activate
python init_db.py
python build_analysis_model.py
streamlit run dashboard.py
```

Optional CLI analytics run:

```bash
python analyze_deliveries.py
```

## 10. Deliverables Produced
- Table-first ingestion script: `init_db.py`
- Analysis view/cause builder: `build_analysis_model.py`
- Interactive dashboard: `dashboard.py`
- Implementation plan: `PLAN.md`
- Problem statement input: `problem_statements.txt`
- Sample run output capture: `docs/sample_outputs.txt`

## 11. Limitations and Next Improvements

### Current limitations
- Rule-based inference may miss nuanced causal interactions
- Some questions rely on fixed template assumptions (for example, festival window)
- Text keyword inference quality depends on note/feedback quality

### Next improvements
- Add ML-based cause ranking on top of rule outputs
- Add confidence score per inferred cause
- Add scenario-specific visualization tabs
- Export dashboard answers directly to `.docx` for submission packaging

## 12. Conclusion
This solution converts fragmented logistics signals into a practical analytics workflow that is easy to run, explain, and demo. It provides both operational visibility (what is failing) and actionable diagnosis (why it is failing and what to do next), aligned to the assignment's expected outcomes.





