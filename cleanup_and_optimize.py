#!/usr/bin/env python3
"""Clean up temporary files and optimize the system for production."""

import os
import shutil
from pathlib import Path

def cleanup_system():
    """Clean up temporary files and optimize for production."""
    print("🧹 CLEANING UP AND OPTIMIZING SYSTEM...")
    print("=" * 50)
    
    # Remove debug/test files
    debug_files = [
        "debug_nasa_data.py",
        "check_permissions.py", 
        "fix_real_data.py",
        "final_fix.py",
        "test_earthaccess.py"
    ]
    
    for file in debug_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️  Removed debug file: {file}")
    
    # Clean up test data directory
    test_dir = Path("data/raw/test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("🗑️  Removed test data directory")
    
    # Organize real data files
    raw_dir = Path("data/raw")
    if raw_dir.exists():
        modis_files = list(raw_dir.glob("MOD11A1*.hdf"))
        print(f"📁 Found {len(modis_files)} real MODIS files:")
        for file in modis_files:
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   ✅ {file.name} ({size_mb:.2f} MB)")
    
    # Create production directories
    prod_dirs = [
        "data/processed/real",
        "data/cache/nasa", 
        "logs",
        "exports"
    ]
    
    for dir_path in prod_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Created production directory: {dir_path}")
    
    print("\n✅ System cleanup and optimization complete!")
    print("🚀 Ready for production deployment!")

if __name__ == "__main__":
    cleanup_system()
