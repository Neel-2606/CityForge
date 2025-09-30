#!/usr/bin/env python3
"""Data refresh utility for NASA satellite data."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import glob

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def clear_cached_data(data_type="all"):
    """Clear cached NASA data to force fresh downloads."""
    
    data_dir = Path("data/raw")
    if not data_dir.exists():
        print("No cached data found.")
        return
    
    files_removed = 0
    
    if data_type in ["all", "omi"]:
        # Remove OMI files
        omi_files = glob.glob(str(data_dir / "OMI-Aura_L2-*.he5"))
        for file in omi_files:
            os.remove(file)
            files_removed += 1
            print(f"🗑️  Removed: {Path(file).name}")
    
    if data_type in ["all", "modis"]:
        # Remove MODIS files
        modis_files = glob.glob(str(data_dir / "MOD11A1.*.hdf"))
        for file in modis_files:
            os.remove(file)
            files_removed += 1
            print(f"🗑️  Removed: {Path(file).name}")
    
    if data_type in ["all", "processed"]:
        # Remove processed files
        processed_files = glob.glob(str(data_dir / "*_processed.nc"))
        for file in processed_files:
            os.remove(file)
            files_removed += 1
            print(f"🗑️  Removed: {Path(file).name}")
    
    print(f"✅ Removed {files_removed} cached files. Next analysis will download fresh data.")

def check_data_age():
    """Check age of cached NASA data."""
    
    data_dir = Path("data/raw")
    if not data_dir.exists():
        print("No cached data found.")
        return
    
    print("📅 Cached Data Status:")
    print("-" * 40)
    
    # Check OMI files
    omi_files = glob.glob(str(data_dir / "OMI-Aura_L2-*.he5"))
    for file in omi_files:
        file_path = Path(file)
        age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
        status = "🟢 Fresh" if age.days < 1 else "🟡 Stale" if age.days < 7 else "🔴 Old"
        print(f"   🛰️  OMI: {file_path.name[:30]}... ({age.days}d old) {status}")
    
    # Check MODIS files
    modis_files = glob.glob(str(data_dir / "MOD11A1.*.hdf"))
    for file in modis_files:
        file_path = Path(file)
        age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
        status = "🟢 Fresh" if age.days < 1 else "🟡 Stale" if age.days < 7 else "🔴 Old"
        print(f"   🌡️  MODIS: {file_path.name[:30]}... ({age.days}d old) {status}")
    
    print("\n💡 Tip: Run 'python refresh_data.py clear' to force fresh downloads")

def main():
    """Main refresh utility."""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clear":
            data_type = sys.argv[2] if len(sys.argv) > 2 else "all"
            clear_cached_data(data_type)
        elif command == "status":
            check_data_age()
        else:
            print("Usage:")
            print("  python refresh_data.py status          # Check data age")
            print("  python refresh_data.py clear [type]    # Clear cached data")
            print("  Types: all, omi, modis, processed")
    else:
        check_data_age()

if __name__ == "__main__":
    main()
