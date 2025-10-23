#!/usr/bin/env python3
"""
Debug script to see what's actually in the DuckDuckGo database on Windows.
Run this on your Windows device to see all URLs in the database.
"""

import sqlite3
import tempfile
import shutil
from pathlib import Path

def debug_duckduckgo():
    """Debug DuckDuckGo database contents."""
    print("=" * 80)
    print("DUCKDUCKGO DATABASE DEBUG")
    print("=" * 80)

    # Try to find DuckDuckGo History file
    from mcp_server import find_windows_store_app_path, get_history_db_path

    try:
        # Try Windows Store version first
        store_path = find_windows_store_app_path("DuckDuckGo")
        if store_path:
            db_path = store_path
            print(f"\n✅ Found Windows Store version: {db_path}")
        else:
            db_path = get_history_db_path("duckduckgo")
            print(f"\n📁 Using standard path: {db_path}")

        if not db_path.exists():
            print(f"❌ Database file does not exist!")
            return

        # Create temp copy
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_path = tmp_file.name

        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM urls")
            total = cursor.fetchone()['count']
            print(f"\n📊 Total URLs in database: {total}")

            # Get count of internal pages
            cursor.execute("SELECT COUNT(*) as count FROM urls WHERE url LIKE 'https://static.ddg.local/%'")
            internal = cursor.fetchone()['count']
            print(f"📊 Internal DuckDuckGo pages: {internal}")

            # Get count of external pages
            cursor.execute("SELECT COUNT(*) as count FROM urls WHERE url NOT LIKE 'https://static.ddg.local/%'")
            external = cursor.fetchone()['count']
            print(f"📊 External websites: {external}")

            # Show all URLs (limit to 20)
            print(f"\n{'=' * 80}")
            print("ALL URLs IN DATABASE (up to 20):")
            print('=' * 80)
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                ORDER BY last_visit_time DESC
                LIMIT 20
            """)

            results = cursor.fetchall()
            for i, row in enumerate(results, 1):
                url = row['url']
                title = row['title'] or "No title"
                visit_count = row['visit_count']

                # Mark internal vs external
                url_type = "🏠 Internal" if "static.ddg.local" in url else "🌐 External"

                print(f"\n{i}. {url_type}")
                print(f"   Title: {title}")
                print(f"   URL: {url}")
                print(f"   Visits: {visit_count}")

            # Show external URLs only
            print(f"\n{'=' * 80}")
            print("EXTERNAL URLS ONLY (up to 20):")
            print('=' * 80)
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                WHERE url NOT LIKE 'https://static.ddg.local/%'
                ORDER BY last_visit_time DESC
                LIMIT 20
            """)

            results = cursor.fetchall()
            if results:
                for i, row in enumerate(results, 1):
                    url = row['url']
                    title = row['title'] or "No title"
                    visit_count = row['visit_count']

                    print(f"\n{i}. {title}")
                    print(f"   URL: {url}")
                    print(f"   Visits: {visit_count}")
            else:
                print("\n⚠️  No external URLs found!")
                print("\n💡 This means:")
                print("   1. You haven't browsed any websites in DuckDuckGo yet, OR")
                print("   2. DuckDuckGo isn't storing history (check browser settings)")

            conn.close()

        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_duckduckgo()
