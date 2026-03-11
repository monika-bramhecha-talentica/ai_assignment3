# Delivery Failure Root-Cause Analysis System

## 1. Executive Summary
This project analyzes multi-domain logistics data to identify why deliveries fail or get delayed, not just how many were affected. The solution combines order records, fleet logs, warehouse operations, external disruption signals, and customer feedback into one enriched order-level view. A rule-based inference engine then assigns likely root causes and generates action-oriented recommendations for operations teams.

The implementation is available in `analyze_deliveries.py`, with setup validation in `test_setup.py`, and sample run outputs captured in `docs/sample_outputs.txt`.

---

## 2. Business Problem
Delivery performance issues are driven by multiple systems and stakeholders. Manual diagnosis across siloed data sources is slow and error-prone. The required capability is an automated workflow that can:
- Correlate events across order lifecycle stages.
- Explain likely root causes in plain language.
- Prioritize operational actions per scenario.

---

## 3. Data Set Studied
Data folder: `third-assignment-sample-data-set/`

Files analyzed:
- `orders.csv`
- `fleet_logs.csv`
- `warehouse_logs.csv`
- `external_factors.csv`
- `feedback.csv`
- `warehouses.csv`
- `drivers.csv`
- `clients.csv`

### Data model (high level)
- Primary analytical grain: **order_id**.
- Core fact table: `orders.csv`.
- Event tables joined by `order_id`: fleet, warehouse, external factors, feedback.
- Dimension enrichment:
  - Warehouse metadata from `warehouses.csv` via `warehouse_id`.
  - Client metadata from `clients.csv` via `client_id`.

### Observed structure notes
- `orders.csv` includes lifecycle dates (`order_date`, `promised_delivery_date`, `actual_delivery_date`), status, amount, and failure reason.
- Event tables can contain multiple records per `order_id`; script aggregates these to one order-level view before final inference.
- Missing `actual_delivery_date` is expected for non-delivered orders.

---

## 4. Solution Approach Implemented

### 4.1 Ingestion and Enrichment
- Parse timestamp columns from all CSVs.
- Standardize selected numeric columns.
- Merge operational and contextual data into one enriched orders DataFrame.

### 4.2 Feature Engineering
Derived metrics include:
- `delay_hours` = actual delivery timestamp minus promised delivery timestamp.
- `is_late` flag from delay threshold.
- `transit_hours` from fleet departure/arrival.
- `picking_minutes` and `dispatch_lag_minutes` from warehouse logs.
- External traffic severity score (Heavy > Moderate > Clear).
- Feedback tags from keyword extraction (e.g., delay, address, stock, communication).

### 4.3 Root-Cause Inference Rules
Cause labels detected per order from structured and textual signals:
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

### 4.4 Insight Generation
For a selected scope (city/client/warehouse/date range), the script outputs:
- Orders analyzed.
- Late/failed rate.
- Top causes with counts.
- Recommendations mapped to each cause.
- Sample impacted order IDs.

---

## 5. Scenario Results (Sample Run)
Source: `docs/sample_outputs.txt`

### Use Case 1: City delays (Bengaluru example)
- Orders analyzed: **997**
- Late/failed rate: **12.34%**
- Top causes: `traffic (591)`, `event (468)`, `late_delivery (418)`, `weather (407)`, `address_issue (367)`

### Use Case 2: Client failures (Saini LLC example)
- Orders analyzed: **28**
- Late/failed rate: **10.71%**
- Top causes: `traffic (19)`, `event (18)`, `weather (16)`, `address_issue (10)`, `cancellation (8)`

### Use Case 3: Warehouse August issues (Warehouse 2 example)
- Orders analyzed: **170**
- Late/failed rate: **14.71%**
- Top causes: `traffic (114)`, `event (100)`, `weather (78)`, `late_delivery (70)`, `dispatch_lag (68)`

### Use Case 4: City comparison (Pune vs Chennai, Aug 2025)
- Pune: **66** orders, **15.15%** late/failed rate
- Chennai: **107** orders, **18.69%** late/failed rate
- Observation: Chennai shows higher late/failed rate in this window.

### Use Case 5: Festival/peak period outlook (Oct 2025)
- No matching orders in selected filter window for this sample run.

### Use Case 6: Onboarding risk (20k monthly orders, hypothetical)
- Baseline late rate: **12.71%**
- Projected delayed orders/month: **~2542**
- Top network risks: traffic, event, weather, late_delivery, address_issue

---

## 6. Operational Recommendations
Top recurring actions from inference-to-playbook mapping:
- Traffic risk: dynamic routing and slot re-allocation.
- Event disruptions: strike/holiday slowdown plans.
- Weather impact: buffered ETA and proactive customer alerts.
- Late delivery trend: improve promise calibration and live tracking visibility.
- Address issues: pre-ship address validation and driver assist workflows.
- Dispatch lag: stricter warehouse handoff SLA and cutoff alerts.

---

## 7. Assumptions and Limitations
- Rule-based inference is transparent and fast but not probabilistic/ML-ranked.
- Some orders can map to multiple causes simultaneously.
- Quality of free-text fields (notes/feedback) affects keyword-based signals.
- Scenario metrics vary based on selected city/client/date filters.

---

## 8. Reproducibility Steps
1. Activate environment:
   - `source .venv/bin/activate`
2. Validate setup:
   - `python test_setup.py`
3. Run analysis:
   - `python analyze_deliveries.py`
4. Capture output:
   - `python analyze_deliveries.py > docs/sample_outputs.txt`

---

## 9. Submission Checklist
- [x] Working analytics script: `analyze_deliveries.py`
- [x] Setup verification script: `test_setup.py`
- [x] Solution documentation: `docs/solution_writeup.md`
- [x] Sample output artifact: `docs/sample_outputs.txt`
- [ ] Convert this report to `.docx`
- [ ] Record demo video with voice narration
- [ ] Share GitHub repository link

---

## 10. Suggested Demo Narration (7–8 minutes)
1. Introduce business problem and source tables.
2. Explain enrichment and feature engineering pipeline.
3. Run city/client/warehouse scenarios and interpret causes.
4. Show city comparison and onboarding risk estimate.
5. Conclude with operational playbook and next enhancements.
