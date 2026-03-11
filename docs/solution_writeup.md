## Delivery Failure Root-Cause System – Proposal & Demo Plan

### Business Challenge
- Fragmented signals across orders, fleet logs, warehouse ops, customer feedback, and external factors hides true drivers of delays/failures.
- Manual investigations slow recovery, obscure systemic bottlenecks, and leak revenue/customer trust.

### Data Available (sample set)
- Orders: promised vs actual delivery, status, failure reason.
- Fleet logs: GPS notes, transit times.
- Warehouse logs: picking/dispatch timestamps, notes.
- External factors: traffic/weather/event markers.
- Feedback: free text + sentiment/rating.
- Master data: clients, warehouses, drivers.

### Approach (implemented in `analyze_deliveries.py`)
1) **Ingest & unify** all CSVs; parse timestamps and normalize identifiers.
2) **Feature engineering**
   - Delivery delay vs promise (`delay_hours`, `is_late`).
   - Warehouse cycle times (`picking_minutes`, `dispatch_lag_minutes`).
   - Transit time + GPS notes.
   - External severity score (Heavy > Moderate > Clear), weather + events.
   - Feedback tag extraction (late/address/stock/comm).
3) **Cause inference** per order using heuristic rules on structured + text fields:
   - Stockouts, warehouse delay/dispatch lag, traffic, weather, events/strikes/holidays, address issues, vehicle issues, late delivery, communication gaps.
4) **Aggregation** by any slice (city, client, warehouse, date range) to surface:
   - Late/failed rate, top causes, sample affected orders, and mapped recommendations.
5) **Narrative outputs** (stdout) ready for recording/screen-share; can be piped to text/Docx.

### High-level flow (simplified)
```
CSV sources ──► Pandas ingestion ──► Derived features ──► Causes per order
                                              │
                                Filters (city/client/warehouse/date)
                                              │
                                   Aggregated insights + actions
```

### Running the demo locally
```bash
cd /Users/monika/projects/ai_assignemnts
python3 -m pip install -r requirements.txt
python3 analyze_deliveries.py
```
The script prints narrative answers for the sample use cases:
- City delays (yesterday): filter by `--city`.
- Client failures (past week): filter by `--client`, `--start-date`, `--end-date`.
- Warehouse-month view: `--warehouse` + date range.
- City A vs City B comparison (built-in demo).
- Festival period (Oct/Nov) stress test.
- Onboarding 20k orders risk outlook.

### How to capture outputs & artifacts
- **Word doc**: copy console output + this write-up into a `.docx` (or run `python3 analyze_deliveries.py > outputs.txt` then paste). Add the ASCII diagram above; optionally convert via `pandoc -o delivery-insights.docx outputs.txt`.
- **Recording**: run the script, narrate insights and recommendations while scrolling the console (QuickTime/OBS). Use the six sample questions as the script.
- **Email package**: share the repo link plus a folder containing the `.docx` and the recording.

### Operational recommendations (playbook excerpts)
- Stockouts: safety stock + substitution rules and proactive ETA updates.
- Warehouse delay: staffing by demand curve, pick-pack SLA alerts, re-slot fast movers.
- Traffic/weather/events: dynamic routing, buffer ETAs, upfront customer comms.
- Address issues: pre-ship validation, driver guidance, confirmability checks.
- Vehicle issues: preventive maintenance and standby capacity.
- Visibility/communication: automated customer updates and internal incident flags.





