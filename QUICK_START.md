# Quick Start Guide - Python Installation & Setup

## 🚀 Fast Track Setup (5 minutes)

### Step 1: Check if Python is Already Installed
```bash
python3 --version
```

If you see `Python 3.8.x` or higher, **skip to Step 3**.

### Step 2: Install Python (Choose ONE method)

#### Method A: Homebrew (Easiest for macOS)
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3

# Verify
python3 --version
```

#### Method B: Official Installer (Simple GUI)
1. Go to: https://www.python.org/downloads/
2. Click "Download Python 3.12.x" (or latest)
3. Open the downloaded `.pkg` file
4. **IMPORTANT**: Check ✅ "Add Python to PATH"
5. Click "Install Now"
6. Verify in Terminal: `python3 --version`

### Step 3: Install Project Dependencies
```bash
# Navigate to project
cd /Users/monika/projects/ai_assignemnts

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install packages
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### Step 4: Verify Everything Works
```bash
# Test imports
python3 -c "import pandas; import numpy; print('✅ All packages installed!')"

# Run the demo
python3 analyze_deliveries.py
```

---

## 🐛 Common Issues & Fixes

### "python3: command not found"
- **Fix**: Install Python using Method A or B above
- **Alternative**: Try `python` instead of `python3`

### "ModuleNotFoundError: No module named 'numpy'"
- **Fix**: Run `python3 -m pip install -r requirements.txt`
- **If permission error**: Use `python3 -m pip install --user -r requirements.txt`

### "Permission denied" during pip install
- **Fix 1**: Use virtual environment (Step 3 above)
- **Fix 2**: Use `--user` flag: `python3 -m pip install --user <package>`
- **Fix 3**: Use `sudo` (not recommended): `sudo python3 -m pip install <package>`

### "SSL Certificate Error"
- **Fix**: Update certificates or use:
  ```bash
  python3 -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
  ```

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] Virtual environment created and activated
- [ ] All packages installed (`python3 -m pip list` shows pandas, numpy, etc.)
- [ ] Script runs without errors (`python3 analyze_deliveries.py`)
- [ ] Output shows analysis results

---

## 📋 What Gets Installed

From `requirements.txt`:
- **pandas** (2.2.2) - Data manipulation and analysis
- **numpy** (1.26.4) - Numerical computing
- **python-docx** (1.1.2) - Word document generation
- **matplotlib** (3.8.4) - Plotting (optional for this demo)
- **seaborn** (0.13.2) - Statistical visualization (optional)

---

## 🎯 Next Steps After Setup

1. Run the demo: `python3 analyze_deliveries.py`
2. Review outputs in console
3. Save outputs: `python3 analyze_deliveries.py > outputs.txt`
4. Record demo video
5. Create Word document with results

---

## 💡 Pro Tips

- **Always use virtual environments** to avoid conflicts with system Python
- **Activate venv** before running scripts: `source venv/bin/activate`
- **Deactivate venv** when done: `deactivate`
- **Keep pip updated**: `python3 -m pip install --upgrade pip`

---

## 📞 Still Having Issues?

1. Check Python version: `python3 --version` (need 3.8+)
2. Check pip: `python3 -m pip --version`
3. Check installed packages: `python3 -m pip list`
4. Check data files exist: `ls third-assignment-sample-data-set/`
5. Read full error message - it usually tells you what's missing!




