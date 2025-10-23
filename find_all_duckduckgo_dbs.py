#!/usr/bin/env python3
"""
Find ALL database files in DuckDuckGo package directory and check each one.
"""

import sqlite3
import tempfile
import shutil
from pathlib import Path

def check_database(db_path):
    """Check a database file for browsing history."""
    try:
        # Create temp copy
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_path = tmp_file.name

        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check if it has urls table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='urls'")
            has_urls = cursor.fetchone()

            if has_urls:
                # Count URLs
                cursor.execute("SELECT COUNT(*) as count FROM urls")
                total = cursor.fetchone()['count']

                # Count external URLs
                cursor.execute("SELECT COUNT(*) as count FROM urls WHERE url NOT LIKE 'https://static.ddg.local/%'")
                external = cursor.fetchone()['count']

                return total, external, True

            conn.close()
            return 0, 0, False

        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except Exception:
        return None, None, False


def find_all_duckduckgo_dbs():
    """Find all DuckDuckGo database files."""
    print("=" * 80)
    print("SEARCHING FOR ALL DUCKDUCKGO DATABASE FILES")
    print("=" * 80)

    # DuckDuckGo package directory
    package_base = Path.home() / "AppData" / "Local" / "Packages"

    if not package_base.exists():
        print(f"❌ Packages directory not found: {package_base}")
        return

    print(f"\n📁 Searching in: {package_base}\n")

    # Find DuckDuckGo package
    duckduckgo_packages = []
    for package in package_base.iterdir():
        if "duckduckgo" in package.name.lower():
            duckduckgo_packages.append(package)

    if not duckduckgo_packages:
        print("❌ No DuckDuckGo packages found!")
        return

    for package_dir in duckduckgo_packages:
        print(f"{'=' * 80}")
        print(f"📦 Package: {package_dir.name}")
        print('=' * 80)

        # Find all files named "History" or ending in .db/.sqlite
        print(f"\n🔍 Searching for database files...\n")

        db_files = []

        # Find "History" files
        for history_file in package_dir.rglob("History"):
            if history_file.is_file():
                db_files.append(history_file)

        # Find .db and .sqlite files
        for db_file in package_dir.rglob("*.db"):
            if db_file.is_file():
                db_files.append(db_file)

        for sqlite_file in package_dir.rglob("*.sqlite"):
            if sqlite_file.is_file():
                db_files.append(sqlite_file)

        # Remove duplicates
        db_files = list(set(db_files))

        if not db_files:
            print("⚠️  No database files found in this package")
            continue

        print(f"📊 Found {len(db_files)} database file(s):\n")

        for db_file in sorted(db_files):
            size = db_file.stat().st_size
            relative_path = db_file.relative_to(package_dir)

            print(f"\n{'─' * 80}")
            print(f"📄 {relative_path}")
            print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")

            # Check if it's a SQLite database with urls table
            total, external, has_urls_table = check_database(db_file)

            if has_urls_table:
                if external > 0:
                    print(f"   ✅ HAS BROWSING HISTORY!")
                    print(f"   📊 Total URLs: {total}")
                    print(f"   🌐 External websites: {external}")
                    print(f"   🏠 Internal pages: {total - external}")
                    print(f"\n   🎯 THIS IS LIKELY THE CORRECT DATABASE!")
                    print(f"   Full path: {db_file}")
                else:
                    print(f"   ⚠️  Has urls table but no external URLs")
                    print(f"   📊 Total URLs: {total} (all internal)")
            else:
                # Try to identify what kind of database it is
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                        tmp_path = tmp_file.name
                    try:
                        shutil.copy2(db_file, tmp_path)
                        conn = sqlite3.connect(tmp_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
                        tables = [row[0] for row in cursor.fetchall()]
                        conn.close()

                        if tables:
                            print(f"   📋 Tables: {', '.join(tables[:3])}")
                            if len(tables) > 3:
                                print(f"      (and {len(tables) - 3} more...)")
                        else:
                            print(f"   ⚠️  No tables (not a SQLite database or empty)")
                    finally:
                        if Path(tmp_path).exists():
                            Path(tmp_path).unlink()
                except:
                    print(f"   ⚠️  Cannot read as SQLite database")

        print(f"\n{'=' * 80}\n")

    print("\n" + "=" * 80)
    print("SEARCH COMPLETE")
    print("=" * 80)
    print("\nℹ️  If you found a database with external URLs, update mcp_server.py")
    print("   to use that path instead of the current one.")


if __name__ == "__main__":
    find_all_duckduckgo_dbs()
