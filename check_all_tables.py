#!/usr/bin/env python3
"""
Check all tables in DuckDuckGo database to find where browsing history might be stored.
"""

import sqlite3
import tempfile
import shutil
from pathlib import Path

def check_all_tables():
    """Check all tables for browsing data."""
    print("=" * 80)
    print("CHECKING ALL DUCKDUCKGO TABLES FOR BROWSING HISTORY")
    print("=" * 80)

    try:
        from mcp_server import find_windows_store_app_path

        store_path = find_windows_store_app_path("DuckDuckGo")
        if not store_path or not store_path.exists():
            print("❌ Cannot find DuckDuckGo database")
            return

        print(f"\n📁 Database: {store_path}\n")

        # Create temp copy
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_path = tmp_file.name

        try:
            shutil.copy2(store_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check visits table (might contain the actual visit records)
            print("=" * 80)
            print("CHECKING 'visits' TABLE")
            print("=" * 80)

            cursor.execute("SELECT COUNT(*) as count FROM visits")
            visit_count = cursor.fetchone()['count']
            print(f"\n📊 Total rows in 'visits' table: {visit_count}")

            if visit_count > 0:
                # Get schema
                print("\n📋 'visits' table schema:")
                cursor.execute("PRAGMA table_info(visits)")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")

                # Sample visits
                print(f"\n📖 Sample visits (up to 20):")
                cursor.execute("""
                    SELECT *
                    FROM visits
                    ORDER BY visit_time DESC
                    LIMIT 20
                """)

                visits = cursor.fetchall()
                for i, visit in enumerate(visits, 1):
                    print(f"\n{i}. Visit ID: {visit['id']}")
                    for key in visit.keys():
                        if visit[key] is not None:
                            print(f"   {key}: {visit[key]}")

            # Check if visits are linked to urls
            print("\n" + "=" * 80)
            print("CHECKING URL-VISIT RELATIONSHIP")
            print("=" * 80)

            cursor.execute("""
                SELECT
                    urls.url,
                    urls.title,
                    urls.visit_count,
                    COUNT(visits.id) as actual_visits
                FROM urls
                LEFT JOIN visits ON visits.url = urls.id
                GROUP BY urls.id
                ORDER BY urls.last_visit_time DESC
            """)

            results = cursor.fetchall()
            print(f"\n📊 Found {len(results)} URLs with visit data:\n")

            for i, row in enumerate(results, 1):
                url = row['url']
                title = row['title'] or "(no title)"
                visit_count = row['visit_count']
                actual_visits = row['actual_visits']

                is_internal = "🏠" if "static.ddg.local" in url else "🌐"

                print(f"{i}. {is_internal} {title}")
                print(f"   URL: {url}")
                print(f"   Visit count (urls table): {visit_count}")
                print(f"   Actual visits (visits table): {actual_visits}")
                print()

            # Check edge_urls and edge_visits tables
            print("=" * 80)
            print("CHECKING EDGE TABLES")
            print("=" * 80)

            cursor.execute("SELECT COUNT(*) as count FROM edge_urls")
            edge_url_count = cursor.fetchone()['count']
            print(f"\n📊 edge_urls table: {edge_url_count} rows")

            cursor.execute("SELECT COUNT(*) as count FROM edge_visits")
            edge_visit_count = cursor.fetchone()['count']
            print(f"📊 edge_visits table: {edge_visit_count} rows")

            if edge_url_count > 0:
                print("\n📖 Sample from edge_urls:")
                cursor.execute("SELECT * FROM edge_urls LIMIT 10")
                for row in cursor.fetchall():
                    print(f"   {dict(row)}")

            # Check for URLs that might not be in 'urls' table
            print("\n" + "=" * 80)
            print("CHECKING FOR BROWSING DATA IN OTHER LOCATIONS")
            print("=" * 80)

            # Check visited_links
            cursor.execute("SELECT COUNT(*) as count FROM visited_links")
            visited_count = cursor.fetchone()['count']
            print(f"\n📊 visited_links table: {visited_count} rows")

            if visited_count > 0:
                cursor.execute("SELECT * FROM visited_links LIMIT 10")
                print("\n📖 Sample from visited_links:")
                for row in cursor.fetchall():
                    print(f"   {dict(row)}")

            # Check keyword_search_terms
            cursor.execute("SELECT COUNT(*) as count FROM keyword_search_terms")
            search_count = cursor.fetchone()['count']
            print(f"\n📊 keyword_search_terms table: {search_count} rows")

            if search_count > 0:
                cursor.execute("SELECT * FROM keyword_search_terms LIMIT 10")
                print("\n📖 Sample from keyword_search_terms:")
                for row in cursor.fetchall():
                    print(f"   {dict(row)}")

            conn.close()

        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_all_tables()
