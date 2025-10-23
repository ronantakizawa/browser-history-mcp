#!/usr/bin/env python3
"""
Quick explorer to see what's actually installed in AppData.
"""

import os
from pathlib import Path

def explore_appdata():
    """List all directories in AppData/Local and AppData/Roaming."""
    print("=" * 80)
    print("EXPLORING AppData DIRECTORIES")
    print("=" * 80)

    if os.name != 'nt':
        print("⚠️  This script is designed for Windows only.")
        return

    home = Path.home()

    locations = [
        ("AppData\\Local", home / "AppData" / "Local"),
        ("AppData\\Roaming", home / "AppData" / "Roaming"),
    ]

    for name, path in locations:
        print(f"\n📁 {name}")
        print("=" * 80)

        if not path.exists():
            print("   ❌ Directory not found")
            continue

        # Look for browser-related directories
        browser_keywords = ['arc', 'duck', 'brave', 'chrome', 'edge', 'opera', 'firefox', 'mozilla', 'browser']

        try:
            all_dirs = sorted([d for d in path.iterdir() if d.is_dir()])
            browser_dirs = [d for d in all_dirs if any(keyword in d.name.lower() for keyword in browser_keywords)]

            if browser_dirs:
                print("\n   🌐 Browser-related directories:")
                for d in browser_dirs:
                    print(f"      • {d.name}")

                    # Check for User Data or Default subdirectories
                    try:
                        subdirs = list(d.iterdir())[:20]
                        for subdir in subdirs:
                            if subdir.is_dir() and subdir.name in ['User Data', 'Default', 'Profiles']:
                                print(f"        └─ {subdir.name}/")
                                # Check for History file
                                if (subdir / "Default" / "History").exists():
                                    print(f"           └─ Default/History ✅")
                                elif (subdir / "History").exists():
                                    print(f"           └─ History ✅")
                    except:
                        pass
            else:
                print("   No browser directories found")

            # Also show total count
            print(f"\n   Total directories: {len(all_dirs)}")
            print(f"   (Showing browser-related only)")

        except PermissionError:
            print("   ❌ Permission denied")

    print("\n" + "=" * 80)
    print("\n💡 TIP: Look for directories with 'Arc' or 'DuckDuckGo' in the name above.")
    print("   Then manually check for: DirectoryName/User Data/Default/History")
    print("=" * 80)


if __name__ == "__main__":
    explore_appdata()
