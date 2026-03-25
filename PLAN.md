# Assignment Execution Plan: Delivery Failure Root-Cause Analysis (Table-First)

## 1. Goal and Scope

Build a practical, demo-ready analytics solution that first loads all sample data into queryable SQL tables, then performs root-cause analysis and exposes a simple dashboard for filtered insights.

The solution should answer all sample business questions with narrative insights and action recommendations.

Core principle for this implementation:
1. Insert all sample CSV data into tables first.
2. Build analysis views on top of those tables.
3. Run business queries from tables/views (not ad-hoc file joins).

## 2. Inputs and Table Mapping

Data folder: `third-assignment-sample-data-set/`

Source files and target table names:
- `orders.csv` -> `raw_orders`
- `fleet_logs.csv` -> `raw_fleet_logs`
- `warehouse_logs.csv` -> `raw_warehouse_logs`
- `external_factors.csv` -> `raw_external_factors`
- `feedback.csv` -> `raw_feedback`
- `warehouses.csv` -> `dim_warehouses`
- `clients.csv` -> `dim_clients`
- `drivers.csv` -> `dim_drivers`

Primary join key:
- `order_id` (across orders, fleet, warehouse, external, feedback)

Secondary joins:
- `warehouse_id` -> warehouse attributes
- `client_id` -> client attributes
- `driver_id` -> driver attributes

## 3. Solution Approach

### Phase A: Load All Sample Data Into Tables (First Step)
1. Create local analytics DB (DuckDB or SQLite; DuckDB preferred for CSV ingestion speed).
2. Create staging/dimension tables listed above.
3. Insert all CSV data into their corresponding tables.
4. Validate row counts after each load.
5. Add data quality checks (null keys, duplicate order rows, invalid dates).

Deliverable:
- Persistent local database file with all sample data inserted into tables.

### Phase B: Build Query-Friendly Analytics View
Create an enriched order-level SQL view/table (`fact_order_analysis`) by joining all tables and computing reusable fields:
- `delay_hours` = `actual_delivery_date - promised_delivery_date`
- `is_late` boolean
- `transit_hours`
- `picking_minutes`
- `dispatch_lag_minutes`
- `traffic_score`
- feedback issue tags

Deliverable:
- One queryable analysis view that powers all downstream queries.

### Phase C: Root-Cause Inference Layer
Implement transparent, rule-based inference from `fact_order_analysis` with cause buckets:
- `stockout`
- `warehouse_delay`
- `dispatch_lag`
- `traffic`
- `weather`
- `event`
- `address_issue`
- `vehicle_issue`
- `late_delivery`
- `poor_comm`

Persist inferred causes in `fact_order_causes` table for easy reuse.

Deliverable:
- Order-level cause labels stored in table form.

### Phase D: Query Layer (SQL Templates)
Create reusable SQL templates/functions for:
1. City + date delay analysis
2. Client + period failure analysis
3. Warehouse + month top causes
4. City A vs City B comparison
5. Peak/festival period risk scan
6. Volume onboarding risk simulation

Deliverable:
- Query library that runs directly on tables/views.

### Phase E: Simple Dashboard for Analysis Queries
Create a lightweight dashboard (Streamlit) with:
- Filters: city, client, warehouse, date range
- KPI cards: orders analyzed, late rate, failed rate
- Top causes table/chart
- Sample impacted orders
- Recommendation panel by cause type
- "Sample Problem Statements" panel populated from assignment use cases
- One-click "Run Analysis" buttons for each sample question
- "Answer Explanation" section that explains: scope, top causes, evidence, and recommended actions
- "Ask Similar Question" input (template-driven) that maps user question intent to the closest supported analysis query
- Custom SQL/parameterized query runner section for quick analysis

Deliverable:
- Simple local dashboard where users can explore data and run basic analysis queries.

## 4. Implementation Tasks

### Task 1: Environment and Dependencies
- Create/activate virtual environment.
- Install dependencies from `requirements.txt`.
- Add dashboard/query dependencies if needed (`duckdb`, `streamlit`, `plotly`).
- Run setup check script.

### Task 2: Database Setup and Ingestion
- Create DB initialization script (`init_db.py`).
- Create all tables and load all sample CSVs into tables.
- Add row-count and schema validation logs.

### Task 3: Analysis Model Build
- Create model script (`build_analysis_model.py`).
- Build `fact_order_analysis` and `fact_order_causes`.
- Validate computed metrics and cause tagging quality.

### Task 4: Query Service
- Refactor analysis logic to query tables/views first.
- Add SQL templates for all six sample use cases.
- Ensure outputs are interpretable and non-empty.

### Task 5: Dashboard
- Build `dashboard.py` with filters and KPI panels.
- Add top-cause visualization and recommendation text.
- Add sample problem statement cards from `problem_statements.txt` use cases.
- Add one-click execution for each sample use case (including city vs city last month).
- Add explanation block for each answer (what was analyzed, why these causes are top, what to do next).
- Add "similar question" input with intent mapping to existing query templates.
- Add basic query section for ad-hoc analysis.

### Task 6: Output Capture and Documentation
- Capture query outputs for six scenarios.
- Update write-up with table-first architecture and dashboard screenshots.
- Add a simple data flow diagram (CSV -> Tables -> Analysis Views -> Dashboard).

### Task 7: Demo Recording and Packaging
- Demo both CLI output and dashboard filters/querying.
- Record a 3-5 minute walkthrough with voice.
- Prepare final submission assets (repo + docs + recording links).

## 5. Suggested 3-Day Timeline

Day 1:
- Environment setup
- Create DB and insert all sample data into tables
- Validate joins and row counts

Day 2:
- Build analysis views and cause-inference tables
- Implement six use-case SQL queries
- Build and test simple dashboard with sample-question analysis panel

Day 3:
- Capture outputs and dashboard screenshots
- Finalize write-up and diagram
- Record demo and package submission

## 6. Acceptance Criteria

The assignment is complete when:
1. All sample CSV data is inserted into SQL tables and validated.
2. All analysis queries run against tables/views successfully.
3. All six sample use cases are answered with:
   - quantified metrics
   - top cause categories
   - actionable recommendations
4. A simple dashboard allows filtering and basic query-driven analysis.
5. Dashboard shows sample problem statements and returns explained answers for each.
6. Dashboard supports user-entered similar questions via template mapping.
7. Write-up explains table model, query approach, and outcomes.
8. Demo video shows local execution and dashboard usage.

## 7. Risks and Mitigations

- Data quality gaps (missing timestamps/notes):
  - Apply null-safe SQL transforms and explicit fallback rules.
- Join/key mismatches across tables:
  - Add ingestion-time key validation and exception logging.
- Ambiguous causality from limited fields:
  - Keep inference rule-based and transparent.
- Dashboard complexity creep:
  - Limit v1 to filtering, KPI summary, and basic query section.

## 8. Final Submission Checklist

- [ ] Database created and all CSVs loaded into tables
- [ ] Analysis views/tables built and validated
- [ ] Six scenario queries executed from table layer
- [ ] Simple dashboard working locally with filters/queries
- [ ] Sample problem statements visible in dashboard with one-click analysis
- [ ] Answer explanation panel available for each executed question
- [ ] Similar-question input mapped to supported templates
- [ ] Outputs captured for documentation
- [ ] Write-up completed (Word format) with architecture + screenshots
- [ ] Voice demo video recorded
- [ ] GitHub repository link ready
- [ ] Shareable folder link ready
- [ ] Final email drafted with both links
