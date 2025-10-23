#!/usr/bin/env python3
"""
Comprehensive diagnostic for DuckDuckGo database issues on Windows.
Checks: path detection, permissions, schema, encryption.
"""

import os
import sqlite3
import tempfile
import shutil
from pathlib import Path

def diagnose_duckduckgo():
    """Run comprehensive diagnostics on DuckDuckGo database."""
    print("=" * 80)
    print("DUCKDUCKGO COMPREHENSIVE DIAGNOSTICS")
    print("=" * 80)

    # Step 1: Path Detection
    print("\n[STEP 1] PATH DETECTION")
    print("-" * 80)

    try:
        from mcp_server import find_windows_store_app_path, get_history_db_path

        # Try Windows Store version
        print("\n🔍 Searching for Windows Store version...")
        store_path = find_windows_store_app_path("DuckDuckGo")

        if store_path:
            print(f"✅ Found Windows Store path: {store_path}")
            db_path = store_path
        else:
            print("⚠️  Windows Store version not found")
            print("\n🔍 Trying standard installation path...")
            db_path = get_history_db_path("duckduckgo")
            print(f"📁 Standard path: {db_path}")

        # Step 2: File Existence & Permissions
        print(f"\n[STEP 2] FILE EXISTENCE & PERMISSIONS")
        print("-" * 80)

        if not db_path.exists():
            print(f"❌ File does not exist: {db_path}")
            print("\n💡 TROUBLESHOOTING:")
            print("   1. Make sure DuckDuckGo browser is installed")
            print("   2. Open DuckDuckGo and browse some websites")
            print("   3. Close DuckDuckGo completely")
            print("   4. Run this script again")
            return

        print(f"✅ File exists: {db_path}")

        # Check file size
        size = db_path.stat().st_size
        print(f"📏 File size: {size:,} bytes ({size/1024/1024:.2f} MB)")

        if size == 0:
            print("❌ File is empty!")
            return

        # Check read permissions
        if os.access(db_path, os.R_OK):
            print("✅ File is readable")
        else:
            print("❌ File is NOT readable (permission issue)")
            print("\n💡 Try running this script as Administrator")
            return

        # Step 3: Database Schema Check
        print(f"\n[STEP 3] DATABASE SCHEMA CHECK")
        print("-" * 80)

        # Create temp copy to avoid locking
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_path = tmp_file.name

        try:
            print(f"📋 Creating temporary copy...")
            shutil.copy2(db_path, tmp_path)
            print(f"✅ Temporary copy created")

            # Try to open as SQLite database
            print(f"\n🔓 Opening database...")
            try:
                conn = sqlite3.connect(tmp_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                print("✅ Successfully opened as SQLite database")
            except sqlite3.DatabaseError as e:
                print(f"❌ Cannot open as SQLite database: {e}")
                print("\n💡 The database might be:")
                print("   1. Encrypted (requires decryption key)")
                print("   2. Corrupted")
                print("   3. In use by DuckDuckGo (close the browser)")
                return

            # List all tables
            print(f"\n📊 Database tables:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()

            if not tables:
                print("⚠️  No tables found (empty database)")
                return

            for table in tables:
                print(f"   - {table['name']}")

            # Check if 'urls' table exists (Chromium schema)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='urls'")
            has_urls = cursor.fetchone()

            if has_urls:
                print("\n✅ Found 'urls' table (Chromium schema)")

                # Get schema of urls table
                print("\n📋 'urls' table schema:")
                cursor.execute("PRAGMA table_info(urls)")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")

                # Count rows
                cursor.execute("SELECT COUNT(*) as count FROM urls")
                count = cursor.fetchone()['count']
                print(f"\n📊 Total rows in 'urls' table: {count}")

                if count == 0:
                    print("\n⚠️  The database is empty!")
                    print("\n💡 SOLUTION:")
                    print("   1. Open DuckDuckGo browser")
                    print("   2. Browse to several different websites")
                    print("   3. Close DuckDuckGo")
                    print("   4. Run this script again")
                else:
                    # Sample some URLs
                    print(f"\n📖 Sample URLs (up to 10):")
                    cursor.execute("""
                        SELECT url, title, visit_count
                        FROM urls
                        ORDER BY last_visit_time DESC
                        LIMIT 10
                    """)

                    rows = cursor.fetchall()
                    for i, row in enumerate(rows, 1):
                        url = row['url']
                        title = row['title'] or "(no title)"
                        visits = row['visit_count']

                        # Truncate long URLs
                        display_url = url if len(url) <= 60 else url[:57] + "..."

                        is_internal = "🏠" if "static.ddg.local" in url else "🌐"
                        print(f"\n   {i}. {is_internal} {display_url}")
                        print(f"      Title: {title}")
                        print(f"      Visits: {visits}")

                    # Count internal vs external
                    cursor.execute("SELECT COUNT(*) as count FROM urls WHERE url LIKE 'https://static.ddg.local/%'")
                    internal_count = cursor.fetchone()['count']

                    cursor.execute("SELECT COUNT(*) as count FROM urls WHERE url NOT LIKE 'https://static.ddg.local/%'")
                    external_count = cursor.fetchone()['count']

                    print(f"\n📊 URL breakdown:")
                    print(f"   🏠 Internal pages: {internal_count}")
                    print(f"   🌐 External websites: {external_count}")

                    if external_count == 0:
                        print(f"\n⚠️  NO EXTERNAL WEBSITES FOUND!")
                        print(f"\n💡 This means you haven't visited any real websites yet.")
                        print(f"   Only internal DuckDuckGo pages are in the history.")
            else:
                print("\n❌ 'urls' table not found!")
                print("\n💡 This database has a different schema.")
                print("   It might be the macOS encrypted version or corrupted.")

                # Check for encrypted schema
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ZHISTORYENTRYMANAGEDOBJECT'")
                has_encrypted = cursor.fetchone()

                if has_encrypted:
                    print("\n🔐 Found encrypted macOS schema!")
                    print("   This is unexpected on Windows.")
                else:
                    print(f"\n📋 Available tables: {[t['name'] for t in tables]}")

            conn.close()

        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
                print(f"\n🗑️  Cleaned up temporary file")

        print("\n" + "=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)

    except ImportError as e:
        print(f"❌ Error importing mcp_server: {e}")
        print("Make sure mcp_server.py is in the same directory")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_duckduckgo()
