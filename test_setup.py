#!/usr/bin/env python3
"""Quick test script to verify Python environment and dependencies are set up correctly."""

import sys

def test_python_version():
    """Check Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python version {version.major}.{version.minor} is too old. Need 3.8+")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro}")
    return True

def test_imports():
    """Test if all required packages can be imported."""
    packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'python-docx': 'docx',
    }
    
    failed = []
    for display_name, import_name in packages.items():
        try:
            __import__(import_name)
            print(f"✅ {display_name} imported successfully")
        except ImportError as e:
            print(f"❌ {display_name} not found: {e}")
            failed.append(display_name)
    
    return len(failed) == 0

def test_data_files():
    """Check if data files exist."""
    from pathlib import Path
    
    data_dir = Path(__file__).parent / "third-assignment-sample-data-set"
    required_files = [
        "orders.csv",
        "fleet_logs.csv",
        "warehouse_logs.csv",
        "external_factors.csv",
        "feedback.csv",
        "warehouses.csv",
        "drivers.csv",
        "clients.csv",
    ]
    
    missing = []
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            print(f"✅ {filename} found")
        else:
            print(f"❌ {filename} NOT FOUND at {filepath}")
            missing.append(filename)
    
    return len(missing) == 0

def main():
    print("=" * 60)
    print("Python Environment Test")
    print("=" * 60)
    print()
    
    all_passed = True
    
    print("1. Checking Python version...")
    if not test_python_version():
        all_passed = False
    print()
    
    print("2. Checking required packages...")
    if not test_imports():
        all_passed = False
        print("\n💡 To install missing packages, run:")
        print("   python3 -m pip install -r requirements.txt")
    print()
    
    print("3. Checking data files...")
    if not test_data_files():
        all_passed = False
        print("\n💡 Make sure data files are in 'third-assignment-sample-data-set/' directory")
    print()
    
    print("=" * 60)
    if all_passed:
        print("✅ All checks passed! You're ready to run analyze_deliveries.py")
        print("\nNext step: python3 analyze_deliveries.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    print("=" * 60)

if __name__ == "__main__":
    main()




