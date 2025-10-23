#!/usr/bin/env python3
"""
Follow .lnk shortcuts to find actual browser installation locations.
"""

import os
import sys
from pathlib import Path

def follow_shortcut(lnk_path):
    """Follow a .lnk shortcut to find the target."""
    try:
        # Use PowerShell to read the shortcut
        import subprocess
        ps_command = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{lnk_path}")
        Write-Output $Shortcut.TargetPath
        '''

        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            check=True
        )

        target = result.stdout.strip()
        return Path(target) if target else None
    except Exception as e:
        print(f"Error reading shortcut: {e}")
        return None


def find_browser_data_from_exe(exe_path):
    """Given a browser .exe, try to find its User Data directory."""
    if not exe_path or not Path(exe_path).exists():
        return None

    exe_path = Path(exe_path)

    # Common patterns for browser data locations relative to .exe
    possible_data_locations = [
        # Same directory as exe
        exe_path.parent / "User Data" / "Default" / "History",

        # Parent directory
        exe_path.parent.parent / "User Data" / "Default" / "History",

        # AppData Local (even for portable)
        Path.home() / "AppData" / "Local" / exe_path.parent.name / "User Data" / "Default" / "History",
    ]

    for location in possible_data_locations:
        if location.exists() and location.is_file():
            return location

    return None


def main():
    """Follow shortcuts and find browser history."""
    print("=" * 80)
    print("FOLLOWING BROWSER SHORTCUTS")
    print("=" * 80)

    if os.name != 'nt':
        print("⚠️  This script is designed for Windows only.")
        return

    desktop = Path.home() / "Desktop"

    shortcuts = {
        'Arc': desktop / "Arc.lnk",
        'DuckDuckGo': desktop / "DuckDuckGo.lnk",
    }

    results = {}

    for browser_name, shortcut_path in shortcuts.items():
        print(f"\n{'=' * 80}")
        print(f"🔍 {browser_name}")
        print('=' * 80)

        if not shortcut_path.exists():
            print(f"❌ Shortcut not found: {shortcut_path}")
            continue

        print(f"✅ Found shortcut: {shortcut_path}")

        # Follow the shortcut
        target = follow_shortcut(str(shortcut_path))

        if not target:
            print("❌ Could not read shortcut target")
            continue

        print(f"📍 Target: {target}")

        if not target.exists():
            print("⚠️  Target does not exist")
            continue

        # Try to find the History file
        history_path = find_browser_data_from_exe(target)

        if history_path:
            print(f"✅ Found History file: {history_path}")
            size = history_path.stat().st_size / 1024 / 1024
            print(f"   Size: {size:.2f} MB")
            results[browser_name] = history_path
        else:
            print(f"❌ Could not find History file for {browser_name}")
            print(f"\n   Searching around {target.parent}...")

            # Manual search around the exe location
            search_dirs = [target.parent, target.parent.parent]
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue

                try:
                    for item in search_dir.rglob("History"):
                        if item.is_file() and "User Data" in str(item):
                            print(f"   ✅ Found: {item}")
                            size = item.stat().st_size / 1024 / 1024
                            print(f"      Size: {size:.2f} MB")
                            results[browser_name] = item
                            break
                except:
                    pass

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if results:
        print(f"\n✅ Found {len(results)} browser history file(s):\n")

        for browser_name, history_path in results.items():
            print(f"{browser_name}:")
            print(f"  {history_path}\n")

        print("\n" + "=" * 80)
        print("COPY THESE PATHS")
        print("=" * 80)
        print("\nPaste these exact paths in your response:\n")

        for browser_name, history_path in results.items():
            print(f"{browser_name}: {history_path}")
    else:
        print("\n❌ No browser history files found.")
        print("\n💡 Try these steps:")
        print("   1. Open Arc browser and visit a few websites")
        print("   2. Open DuckDuckGo browser and visit a few websites")
        print("   3. Run this script again")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
