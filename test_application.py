#!/usr/bin/env python3
"""
Test script for Data Usage Monitor
Verifies basic functionality of the application
"""

import sqlite3
import os
import sys
import json
import subprocess
import time

def test_database():
    """Test database functionality"""
    print("Testing database...")
    
    db_path = "/home/ubuntu/data-usage-monitor/data_usage.db"
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM locations")
        location_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM daily_usage")
        usage_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Database test passed - {location_count} locations, {usage_count} usage records")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_backup_system():
    """Test backup functionality"""
    print("Testing backup system...")
    
    try:
        os.chdir("/home/ubuntu/data-usage-monitor")
        result = subprocess.run([
            "python3", "backup_manager.py", "--backup"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Backup system test passed")
            return True
        else:
            print(f"❌ Backup system test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Backup system test failed: {e}")
        return False

def test_flask_import():
    """Test Flask application imports"""
    print("Testing Flask application imports...")
    
    try:
        # Add virtual environment to path
        venv_path = "/home/ubuntu/data-usage-monitor/data-usage-api/venv/lib/python3.11/site-packages"
        if venv_path not in sys.path:
            sys.path.insert(0, venv_path)
        
        sys.path.insert(0, "/home/ubuntu/data-usage-monitor/data-usage-api/src")
        
        # Test importing main modules
        import main
        from routes import data_usage, dashboard, system
        
        print("✅ Flask import test passed")
        return True
        
    except Exception as e:
        print(f"❌ Flask import test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("Testing file structure...")
    
    required_files = [
        "/home/ubuntu/data-usage-monitor/database.py",
        "/home/ubuntu/data-usage-monitor/backup_manager.py",
        "/home/ubuntu/data-usage-monitor/setup.sh",
        "/home/ubuntu/data-usage-monitor/schema.sql",
        "/home/ubuntu/data-usage-monitor/DEPLOYMENT_GUIDE.md",
        "/home/ubuntu/data-usage-monitor/data-usage-api/src/main.py",
        "/home/ubuntu/data-usage-monitor/data-usage-api/src/static/index.html",
        "/home/ubuntu/data-usage-monitor/data-usage-api/src/static/styles.css",
        "/home/ubuntu/data-usage-monitor/data-usage-api/src/static/app.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ File structure test passed")
        return True

def main():
    """Run all tests"""
    print("Data Usage Monitor - Test Suite")
    print("=" * 40)
    
    tests = [
        test_file_structure,
        test_database,
        test_backup_system,
        test_flask_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Application is ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

