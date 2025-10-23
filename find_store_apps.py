#!/usr/bin/env python3
"""
Find browser data for Windows Store/MSIX installed applications.
Windows Store apps store data in different locations.
"""

import os
from pathlib import Path

def find_store_app_data():
    """Find Windows Store app data locations."""
    print("=" * 80)
    print("FINDING WINDOWS STORE BROWSER DATA")
    print("=" * 80)

    if os.name != 'nt':
        print("⚠️  This script is designed for Windows only.")
        return

    home = Path.home()

    # Windows Store apps can store data in several locations
    possible_locations = [
        # AppData\Local\Packages (Windows Store apps)
        home / "AppData" / "Local" / "Packages",

        # Standard locations (in case they also use these)
        home / "AppData" / "Local" / "Arc",
        home / "AppData" / "Local" / "DuckDuckGo",
        home / "AppData" / "Roaming" / "Arc",
        home / "AppData" / "Roaming" / "DuckDuckGo",
    ]

    print("\n🔍 Searching for Arc and DuckDuckGo data...\n")

    found_browsers = {}

    # Search Packages directory for Store apps
    packages_dir = home / "AppData" / "Local" / "Packages"
    if packages_dir.exists():
        print(f"📁 Checking Windows Store packages...")

        try:
            # Look for Arc and DuckDuckGo package folders
            for package in packages_dir.iterdir():
                package_name_lower = package.name.lower()

                browser_name = None
                if 'arc' in package_name_lower:
                    browser_name = 'Arc'
                elif 'duck' in package_name_lower:
                    browser_name = 'DuckDuckGo'

                if browser_name:
                    print(f"\n   ✅ Found {browser_name} package: {package.name}")

                    # Search for History file in this package
                    try:
                        for history_file in package.rglob("History"):
                            if history_file.is_file():
                                size = history_file.stat().st_size / 1024 / 1024
                                print(f"      📖 History file: {history_file}")
                                print(f"         Size: {size:.2f} MB")

                                if browser_name not in found_browsers:
                                    found_browsers[browser_name] = []
                                found_browsers[browser_name].append(history_file)
                    except Exception as e:
                        print(f"      ⚠️  Error searching: {e}")

        except Exception as e:
            print(f"   ❌ Error accessing Packages: {e}")

    # Also check standard locations
    for location in possible_locations[1:]:
        if location.exists():
            browser_name = location.name
            print(f"\n📁 Checking: {location}")

            try:
                for history_file in location.rglob("History"):
                    if history_file.is_file():
                        size = history_file.stat().st_size / 1024 / 1024
                        print(f"   ✅ Found History: {history_file}")
                        print(f"      Size: {size:.2f} MB")

                        if browser_name not in found_browsers:
                            found_browsers[browser_name] = []
                        found_browsers[browser_name].append(history_file)
            except Exception as e:
                print(f"   ⚠️  Error: {e}")

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if found_browsers:
        print(f"\n✅ Found browser data for: {', '.join(found_browsers.keys())}\n")

        for browser, paths in found_browsers.items():
            print(f"\n{browser}:")
            print("-" * 80)
            for i, path in enumerate(paths, 1):
                print(f"\n{i}. {path}")
                try:
                    size = path.stat().st_size / 1024 / 1024
                    print(f"   Size: {size:.2f} MB")
                except:
                    pass

        print("\n" + "=" * 80)
        print("COPY THESE PATHS")
        print("=" * 80)
        print("\nShare these paths with me:\n")

        for browser, paths in found_browsers.items():
            # Use the first (usually only) path
            print(f"{browser}: {paths[0]}")

    else:
        print("\n❌ No browser History files found.")
        print("\n💡 TROUBLESHOOTING:")
        print("   1. Open Arc browser and browse some websites")
        print("   2. Open DuckDuckGo browser and browse some websites")
        print("   3. Close both browsers completely")
        print("   4. Run this script again")
        print("\n   Or check if the browsers are actually installed:")
        print("   - Look in Start Menu for Arc")
        print("   - Look in Start Menu for DuckDuckGo")

    print("\n" + "=" * 80)

    # Additional check - list what's actually in Packages
    print("\n📦 INSTALLED STORE APPS (matching Arc or Duck):")
    print("=" * 80)
    if packages_dir.exists():
        try:
            matching = [p.name for p in packages_dir.iterdir()
                       if 'arc' in p.name.lower() or 'duck' in p.name.lower()]
            if matching:
                for name in matching:
                    print(f"   • {name}")
            else:
                print("   None found - browsers may not be Windows Store versions")
        except:
            print("   Error listing packages")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    find_store_app_data()
