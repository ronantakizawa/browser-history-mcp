#!/usr/bin/env python3
"""
Test script for Windows - verifies browser path detection on Windows OS.
Run this on your Windows device to verify all browser paths are correct.
"""

import os
import sys
from pathlib import Path

def test_os_detection():
    """Test that Windows OS is detected correctly."""
    print("=" * 60)
    print("Testing OS Detection")
    print("=" * 60)
    print(f"os.name: {os.name}")
    print(f"Expected: nt")

    if os.name == 'nt':
        print("✅ Windows detected correctly!\n")
        return True
    else:
        print("❌ Not running on Windows!\n")
        return False


def test_browser_paths():
    """Test browser path detection for all supported browsers."""
    print("=" * 60)
    print("Testing Browser Path Detection")
    print("=" * 60)

    try:
        from mcp_server import get_history_db_path
    except ImportError as e:
        print(f"❌ Error importing mcp_server: {e}")
        print("Make sure mcp_server.py is in the same directory.")
        return False

    browsers = ['brave', 'chrome', 'edge', 'firefox', 'opera']
    results = []

    for browser in browsers:
        try:
            path = get_history_db_path(browser)
            exists = path.exists()

            print(f"\n{browser.upper()}:")
            print(f"  Path: {path}")
            print(f"  Exists: {'✅ Yes' if exists else '⚠️  No (browser not installed or no history)'}")

            # Verify it's a Windows path
            if str(path).startswith('C:\\Users\\'):
                print(f"  Format: ✅ Valid Windows path")
                results.append((browser, True))
            else:
                print(f"  Format: ❌ Invalid Windows path")
                results.append((browser, False))

        except FileNotFoundError as e:
            print(f"\n{browser.upper()}:")
            print(f"  ⚠️  {e}")
            results.append((browser, True))  # Expected for Firefox if no profile
        except Exception as e:
            print(f"\n{browser.upper()}:")
            print(f"  ❌ Error: {e}")
            results.append((browser, False))

    print("\n" + "=" * 60)
    return all(result[1] for result in results)


def test_macos_only_browsers():
    """Test that macOS-only browsers raise appropriate errors on Windows."""
    print("=" * 60)
    print("Testing macOS-Only Browser Restrictions")
    print("=" * 60)

    try:
        from mcp_server import get_history_db_path
    except ImportError:
        return False

    macos_browsers = ['safari', 'arc', 'duckduckgo']
    results = []

    for browser in macos_browsers:
        try:
            path = get_history_db_path(browser)
            print(f"\n{browser.upper()}:")
            print(f"  ❌ Should have raised ValueError but got: {path}")
            results.append(False)
        except ValueError as e:
            print(f"\n{browser.upper()}:")
            print(f"  ✅ Correctly raised error: {e}")
            results.append(True)
        except Exception as e:
            print(f"\n{browser.upper()}:")
            print(f"  ❌ Unexpected error: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    return all(results)


def test_expected_paths():
    """Verify the exact expected paths for Windows."""
    print("=" * 60)
    print("Verifying Expected Windows Path Formats")
    print("=" * 60)

    try:
        from mcp_server import get_history_db_path
    except ImportError:
        return False

    username = Path.home().name
    expected_paths = {
        'brave': f'C:\\Users\\{username}\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\History',
        'chrome': f'C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History',
        'edge': f'C:\\Users\\{username}\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History',
        'opera': f'C:\\Users\\{username}\\AppData\\Roaming\\Opera Software\\Opera Stable\\History',
    }

    results = []
    for browser, expected in expected_paths.items():
        actual = str(get_history_db_path(browser))
        match = actual == expected

        print(f"\n{browser.upper()}:")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print(f"  Match:    {'✅ Yes' if match else '❌ No'}")
        results.append(match)

    print("\n" + "=" * 60)
    return all(results)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("WINDOWS BROWSER PATH DETECTION TEST SUITE")
    print("=" * 60 + "\n")

    # Check if running on Windows
    if not test_os_detection():
        print("\n❌ This test script must be run on Windows!")
        sys.exit(1)

    print()

    # Run all tests
    tests = [
        ("Browser Path Detection", test_browser_paths),
        ("macOS-Only Browser Restrictions", test_macos_only_browsers),
        ("Expected Path Formats", test_expected_paths),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
        print()

    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED! Windows support is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! Review the output above.")
    print("=" * 60 + "\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
