#!/usr/bin/env python3
"""
Script to fix all logging.getLogger instances in Pydance codebase
"""
import os
import re
from pathlib import Path

def fix_logging_in_file(filepath):
    """Fix logging imports and usage in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Skip the logging.py file itself
        if 'utils/logging.py' in str(filepath):
            return False

        # Skip if already has pydance logging import
        if 'from pydance.utils.logging import get_logger' in content:
            return False

        # Check if file uses logging.getLogger
        if 'logging.getLogger' not in content:
            return False

        # Add pydance logging import
        lines = content.split('\n')
        import_added = False

        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('import logging') or line.startswith('from logging'):
                # Add pydance import after logging import
                lines.insert(i + 1, 'from pydance.utils.logging import get_logger')
                import_added = True
                break
            elif line.startswith('import ') or line.startswith('from '):
                continue
            elif line and not line.startswith('#'):
                # First non-import, non-comment line - add import here
                lines.insert(i, 'from pydance.utils.logging import get_logger')
                lines.insert(i, '')  # Add blank line
                import_added = True
                break

        if not import_added:
            # Add at the beginning if no imports found
            lines.insert(0, 'from pydance.utils.logging import get_logger')
            lines.insert(1, '')

        # Replace logging.getLogger calls
        content = '\n'.join(lines)

        # Replace logger = logging.getLogger(__name__)
        content = re.sub(r'logger\s*=\s*logging\.getLogger\(__name__\)', 'logger = get_logger(__name__)', content)

        # Replace other logging.getLogger calls
        content = re.sub(r'logging\.getLogger\(([^)]+)\)', r'get_logger(\1)', content)

        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

    return False

def main():
    """Main function to fix logging in all files"""
    pydance_dir = Path('src/pydance')
    fixed_count = 0

    print("Scanning for files that need logging fixes...")

    for py_file in pydance_dir.rglob('*.py'):
        if fix_logging_in_file(py_file):
            print(f"Fixed: {py_file}")
            fixed_count += 1

    print(f"\nCompleted! Fixed logging in {fixed_count} files.")

if __name__ == '__main__':
    main()
