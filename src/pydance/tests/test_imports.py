#!/usr/bin/env python3
"""
Simple test to check imports
"""

try:
    print("Testing basic imports...")
    
    # Test config import
    from pydance.config import AppConfig
    print("✓ AppConfig imported successfully")
    
    # Test application import without db
    from pydance.server.application import Application
    print("✓ Application imported successfully")
    
    # Test if we can create an application
    app = Application()
    print("✓ Application created successfully")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()