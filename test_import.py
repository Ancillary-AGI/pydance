#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

try:
    import pydance
    print("✅ pydance imported successfully")
    from pydance.server.application import Application
    print("✅ Application imported successfully")
    from pydance.http.request import Request
    print("✅ Request imported successfully")
    from pydance.routing.router import Router
    print("✅ Router imported successfully")
    print("✅ All core modules import successfully!")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
