#!/usr/bin/env python3
"""
Comprehensive diagnostic script to find Arc and DuckDuckGo browser history paths on Windows.
Searches all possible locations recursively.
"""

import os
from pathlib import Path

def find_all_history_files():
    """Find ALL browser history files by searching common directories."""
    print("=" * 80)
    print("COMPREHENSIVE BROWSER HISTORY PATH FINDER (WINDOWS)")
    print("=" * 80)

    if os.name != 'nt':
        print("⚠️  This script is designed for Windows only.")
        return

    home = Path.home()

    # Search directories
    search_dirs = [
        home / "AppData" / "Local",
        home / "AppData" / "Roaming",
    ]

    print("\n🔍 Searching for ALL browser History files...")
    print("This may take a minute...\n")

    found_files = {}

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        print(f"Searching: {search_dir}")

        # Find all files named "History"
        try:
            for history_file in search_dir.rglob("History"):
                if history_file.is_file():
                    # Get size
                    try:
                        size = history_file.st_size
                        size_mb = size / 1024 / 1024

                        # Try to identify which browser
                        path_str = str(history_file)
                        browser_name = "Unknown"

                        if "Arc" in path_str:
                            browser_name = "Arc"
                        elif "DuckDuckGo" in path_str:
                            browser_name = "DuckDuckGo"
                        elif "Brave" in path_str:
                            browser_name = "Brave"
                        elif "Chrome" in path_str:
                            browser_name = "Chrome"
                        elif "Edge" in path_str:
                            browser_name = "Edge"
                        elif "Opera" in path_str:
                            browser_name = "Opera"

                        if browser_name not in found_files:
                            found_files[browser_name] = []

                        found_files[browser_name].append({
                            'path': history_file,
                            'size': size,
                            'size_mb': size_mb
                        })
                    except Exception as e:
                        pass
        except PermissionError:
            pass

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if not found_files:
        print("\n❌ No browser history files found!")
        print("\nPossible reasons:")
        print("  1. Browsers not installed")
        print("  2. Browsers never run (no history yet)")
        print("  3. Permission issues")
        return

    for browser_name, files in sorted(found_files.items()):
        print(f"\n{'=' * 80}")
        print(f"🌐 {browser_name.upper()} ({len(files)} file(s) found)")
        print('=' * 80)

        for i, file_info in enumerate(files, 1):
            path = file_info['path']
            size_mb = file_info['size_mb']

            print(f"\n{i}. {path}")
            print(f"   Size: {size_mb:.2f} MB")

            # Show relative path for code
            try:
                rel_path = path.relative_to(home)
                parts = ' / '.join([f'"{p}"' for p in rel_path.parts])
                print(f"   Code: Path.home() / {parts}")
            except:
                pass

    # Specific recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS FOR mcp_server.py")
    print("=" * 80)

    if "Arc" in found_files:
        arc_path = found_files["Arc"][0]['path']
        rel_path = arc_path.relative_to(home)
        parts = ' / '.join([f'"{p}"' for p in rel_path.parts])
        print(f"\n📝 Arc Browser:")
        print(f"   Update line ~154 to:")
        print(f'   history_path = Path.home() / {parts}')

    if "DuckDuckGo" in found_files:
        ddg_path = found_files["DuckDuckGo"][0]['path']
        rel_path = ddg_path.relative_to(home)
        parts = ' / '.join([f'"{p}"' for p in rel_path.parts])
        print(f"\n📝 DuckDuckGo Browser:")
        print(f"   Update line ~119 to:")
        print(f'   history_path = Path.home() / {parts}')

    if "Arc" not in found_files:
        print("\n⚠️  Arc Browser:")
        print("   No Arc History file found")
        print("   Check if Arc is installed at:")
        arc_dirs = [
            home / "AppData" / "Local" / "Arc",
            home / "AppData" / "Roaming" / "Arc",
        ]
        for arc_dir in arc_dirs:
            if arc_dir.exists():
                print(f"\n   ✅ Found directory: {arc_dir}")
                print("      Contents:")
                try:
                    for item in sorted(arc_dir.iterdir())[:10]:
                        print(f"        - {item.name}")
                except:
                    pass

    if "DuckDuckGo" not in found_files:
        print("\n⚠️  DuckDuckGo Browser:")
        print("   No DuckDuckGo History file found")
        print("   Check if DuckDuckGo is installed at:")
        ddg_dirs = [
            home / "AppData" / "Local" / "DuckDuckGo",
            home / "AppData" / "Roaming" / "DuckDuckGo",
        ]
        for ddg_dir in ddg_dirs:
            if ddg_dir.exists():
                print(f"\n   ✅ Found directory: {ddg_dir}")
                print("      Contents:")
                try:
                    for item in sorted(ddg_dir.iterdir())[:10]:
                        print(f"        - {item.name}")
                        if item.is_dir():
                            print(f"        └─ Contents of {item.name}:")
                            for subitem in sorted(item.iterdir())[:10]:
                                print(f"           - {subitem.name}")
                except:
                    pass

    print("\n" + "=" * 80)


if __name__ == "__main__":
    find_all_history_files()
