#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing pydance core imports (excluding optional dependencies)...")

try:
    # Test main package import
    import pydance
    print("✅ Main pydance package imported successfully")

    # Test core modules that should work without optional deps
    from pydance.core.management.base import BaseCommand
    print("✅ Management commands imported successfully")

    from pydance.utils.logging import get_logger
    print("✅ Logging utilities imported successfully")

    from pydance.core.exceptions import HTTPException
    print("✅ Core exceptions imported successfully")

    from pydance.routing import Router
    print("✅ Routing imported successfully")

    from pydance.middleware.manager import MiddlewareManager
    print("✅ Middleware manager imported successfully")

    print("\n🎉 Core imports successful! No unresolved symbols in core modules.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()
