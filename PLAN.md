# Delivery Failure Root-Cause Analysis System - Implementation Plan

## 📋 Project Overview

**Problem**: Delivery failures and delays are major drivers of customer dissatisfaction, but current systems only report *how many* failed, not *why*. Operations teams manually investigate across siloed systems (orders, fleet, warehouse, feedback, external factors), making the process reactive and error-prone.

**Solution**: Build an automated analytics system that aggregates multi-domain data, correlates events automatically, generates human-readable insights, and surfaces actionable recommendations.

---

## 🎯 Solution Architecture

### Phase 1: Data Aggregation & Enrichment
- **Input**: 8 CSV files (orders, fleet_logs, warehouse_logs, external_factors, feedback, warehouses, drivers, clients)
- **Process**: 
  - Load and parse all CSV files with proper date/time handling
  - Merge related data using order_id as the primary key
  - Calculate derived metrics (delay hours, transit times, picking times, dispatch lag)
- **Output**: Single enriched DataFrame with all order-level attributes

### Phase 2: Feature Engineering
- **Temporal Features**: 
  - `delay_hours`: actual_delivery_date - promised_delivery_date
  - `transit_hours`: arrival_time - departure_time
  - `picking_minutes`: picking_end - picking_start
  - `dispatch_lag_minutes`: dispatch_time - picking_end
- **External Factors**:
  - Traffic severity score (Heavy=2, Moderate=1, Clear=0)
  - Weather conditions (Rain, Fog, Clear)
  - Event types (Strike, Holiday, etc.)
- **Feedback Analysis**:
  - Sentiment aggregation
  - Keyword extraction (late, delay, address, stock, cancel, etc.)
  - Rating averages

### Phase 3: Root Cause Inference
- **Rule-based cause detection** per order:
  - Stockout: failure_reason contains "stock"
  - Warehouse delay: picking_minutes > 30 or notes contain "slow"
  - Dispatch lag: dispatch_lag_minutes > 45
  - Traffic: traffic_score >= 1 or notes contain "congestion"
  - Weather: weather_condition in {Rain, Fog}
  - Events: event_type is not empty
  - Address issues: notes contain "address"
  - Vehicle issues: notes contain "breakdown"
  - Late delivery: delay_hours > 0
  - Communication gaps: feedback mentions "no update"

### Phase 4: Aggregation & Insights
- **Filtering**: By city, client, warehouse, date range
- **Metrics**:
  - Total orders analyzed
  - Late/failed rate (%)
  - Top 5 causes with counts
  - Sample impacted order IDs
- **Recommendations**: Actionable steps mapped to each cause type

### Phase 5: Use Case Queries
1. City delays (yesterday/last week)
2. Client-specific failures
3. Warehouse performance analysis
4. City comparisons
5. Peak period forecasting
6. Onboarding risk assessment

---

## 🛠️ Implementation Steps

### Step 1: Environment Setup
1. Install Python 3.8+ (see Python Installation Guide below)
2. Create virtual environment (recommended)
3. Install dependencies from `requirements.txt`

### Step 2: Data Preparation
- Ensure CSV files are in `third-assignment-sample-data-set/` directory
- Verify data integrity (check for missing files)

### Step 3: Run Analytics Script
```bash
python3 analyze_deliveries.py
```

### Step 4: Generate Outputs
- Console output → Save to text file
- Create Word document with write-up + outputs
- Record demo video with voice narration
- Document sample use case results

### Step 5: Package Deliverables
- GitHub repository link
- Documentation folder (Word doc + recording)
- Sample outputs document

---

## 🐍 Python Installation Guide

### For macOS (Your System)

#### Option 1: Using Homebrew (Recommended)
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3

# Verify installation
python3 --version
```

#### Option 2: Using Official Python Installer
1. Visit https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 for macOS
3. Run the installer (.pkg file)
4. **Important**: Check "Add Python to PATH" during installation
5. Verify: Open Terminal and run `python3 --version`

#### Option 3: Using pyenv (For Multiple Python Versions)
```bash
# Install pyenv
brew install pyenv

# Install Python 3.11
pyenv install 3.11.7

# Set as global version
pyenv global 3.11.7

# Add to shell profile
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Verify
python3 --version
```

### Verify Python Installation
```bash
python3 --version
# Should show: Python 3.8.x or higher

which python3
# Should show: /usr/local/bin/python3 or similar
```

---

## 📦 Dependency Installation

### Step 1: Navigate to Project Directory
```bash
cd /Users/monika/projects/ai_assignemnts
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

### Step 3: Install Dependencies
```bash
# Upgrade pip first
python3 -m pip install --upgrade pip

# Install all required packages
python3 -m pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python3 -c "import pandas, numpy, matplotlib, seaborn; print('All packages installed successfully!')"
```

### If Installation Fails
- **Permission errors**: Use `--user` flag: `python3 -m pip install --user -r requirements.txt`
- **Network issues**: Check internet connection or use `--no-cache-dir` flag
- **SSL errors**: Update certificates or use `--trusted-host` flags

---

## 🚀 Running the Demo

### Basic Run (All Use Cases)
```bash
cd /Users/monika/projects/ai_assignemnts
python3 analyze_deliveries.py
```

### Custom Filters (Optional)
The script supports command-line arguments (if implemented):
```bash
# City-specific analysis
python3 analyze_deliveries.py --city "Bengaluru"

# Client-specific analysis
python3 analyze_deliveries.py --client "Saini LLC" --start-date 2025-08-01 --end-date 2025-08-31

# Warehouse analysis
python3 analyze_deliveries.py --warehouse "Warehouse 8" --start-date 2025-08-01 --end-date 2025-08-31
```

### Save Output to File
```bash
python3 analyze_deliveries.py > demo_outputs.txt 2>&1
```

---

## 📊 Expected Outputs

### Sample Use Case 1: City Delays
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

### Sample Use Case 2: Client Failures
```
Scope: Client X failures last 7 days (example: Saini LLC)
Orders analyzed: 456
Late/failed rate: 22.1%
Top causes:
- stockout: 67
- dispatch_lag: 34
- late_delivery: 23
...
```

---

## 📝 Deliverables Checklist

- [x] Solution write-up document (Word format)
- [x] Sample program (`analyze_deliveries.py`)
- [ ] Demo video with voice explanation
- [ ] Sample use case outputs document
- [ ] GitHub repository link
- [ ] Email with deliverables

---

## 🎬 Demo Recording Guide

### Preparation
1. Ensure all dependencies are installed
2. Test script runs successfully
3. Prepare script/narration outline

### Recording Steps
1. **Introduction** (30 seconds)
   - Explain the business problem
   - Show the data files available

2. **Run Use Case 1** (1 minute)
   - "Why were deliveries delayed in Bengaluru yesterday?"
   - Run script, show output
   - Explain top causes and recommendations

3. **Run Use Case 2** (1 minute)
   - "Why did Client X's orders fail last week?"
   - Show filtered results

4. **Run Use Case 3** (1 minute)
   - "Warehouse B August issues"
   - Explain warehouse-specific insights

5. **Run Use Case 4** (1 minute)
   - "Compare City A vs City B"
   - Show comparative analysis

6. **Run Use Case 5** (1 minute)
   - "Festival period outlook"
   - Explain peak period risks

7. **Run Use Case 6** (1 minute)
   - "Onboarding Client Y risk model"
   - Show projected risks and mitigation

8. **Conclusion** (30 seconds)
   - Summarize key insights
   - Explain next steps

**Total Duration**: ~7-8 minutes

---

## 🔧 Troubleshooting

### Issue: ModuleNotFoundError
**Solution**: Install missing package
```bash
python3 -m pip install <package_name>
```

### Issue: Permission Denied
**Solution**: Use virtual environment or `--user` flag
```bash
python3 -m pip install --user <package_name>
```

### Issue: Python Not Found
**Solution**: Use `python3` instead of `python`, or create alias
```bash
alias python=python3
```

### Issue: Data File Not Found
**Solution**: Check data directory path
```bash
ls third-assignment-sample-data-set/
```

---

## 📚 Next Steps

1. ✅ Complete Python installation
2. ✅ Install dependencies
3. ✅ Run demo script
4. ⏳ Record demo video
5. ⏳ Create Word document
6. ⏳ Document sample outputs
7. ⏳ Package and email deliverables

---

## 📧 Contact & Support

For issues or questions:
- Check Python version: `python3 --version`
- Check installed packages: `python3 -m pip list`
- Review error messages carefully
- Ensure data files are in correct location




