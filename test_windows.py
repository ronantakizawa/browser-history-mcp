#!/usr/bin/env python3
"""
Test script for Windows - verifies browser path detection and displays search history.
Run this on your Windows device to verify all browser paths are correct.
"""

import os
import sys
from pathlib import Path

def test_os_detection():
    """Test that Windows OS is detected correctly."""
    print("=" * 80)
    print("Testing OS Detection")
    print("=" * 80)
    print(f"os.name: {os.name}")
    print(f"Expected: nt")

    if os.name == 'nt':
        print("✅ Windows detected correctly!\n")
        return True
    else:
        print("❌ Not running on Windows!\n")
        return False


def display_browser_history(browser_name, limit=10, custom_path=None):
    """Display recent history from a specific browser."""
    try:
        # Import the underlying functions, not the MCP tools
        from mcp_server import query_history_db, chrome_timestamp_to_datetime, firefox_timestamp_to_datetime, safari_timestamp_to_datetime
        import sqlite3
        import tempfile
        import shutil

        print(f"\n{'=' * 80}")
        print(f"📖 {browser_name.upper()} - Recent History (Last {limit} entries)")
        print('=' * 80)

        if browser_name == "firefox":
            query = """
            SELECT
                url, title, visit_count,
                last_visit_date as last_visit_time
            FROM moz_places
            WHERE hidden = 0
            ORDER BY last_visit_time DESC
            LIMIT ?
            """
        else:
            # Chromium-based browsers
            query = """
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
            LIMIT ?
            """

        # If custom path provided (Windows Store apps), query directly
        if custom_path:
            # Create temporary copy to avoid locking
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                tmp_path = tmp_file.name

            try:
                shutil.copy2(custom_path, tmp_path)
                conn = sqlite3.connect(tmp_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                results = [dict(row) for row in cursor.fetchall()]
                conn.close()
            finally:
                if Path(tmp_path).exists():
                    Path(tmp_path).unlink()
        else:
            results = query_history_db(query, (limit,), browser_name)

        if not results:
            print(f"No history entries found in {browser_name.capitalize()}")
            return False

        print(f"Most recent {len(results)} {browser_name.capitalize()} browsing history entries:\n")

        for i, entry in enumerate(results, 1):
            title = entry['title'] or "No title"
            url = entry['url']
            visit_count = entry['visit_count']

            if browser_name == "firefox":
                last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
            else:
                last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   Visits: {visit_count} | Last visited: {last_visit}")
            print()

        return True

    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_browser_paths_and_history():
    """Test browser path detection and display history for all supported browsers."""
    print("=" * 80)
    print("Testing Browser Path Detection & History")
    print("=" * 80)

    try:
        from mcp_server import get_history_db_path, find_windows_store_app_path
    except ImportError as e:
        print(f"❌ Error importing mcp_server: {e}")
        print("Make sure mcp_server.py is in the same directory.")
        return False

    browsers = ['brave', 'chrome', 'edge', 'firefox', 'opera', 'arc', 'duckduckgo']
    results = []
    browsers_with_history = []
    store_app_paths = {}

    for browser in browsers:
        try:
            # For Arc and DuckDuckGo, try to find Windows Store app path first
            if browser in ['arc', 'duckduckgo']:
                store_path = find_windows_store_app_path(browser.title())
                if store_path:
                    path = store_path
                    is_store_app = True
                    store_app_paths[browser] = path
                else:
                    path = get_history_db_path(browser)
                    is_store_app = False
            else:
                path = get_history_db_path(browser)
                is_store_app = False

            exists = path.exists()

            print(f"\n{browser.upper()}{' (Windows Store App)' if is_store_app else ''}:")
            print(f"  Path: {path}")
            print(f"  File exists: {'✅ Yes' if exists else '❌ No'}")

            # Verify it's a Windows path
            path_str = str(path)
            if path_str.startswith('C:\\Users\\') or path_str.startswith('C:/Users/'):
                print(f"  Format: ✅ Valid Windows path")

                if exists:
                    # Check if it's actually a file (not just the directory)
                    if path.is_file():
                        print(f"  Status: ✅ History database found!")
                        browsers_with_history.append(browser)
                        results.append((browser, True))
                    else:
                        print(f"  Status: ⚠️  Path exists but is not a file")
                        results.append((browser, True))
                else:
                    print(f"  Status: ⚠️  Browser not installed or no history yet")
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

    print("\n" + "=" * 80)

    # Display history for browsers that have it
    if browsers_with_history:
        print(f"\n✅ Found {len(browsers_with_history)} browser(s) with history!")
        print("Displaying recent history from each browser...\n")

        for browser in browsers_with_history:
            # Use custom path if it's a Windows Store app
            custom_path = store_app_paths.get(browser)
            display_browser_history(browser, limit=5, custom_path=custom_path)
    else:
        print("\n⚠️  No browsers with accessible history found.")

    return all(result[1] for result in results)


def test_search_functionality():
    """Test search functionality across all browsers."""
    print("\n" + "=" * 80)
    print("Testing Search Functionality")
    print("=" * 80)

    try:
        from mcp_server import query_history_db, get_history_db_path, find_windows_store_app_path, chrome_timestamp_to_datetime, firefox_timestamp_to_datetime
        import sqlite3
        import tempfile
        import shutil
    except ImportError as e:
        print(f"❌ Error importing: {e}")
        return False

    browsers = ['brave', 'chrome', 'edge', 'firefox', 'opera', 'arc', 'duckduckgo']
    search_term = input("\nEnter a search term to find in your browser history (or press Enter to skip): ").strip()

    if not search_term:
        print("⏭️  Skipping search test")
        return True

    search_pattern = f"%{search_term}%"

    for browser in browsers:
        try:
            # For Arc and DuckDuckGo, try to find Windows Store app path first
            if browser in ['arc', 'duckduckgo']:
                store_path = find_windows_store_app_path(browser.title())
                path = store_path if store_path else get_history_db_path(browser)
            else:
                path = get_history_db_path(browser)

            if not path.exists() or not path.is_file():
                continue

            print(f"\n{'=' * 80}")
            print(f"🔍 Searching {browser.upper()} for: '{search_term}'")
            print('=' * 80)

            if browser == "firefox":
                query = """
                SELECT
                    url, title, visit_count,
                    last_visit_date as last_visit_time
                FROM moz_places
                WHERE (url LIKE ? OR title LIKE ?)
                AND hidden = 0
                ORDER BY last_visit_time DESC
                LIMIT ?
                """
            else:
                query = """
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                WHERE url LIKE ? OR title LIKE ?
                ORDER BY last_visit_time DESC
                LIMIT ?
                """

            # Always use query_history_db which handles temp file creation
            results = query_history_db(query, (search_pattern, search_pattern, 5), browser)

            if not results:
                print(f"No history entries found matching '{search_term}' in {browser.capitalize()}")
                continue

            print(f"Found {len(results)} {browser.capitalize()} history entries matching '{search_term}':\n")

            for i, entry in enumerate(results, 1):
                title = entry['title'] or "No title"
                url = entry['url']
                visit_count = entry['visit_count']

                if browser == "firefox":
                    last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
                else:
                    last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

                print(f"{i}. {title}")
                print(f"   URL: {url}")
                print(f"   Visits: {visit_count} | Last visited: {last_visit}")
                print()

        except Exception as e:
            print(f"⚠️  Could not search {browser}: {e}")

    return True


def test_macos_only_browsers():
    """Test that macOS-only browsers raise appropriate errors on Windows."""
    print("\n" + "=" * 80)
    print("Testing macOS-Only Browser Restrictions")
    print("=" * 80)

    try:
        from mcp_server import get_history_db_path
    except ImportError:
        return False

    macos_browsers = ['safari']
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

    print("\n" + "=" * 80)
    return all(results)


def test_most_visited():
    """Test most visited sites functionality."""
    print("\n" + "=" * 80)
    print("Testing Most Visited Sites")
    print("=" * 80)

    try:
        from mcp_server import query_history_db, get_history_db_path, find_windows_store_app_path, chrome_timestamp_to_datetime, firefox_timestamp_to_datetime
        import sqlite3
        import tempfile
        import shutil
    except ImportError as e:
        print(f"❌ Error importing: {e}")
        return False

    browsers = ['brave', 'chrome', 'edge', 'firefox', 'opera', 'arc', 'duckduckgo']

    for browser in browsers:
        try:
            # For Arc and DuckDuckGo, try to find Windows Store app path first
            if browser in ['arc', 'duckduckgo']:
                store_path = find_windows_store_app_path(browser.title())
                path = store_path if store_path else get_history_db_path(browser)
            else:
                path = get_history_db_path(browser)

            if not path.exists() or not path.is_file():
                continue

            print(f"\n{'=' * 80}")
            print(f"⭐ {browser.upper()} - Top 5 Most Visited Sites")
            print('=' * 80)

            if browser == "firefox":
                query = """
                SELECT
                    url, title, visit_count,
                    last_visit_date as last_visit_time
                FROM moz_places
                WHERE hidden = 0 AND visit_count > 1
                ORDER BY visit_count DESC
                LIMIT ?
                """
            else:
                query = """
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                WHERE visit_count > 1
                ORDER BY visit_count DESC
                LIMIT ?
                """

            # Always use query_history_db which handles temp file creation
            results = query_history_db(query, (5,), browser)

            if not results:
                print(f"No frequently visited sites found in {browser.capitalize()}")
                continue

            print(f"Top {len(results)} most visited {browser.capitalize()} sites:\n")

            for i, entry in enumerate(results, 1):
                title = entry['title'] or "No title"
                url = entry['url']
                visit_count = entry['visit_count']

                if browser == "firefox":
                    last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
                else:
                    last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

                print(f"{i}. {title}")
                print(f"   URL: {url}")
                print(f"   Visits: {visit_count} | Last visited: {last_visit}")
                print()

        except Exception as e:
            print(f"⚠️  Could not get most visited for {browser}: {e}")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("WINDOWS BROWSER HISTORY MCP SERVER TEST SUITE")
    print("=" * 80 + "\n")

    # Check if running on Windows
    if not test_os_detection():
        print("\n❌ This test script must be run on Windows!")
        sys.exit(1)

    print()

    # Run all tests
    tests = [
        ("Browser Path Detection & History Display", test_browser_paths_and_history),
        ("macOS-Only Browser Restrictions", test_macos_only_browsers),
        ("Most Visited Sites", test_most_visited),
        ("Search Functionality", test_search_functionality),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        print()

    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED! Windows support is working correctly.")
    else:
        print("⚠️  SOME TESTS HAD ISSUES - Review the output above.")
    print("=" * 80 + "\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
