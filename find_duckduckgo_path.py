#!/usr/bin/env python3
"""
Diagnostic script to find DuckDuckGo browser history path on Windows.
"""

import os
from pathlib import Path

def find_duckduckgo_paths():
    """Find all possible DuckDuckGo history file locations."""
    print("=" * 80)
    print("DUCKDUCKGO BROWSER PATH FINDER (WINDOWS)")
    print("=" * 80)

    if os.name != 'nt':
        print("⚠️  This script is designed for Windows only.")
        return

    home = Path.home()

    # Possible DuckDuckGo paths on Windows
    possible_paths = [
        # Standard Chromium structure
        home / "AppData" / "Local" / "DuckDuckGo" / "User Data" / "Default" / "History",

        # Alternative locations
        home / "AppData" / "Roaming" / "DuckDuckGo" / "User Data" / "Default" / "History",
        home / "AppData" / "Local" / "DuckDuckGo Browser" / "User Data" / "Default" / "History",
        home / "AppData" / "Local" / "DuckDuckGo" / "Default" / "History",
    ]

    print(f"\nChecking {len(possible_paths)} possible DuckDuckGo locations...\n")

    found_paths = []

    for path in possible_paths:
        exists = path.exists()
        is_file = path.is_file() if exists else False

        status = "✅ FOUND (FILE)" if is_file else "📁 FOUND (DIR)" if exists else "❌ Not found"

        print(f"{status}: {path}")

        if is_file:
            found_paths.append(path)
            # Get file size
            size = path.stat().st_size
            print(f"         Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")

    print("\n" + "=" * 80)

    if found_paths:
        print(f"\n✅ Found {len(found_paths)} DuckDuckGo history database(s):")
        for path in found_paths:
            print(f"   {path}")

        print("\n📝 The correct path in mcp_server.py is:")
        rel_path = found_paths[0].relative_to(home)
        parts = ' / '.join([f'"{p}"' for p in rel_path.parts])
        print(f'   Path.home() / {parts}')
    else:
        print("\n❌ No DuckDuckGo history databases found.")
        print("\nPossible reasons:")
        print("  1. DuckDuckGo browser is not installed")
        print("  2. DuckDuckGo has never been run (no history yet)")
        print("  3. DuckDuckGo is installed in a custom location")

        # Check if DuckDuckGo directory exists at all
        duckduckgo_dirs = [
            home / "AppData" / "Local" / "DuckDuckGo",
            home / "AppData" / "Roaming" / "DuckDuckGo",
        ]

        print("\nChecking DuckDuckGo installation directories:")
        for ddg_dir in duckduckgo_dirs:
            if ddg_dir.exists():
                print(f"\n✅ Found: {ddg_dir}")
                print("   Contents:")
                for item in ddg_dir.iterdir():
                    print(f"     - {item.name}")
                    if item.is_dir():
                        # Check for History file
                        for subitem in item.rglob("History"):
                            if subitem.is_file():
                                print(f"       └─ HISTORY FILE: {subitem}")
            else:
                print(f"❌ Not found: {ddg_dir}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    find_duckduckgo_paths()
