#!/usr/bin/env python3
"""
Find browser installations in non-standard locations (Desktop, Downloads, etc.)
"""

import os
from pathlib import Path

def search_directory_for_browsers(directory, max_depth=3):
    """Search a directory for browser History files."""
    found = []

    def search_recursive(path, current_depth=0):
        if current_depth > max_depth:
            return

        try:
            for item in path.iterdir():
                if item.is_file() and item.name == "History":
                    # Found a History file
                    found.append(item)
                elif item.is_dir():
                    # Check if directory name suggests it's a browser
                    dir_lower = item.name.lower()
                    if any(keyword in dir_lower for keyword in ['arc', 'duck', 'brave', 'chrome', 'browser', 'opera', 'firefox']):
                        search_recursive(item, current_depth + 1)
                    elif item.name in ['User Data', 'Default', 'Profiles']:
                        search_recursive(item, current_depth + 1)
                    elif current_depth < 2:  # Only go deeper for first 2 levels
                        search_recursive(item, current_depth + 1)
        except (PermissionError, OSError):
            pass

    search_recursive(directory)
    return found


def find_desktop_browsers():
    """Find browsers installed in Desktop or other non-standard locations."""
    print("=" * 80)
    print("SEARCHING FOR BROWSERS IN NON-STANDARD LOCATIONS")
    print("=" * 80)

    if os.name != 'nt':
        print("⚠️  This script is designed for Windows only.")
        return

    home = Path.home()

    # Search locations
    search_locations = [
        ("Desktop", home / "Desktop"),
        ("Downloads", home / "Downloads"),
        ("Documents", home / "Documents"),
        ("OneDrive Desktop", home / "OneDrive" / "Desktop"),
    ]

    all_found = {}

    for name, location in search_locations:
        if not location.exists():
            continue

        print(f"\n🔍 Searching: {name}")
        print(f"   Path: {location}")
        print("   Please wait...")

        history_files = search_directory_for_browsers(location)

        if history_files:
            print(f"   ✅ Found {len(history_files)} History file(s)")
            all_found[name] = history_files
        else:
            print(f"   ❌ No History files found")

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if not all_found:
        print("\n❌ No browser History files found in searched locations.")
        print("\n💡 TIPS:")
        print("   1. Check where Arc and DuckDuckGo are actually installed")
        print("   2. Look for .exe files in Desktop folder")
        print("   3. Right-click the browser shortcut → 'Open file location'")
        return

    for location_name, files in all_found.items():
        print(f"\n📁 {location_name}")
        print("=" * 80)

        for i, file_path in enumerate(files, 1):
            # Try to identify browser
            path_str = str(file_path).lower()
            browser = "Unknown"
            if "arc" in path_str:
                browser = "Arc"
            elif "duck" in path_str:
                browser = "DuckDuckGo"
            elif "brave" in path_str:
                browser = "Brave"
            elif "chrome" in path_str:
                browser = "Chrome"
            elif "opera" in path_str:
                browser = "Opera"

            print(f"\n{i}. {browser}")
            print(f"   Full path: {file_path}")

            try:
                size = file_path.stat().st_size / 1024 / 1024
                print(f"   Size: {size:.2f} MB")
            except:
                pass

            # Show how to use this path
            print(f"\n   🔧 To use this in mcp_server.py:")
            print(f'   path = Path(r"{file_path}")')

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n⚠️  IMPORTANT: Portable browser installations are NOT supported by the MCP server.")
    print("\nThe MCP server is designed for standard browser installations because:")
    print("  1. It uses Path.home() which assumes standard AppData locations")
    print("  2. Portable installations have different paths for each user")
    print("  3. The paths would be hardcoded and not portable")
    print("\n💡 SOLUTIONS:")
    print("  1. Install Arc/DuckDuckGo normally (standard installation)")
    print("  2. Or manually edit the test script to use absolute paths")
    print("  3. Or use the browsers that ARE in standard locations (Brave, Chrome, etc.)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    find_desktop_browsers()
