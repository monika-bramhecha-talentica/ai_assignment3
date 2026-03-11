# Delivery Failure Root-Cause Analysis System

## 📁 Project Structure

```
ai_assignemnts/
├── analyze_deliveries.py          # Main analytics script
├── test_setup.py                  # Environment verification script
├── requirements.txt               # Python dependencies
├── PLAN.md                        # Detailed implementation plan
├── QUICK_START.md                 # Quick setup guide
├── README.md                      # This file
├── docs/
│   └── solution_writeup.md        # Solution documentation
└── third-assignment-sample-data-set/
    ├── orders.csv
    ├── fleet_logs.csv
    ├── warehouse_logs.csv
    ├── external_factors.csv
    ├── feedback.csv
    ├── warehouses.csv
    ├── drivers.csv
    └── clients.csv
```

## 🚀 Quick Start

### 1. Install Python (if not already installed)
See `QUICK_START.md` for detailed instructions.

**Quick method:**
```bash
brew install python3
# OR download from https://www.python.org/downloads/
```

### 2. Install Dependencies
```bash
cd /Users/monika/projects/ai_assignemnts
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 3. Test Setup
```bash
python3 test_setup.py
```

### 4. Run Demo
```bash
python3 analyze_deliveries.py
```

## 📋 What This System Does

1. **Aggregates Multi-Domain Data**
   - Orders, fleet logs, warehouse operations, external factors, customer feedback
   - Links all data using order_id as primary key

2. **Correlates Events Automatically**
   - Identifies root causes: stockouts, traffic, weather, warehouse delays, address issues, etc.
   - Calculates delay metrics and performance indicators

3. **Generates Human-Readable Insights**
   - Narrative explanations instead of raw dashboards
   - Top causes with counts and percentages
   - Sample impacted orders

4. **Surfaces Actionable Recommendations**
   - Specific actions for each root cause type
   - Operational playbook suggestions

## 🎯 Sample Use Cases Covered

1. **City Delays**: Why were deliveries delayed in city X yesterday?
2. **Client Failures**: Why did Client X's orders fail in the past week?
3. **Warehouse Analysis**: Top reasons for delivery failures linked to Warehouse B in August
4. **City Comparison**: Compare delivery failure causes between City A and City B
5. **Peak Period**: Likely causes during festival period and preparation strategies
6. **Onboarding Risk**: Expected failure risks for new client with 20k monthly orders

## 📊 Output Format

The script prints structured insights like:

```
Scope: City delayed yesterday (example: Bengaluru)
Orders analyzed: 1,234
Late/failed rate: 15.3%
Top causes:
- traffic: 45
- warehouse_delay: 32
- address_issue: 28
Recommendations:
- traffic: Dynamic routing and slot re-allocation during congestion.
- warehouse_delay: Staff up or re-slot fast movers; monitor pick-pack SLA.
Sample impacted order_ids: [1234, 5678, 9012, ...]
```

## 📝 Deliverables

- ✅ Solution write-up (`docs/solution_writeup.md`)
- ✅ Sample program (`analyze_deliveries.py`)
- ⏳ Demo video (to be recorded)
- ⏳ Sample outputs document (to be generated)
- ⏳ GitHub repository link (to be shared)

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'numpy'"
```bash
python3 -m pip install -r requirements.txt
```

### "Permission denied"
```bash
python3 -m pip install --user -r requirements.txt
```

### "Python not found"
- Use `python3` instead of `python`
- Or install Python (see `QUICK_START.md`)

## 📚 Documentation

- **PLAN.md**: Complete implementation plan and architecture
- **QUICK_START.md**: Step-by-step Python installation guide
- **docs/solution_writeup.md**: Business solution documentation

## 🎬 Next Steps

1. ✅ Install Python and dependencies
2. ✅ Run `test_setup.py` to verify environment
3. ✅ Run `analyze_deliveries.py` to see results
4. ⏳ Save outputs: `python3 analyze_deliveries.py > outputs.txt`
5. ⏳ Record demo video with voice narration
6. ⏳ Create Word document with write-up + outputs
7. ⏳ Package deliverables and email

## 💡 Tips

- Always activate virtual environment: `source venv/bin/activate`
- Save outputs to file: `python3 analyze_deliveries.py > outputs.txt`
- Use `test_setup.py` to diagnose issues quickly

---

**Ready to start?** Follow `QUICK_START.md` for Python installation, then run `test_setup.py` to verify everything works!




