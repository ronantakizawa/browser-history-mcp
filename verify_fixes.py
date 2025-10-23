#!/usr/bin/env python3
"""
Verification script to confirm all issues are fixed:
1. platform.system() is used instead of os.uname().sysname
2. All SQL queries use parameterized queries (no SQL injection)
"""

import re
from pathlib import Path

def check_platform_usage():
    """Verify platform.system() is used instead of os.uname().sysname"""
    print("=" * 60)
    print("Checking for cross-platform OS detection...")
    print("=" * 60)

    with open('mcp_server.py', 'r') as f:
        content = f.read()

    # Check for platform import
    if 'import platform' in content:
        print("✅ platform module is imported")
    else:
        print("❌ platform module is NOT imported")
        return False

    # Check for os.uname() usage (should be 0)
    uname_matches = re.findall(r'os\.uname\(\)', content)
    if uname_matches:
        print(f"❌ Found {len(uname_matches)} instances of os.uname() - should use platform.system()")
        return False
    else:
        print("✅ No instances of os.uname() found")

    # Check for platform.system() usage
    platform_matches = re.findall(r'platform\.system\(\)', content)
    if platform_matches:
        print(f"✅ Found {len(platform_matches)} instances of platform.system()")
    else:
        print("⚠️  Warning: No instances of platform.system() found")

    print()
    return True


def check_sql_injection_protection():
    """Verify all SQL queries use parameterized queries"""
    print("=" * 60)
    print("Checking SQL injection protection...")
    print("=" * 60)

    with open('mcp_server.py', 'r') as f:
        lines = f.readlines()

    # Find all cursor.execute calls
    execute_calls = []
    for i, line in enumerate(lines, 1):
        if 'cursor.execute' in line:
            execute_calls.append((i, line.strip()))

    print(f"Found {len(execute_calls)} cursor.execute() calls:")

    all_safe = True
    for line_num, line in execute_calls:
        # Check if it uses parameterized queries (has two arguments)
        if re.search(r'cursor\.execute\([^,]+,\s*\w+\)', line):
            print(f"  Line {line_num}: ✅ Uses parameterized query")
        else:
            print(f"  Line {line_num}: ⚠️  {line}")
            all_safe = False

    # Check for dangerous string formatting in SQL
    sql_string_format = re.findall(r'(SELECT|INSERT|UPDATE|DELETE).*[%f]\{', '\n'.join(lines), re.IGNORECASE)
    if sql_string_format:
        print(f"\n❌ Found SQL queries with string formatting (potential SQL injection):")
        for match in sql_string_format:
            print(f"  {match}")
        all_safe = False
    else:
        print("\n✅ No SQL string formatting detected")

    print()
    return all_safe


def main():
    print("\n" + "=" * 60)
    print("VERIFYING CODE FIXES")
    print("=" * 60 + "\n")

    platform_ok = check_platform_usage()
    sql_ok = check_sql_injection_protection()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Cross-platform OS detection: {'✅ PASS' if platform_ok else '❌ FAIL'}")
    print(f"SQL injection protection: {'✅ PASS' if sql_ok else '❌ FAIL'}")
    print("=" * 60)

    if platform_ok and sql_ok:
        print("\n✅ ALL ISSUES FIXED!")
    else:
        print("\n❌ SOME ISSUES REMAIN")
    print()


if __name__ == "__main__":
    main()
