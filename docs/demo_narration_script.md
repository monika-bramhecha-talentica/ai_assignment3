# Demo Narration Script (7–8 Minutes)

## Goal
Show how the system finds delivery failure root causes from multi-source data and converts them into actionable operations recommendations.

## Pre-demo setup (30 sec, before recording)
- Open terminal at project root.
- Activate environment: `source .venv/bin/activate`
- Keep these files visible in editor:
  - `third-assignment-sample-data-set/`
  - `analyze_deliveries.py`
  - `docs/sample_outputs.txt`

---

## 0:00–0:30 | Introduction
**Say:**
- “This project solves a key logistics problem: teams know how many deliveries failed, but not why.”
- “We unify orders, fleet, warehouse, external factors, and customer feedback into one order-level analysis view.”
- “Then we infer root causes and print business recommendations.”

**Show:**
- Folder structure under `third-assignment-sample-data-set`.

---

## 0:30–1:15 | Data and pipeline overview
**Say:**
- “`orders.csv` is the base table and all event tables join on `order_id`.”
- “We derive delay, transit, pick-pack, and dispatch lag metrics.”
- “Rules map signals like congestion, stock issues, address problems, and weather to cause labels.”

**Show:**
- In `analyze_deliveries.py`, briefly scroll these sections:
  - data loading/enrichment
  - `infer_causes`
  - `build_insight`

---

## 1:15–1:40 | Verify setup
**Run:**
- `python test_setup.py`

**Say:**
- “Environment and data checks pass, so analysis is reproducible.”

---

## 1:40–4:40 | Run main analysis and explain outputs
**Run:**
- `python analyze_deliveries.py`

**Narrate each scenario quickly:**

### A) City delays (Bengaluru example)
**Say:**
- “This section explains city-level delay drivers.”
- “Current top causes are traffic, events, and late delivery signals.”
- “Actions include dynamic routing and ETA communication.”

### B) Client failures (Saini LLC example)
**Say:**
- “This isolates one client’s failure pattern over the selected window.”
- “We can see whether issues are operational, address-related, or external.”

### C) Warehouse August issues (Warehouse 2)
**Say:**
- “This links warehouse process delays to delivery outcomes.”
- “Dispatch lag and pick-pack delays become visible as causes.”

### D) City comparison (Pune vs Chennai)
**Say:**
- “This enables comparative diagnostics by city and period.”
- “In this sample, Chennai has a higher late/failed rate than Pune.”

### E) Peak period outlook
**Say:**
- “The selected October window has no matching rows in this sample run, which is also a valid analytical outcome.”

### F) Onboarding risk model (20k/month hypothetical)
**Say:**
- “Using the network baseline late rate, we project delayed volume and pre-launch risk controls.”

---

## 4:40–5:45 | Recommendations summary
**Say:**
- “Top cross-scenario actions are: traffic-based rerouting, event playbooks, weather buffering, address validation, and dispatch SLA control.”
- “This turns diagnostics into specific operational interventions.”

**Show:**
- Recommendations printed under each use case.

---

## 5:45–6:45 | Artifacts and reproducibility
**Run:**
- `python analyze_deliveries.py > docs/sample_outputs.txt`

**Say:**
- “Outputs are persisted for reporting and audit.”
- “The final write-up is in `docs/submission_ready_report.md`, with methodology, assumptions, and scenario results.”

---

## 6:45–7:30 | Conclusion
**Say:**
- “This solution automates root-cause discovery across siloed systems.”
- “It is transparent, reproducible, and immediately actionable for operations teams.”
- “Next enhancements can include confidence scoring and predictive models.”

---

## Backup talking points (if asked)
- Why rule-based first? → Fast, interpretable, low deployment risk.
- Why multiple causes per order? → Real incidents are multi-factor.
- What’s next? → ML ranking, anomaly alerts, SLA breach prediction.
