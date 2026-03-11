# 3-Minute Demo Script (Quick Submission Version)

## Objective
Deliver a fast walkthrough of the root-cause analytics system with one clean run and key insights.

## Before recording (15 sec)
- Open terminal in project root.
- Run: `source .venv/bin/activate`
- Keep these open in editor:
  - `analyze_deliveries.py`
  - `docs/sample_outputs.txt`

---

## 0:00–0:25 | Intro
**Say:**
- “This solution explains why deliveries fail or get delayed by combining orders, fleet, warehouse, external factors, and customer feedback.”
- “Instead of just counts, it produces root causes and operational recommendations.”

---

## 0:25–0:45 | Data + approach
**Say:**
- “`orders.csv` is the base table, linked with event logs by `order_id`.”
- “The script computes delay and process metrics, then applies rule-based cause inference like traffic, stockout, dispatch lag, address issues, weather, and events.”

---

## 0:45–1:00 | Setup proof
**Run:**
- `python test_setup.py`

**Say:**
- “Environment, dependencies, and all data files are validated.”

---

## 1:00–2:20 | Main execution and highlights
**Run:**
- `python analyze_deliveries.py`

**Say while scrolling output:**
- “City scenario shows major drivers like traffic and event disruptions.”
- “Client scenario isolates account-level failure causes.”
- “Warehouse scenario surfaces dispatch and operational bottlenecks.”
- “City comparison shows relative risk between two locations.”
- “Onboarding outlook projects expected delayed volume for 20k monthly orders and lists mitigation actions.”

---

## 2:20–2:45 | Recommendations
**Say:**
- “Top actions are dynamic routing, event contingency plans, weather ETA buffering, address validation, and tighter warehouse dispatch SLAs.”

---

## 2:45–3:00 | Close
**Run (optional):**
- `python analyze_deliveries.py > docs/sample_outputs.txt`

**Say:**
- “Outputs are reproducible and saved for reporting. The final documentation is in `docs/submission_ready_report.md`.”
- “This provides an actionable, explainable decision-support layer for delivery operations.”

---

## One-line fallback (if short on time)
“System ingests multi-source delivery data, infers root causes per order, and prints prioritized actions by city/client/warehouse scenario in a reproducible pipeline.”
