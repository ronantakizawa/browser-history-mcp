#!/usr/bin/env python3
"""
Diagnostic script to find Opera browser history path on Windows.
Opera can be installed in different locations depending on version.
"""

import os
from pathlib import Path

def find_opera_paths():
    """Find all possible Opera history file locations."""
    print("=" * 80)
    print("OPERA BROWSER PATH FINDER")
    print("=" * 80)

    if os.name != 'nt':
        print("⚠️  This script is designed for Windows only.")
        return

    home = Path.home()

    # Possible Opera paths on Windows
    possible_paths = [
        # Opera Stable (standard)
        home / "AppData" / "Roaming" / "Opera Software" / "Opera Stable" / "History",

        # Opera GX
        home / "AppData" / "Roaming" / "Opera Software" / "Opera GX Stable" / "History",

        # Opera with User Data structure (like Chrome)
        home / "AppData" / "Roaming" / "Opera Software" / "Opera Stable" / "User Data" / "Default" / "History",
        home / "AppData" / "Roaming" / "Opera Software" / "Opera GX Stable" / "User Data" / "Default" / "History",

        # Local AppData (some versions)
        home / "AppData" / "Local" / "Opera Software" / "Opera Stable" / "History",
        home / "AppData" / "Local" / "Opera Software" / "Opera GX Stable" / "History",
        home / "AppData" / "Local" / "Opera Software" / "Opera Stable" / "User Data" / "Default" / "History",
        home / "AppData" / "Local" / "Opera Software" / "Opera GX Stable" / "User Data" / "Default" / "History",
    ]

    print(f"\nChecking {len(possible_paths)} possible Opera locations...\n")

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
        print(f"\n✅ Found {len(found_paths)} Opera history database(s):")
        for path in found_paths:
            print(f"   {path}")

        print("\n📝 Update mcp_server.py line ~155 to use:")
        print(f'   history_path = Path.home() / "{found_paths[0].relative_to(home)}"')
    else:
        print("\n❌ No Opera history databases found.")
        print("\nPossible reasons:")
        print("  1. Opera is not installed")
        print("  2. Opera has never been run (no history yet)")
        print("  3. Opera is installed in a custom location")

        # Check if Opera directory exists at all
        opera_dirs = [
            home / "AppData" / "Roaming" / "Opera Software",
            home / "AppData" / "Local" / "Opera Software",
        ]

        print("\nChecking Opera installation directories:")
        for opera_dir in opera_dirs:
            if opera_dir.exists():
                print(f"\n✅ Found: {opera_dir}")
                print("   Contents:")
                for item in opera_dir.iterdir():
                    print(f"     - {item.name}")
                    if item.is_dir():
                        # Check for History file
                        for subitem in item.rglob("History"):
                            if subitem.is_file():
                                print(f"       └─ HISTORY FILE: {subitem}")
            else:
                print(f"❌ Not found: {opera_dir}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    find_opera_paths()
