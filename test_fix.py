#!/usr/bin/env python3
"""
Quick test to verify the DuckDuckGo path fix works.
"""

from mcp_server import find_windows_store_app_path, query_history_db

print("=" * 80)
print("TESTING DUCKDUCKGO PATH FIX")
print("=" * 80)

# Test path detection
print("\n[STEP 1] Finding DuckDuckGo path...")
path = find_windows_store_app_path("DuckDuckGo")

if path:
    print(f"✅ Found path: {path}")

    # Check if it's the correct one (not internalEnvironment)
    if "internalEnvironment" in str(path):
        print("❌ ERROR: Found internal environment path (wrong one!)")
    else:
        print("✅ Correct path (not internal environment)")

    # Test if file exists
    if path.exists():
        print(f"✅ File exists")
        print(f"   Size: {path.stat().st_size:,} bytes")
    else:
        print(f"❌ File does not exist")

    # Try to query it
    print("\n[STEP 2] Testing query...")
    try:
        query = """
        SELECT url, title, visit_count
        FROM urls
        WHERE url NOT LIKE 'https://static.ddg.local/%'
        ORDER BY last_visit_time DESC
        LIMIT 5
        """

        results = query_history_db(query, (5,), "duckduckgo")

        if results:
            print(f"✅ Successfully queried database!")
            print(f"   Found {len(results)} external URLs\n")

            for i, result in enumerate(results, 1):
                title = result.get('title', '(no title)')
                url = result.get('url', '')

                # Truncate long URLs
                display_url = url if len(url) <= 70 else url[:67] + "..."

                print(f"{i}. {title}")
                print(f"   {display_url}\n")

            print("=" * 80)
            print("✅ ✅ ✅ FIX SUCCESSFUL! ✅ ✅ ✅")
            print("=" * 80)
            print("\nDuckDuckGo browsing history is now accessible!")

        else:
            print("⚠️  Query returned no results")
            print("   (Database might be empty or filter too strict)")

    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()

else:
    print("❌ Could not find DuckDuckGo path")

print()
