#!/usr/bin/env python3
"""
Check all DuckDuckGo database files, including encrypted ones.
Try to decrypt encrypted databases using the same scheme as macOS.
"""

import sqlite3
import tempfile
import shutil
import struct
import base64
from pathlib import Path

# Encryption imports
try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  cryptography library not available - cannot decrypt encrypted databases")


def get_encryption_key_windows():
    """
    Try to get DuckDuckGo encryption key from Windows.
    The key might be stored in Windows Credential Manager or Registry.
    """
    # Try different possible locations for the encryption key on Windows

    # Option 1: Check if there's a key file in the DuckDuckGo directory
    package_base = Path.home() / "AppData" / "Local" / "Packages"
    for package in package_base.iterdir():
        if "duckduckgo" in package.name.lower():
            # Look for key files
            possible_key_files = [
                package / "LocalState" / "encryption_key",
                package / "LocalState" / "key",
                package / "LocalState" / ".key",
                package / "Settings" / "settings.dat",
            ]

            for key_file in possible_key_files:
                if key_file.exists():
                    print(f"🔑 Found potential key file: {key_file}")
                    try:
                        with open(key_file, 'rb') as f:
                            key_data = f.read()
                            print(f"   Size: {len(key_data)} bytes")
                            print(f"   First 32 bytes (hex): {key_data[:32].hex()}")
                    except Exception as e:
                        print(f"   Error reading: {e}")

    # Option 2: Try common encryption keys (DuckDuckGo might use a hardcoded key on Windows)
    # This is speculative - we'll try a few common patterns

    print("\n⚠️  No encryption key found in expected locations")
    print("   The encryption key might be:")
    print("   1. Stored in Windows Credential Manager")
    print("   2. Hardcoded in the DuckDuckGo application")
    print("   3. Derived from a user/machine-specific value")

    return None


def decode_nskeyedarchiver(data: bytes) -> str:
    """Decode NSKeyedArchiver format (used on macOS, might be used on Windows too)."""
    try:
        # Simple string extraction for NSKeyedArchiver
        # Look for string data after markers
        if b'NS.string' in data:
            start = data.find(b'NS.string') + len(b'NS.string')
            # Skip some bytes and try to find the string
            remaining = data[start:]

            # Look for length-prefixed string
            for i in range(min(20, len(remaining))):
                try:
                    length = struct.unpack('B', remaining[i:i+1])[0]
                    if 0 < length < 200:  # Reasonable URL length
                        potential_string = remaining[i+1:i+1+length]
                        if potential_string.startswith(b'http'):
                            return potential_string.decode('utf-8', errors='ignore')
                except:
                    continue

        # Fallback: look for http/https strings
        if b'http' in data:
            start = data.find(b'http')
            end = data.find(b'\x00', start)
            if end > start:
                return data[start:end].decode('utf-8', errors='ignore')

        return None
    except Exception as e:
        return None


def decrypt_chacha_poly(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt data encrypted with ChaCha20-Poly1305."""
    try:
        if not CRYPTO_AVAILABLE:
            return None

        # Extract nonce (first 12 bytes) and ciphertext
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        # Decrypt
        cipher = ChaCha20Poly1305(key)
        decrypted = cipher.decrypt(nonce, ciphertext, None)

        # Try to decode as NSKeyedArchiver format
        decoded = decode_nskeyedarchiver(decrypted)
        if decoded:
            return decoded

        # Fallback: try direct UTF-8 decode
        return decrypted.decode('utf-8', errors='ignore')

    except Exception as e:
        return None


def try_decrypt_database(db_path, encryption_key=None):
    """
    Try to open and decrypt a database file.
    Returns: (is_sqlite, has_urls, total_urls, external_urls, sample_urls)
    """
    try:
        # First, try to open as regular SQLite
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_path = tmp_file.name

        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in cursor.fetchall()]

            # Check for urls table (Chromium schema)
            if 'urls' in tables:
                cursor.execute("SELECT COUNT(*) as count FROM urls")
                total = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM urls WHERE url NOT LIKE 'https://static.ddg.local/%'")
                external = cursor.fetchone()['count']

                # Get sample URLs
                cursor.execute("""
                    SELECT url, title, visit_count
                    FROM urls
                    WHERE url NOT LIKE 'https://static.ddg.local/%'
                    ORDER BY last_visit_time DESC
                    LIMIT 5
                """)
                samples = cursor.fetchall()

                conn.close()
                return True, True, total, external, samples

            # Check for encrypted DuckDuckGo schema (macOS style)
            if 'ZHISTORYENTRYMANAGEDOBJECT' in tables:
                print(f"      🔐 Found encrypted schema!")

                if not encryption_key or not CRYPTO_AVAILABLE:
                    conn.close()
                    return True, False, 0, 0, []

                cursor.execute("""
                    SELECT
                        ZURLENCRYPTED,
                        ZTITLEENCRYPTED,
                        ZNUMBEROFTOTALVISITS
                    FROM ZHISTORYENTRYMANAGEDOBJECT
                    WHERE ZURLENCRYPTED IS NOT NULL
                    LIMIT 10
                """)

                encrypted_entries = cursor.fetchall()
                decrypted_samples = []

                for entry in encrypted_entries:
                    try:
                        encrypted_url = entry['ZURLENCRYPTED']
                        encrypted_title = entry['ZTITLEENCRYPTED']

                        decrypted_url = decrypt_chacha_poly(encrypted_url, encryption_key)
                        decrypted_title = decrypt_chacha_poly(encrypted_title, encryption_key) if encrypted_title else None

                        if decrypted_url and 'static.ddg.local' not in decrypted_url:
                            decrypted_samples.append({
                                'url': decrypted_url,
                                'title': decrypted_title or '(no title)',
                                'visit_count': entry['ZNUMBEROFTOTALVISITS']
                            })
                    except Exception as e:
                        continue

                conn.close()

                if decrypted_samples:
                    return True, True, len(encrypted_entries), len(decrypted_samples), decrypted_samples
                else:
                    return True, False, len(encrypted_entries), 0, []

            # Other SQLite database
            conn.close()
            return True, False, 0, 0, []

        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except sqlite3.DatabaseError:
        # Not a SQLite database or encrypted at file level
        # Try to read as raw encrypted data
        if encryption_key and CRYPTO_AVAILABLE:
            try:
                with open(db_path, 'rb') as f:
                    data = f.read()

                # Check if this looks like encrypted data
                # DuckDuckGo encrypted files might have specific headers
                if len(data) > 100:
                    print(f"      📄 File size: {len(data)} bytes")
                    print(f"      🔍 Header (hex): {data[:16].hex()}")
                    print(f"      🔍 Trying to decrypt as encrypted blob...")

                    # Try to decrypt the whole file or chunks
                    # This is speculative - the encryption format might differ

            except Exception as e:
                pass

        return False, False, 0, 0, []

    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False, False, 0, 0, []


def main():
    """Check all DuckDuckGo databases."""
    print("=" * 80)
    print("CHECKING ALL DUCKDUCKGO DATABASES (INCLUDING ENCRYPTED)")
    print("=" * 80)

    # Try to get encryption key
    print("\n[STEP 1] Looking for encryption key...")
    print("-" * 80)
    encryption_key = get_encryption_key_windows()

    # Find DuckDuckGo package
    package_base = Path.home() / "AppData" / "Local" / "Packages"

    if not package_base.exists():
        print(f"❌ Packages directory not found: {package_base}")
        return

    duckduckgo_packages = []
    for package in package_base.iterdir():
        if "duckduckgo" in package.name.lower():
            duckduckgo_packages.append(package)

    if not duckduckgo_packages:
        print("❌ No DuckDuckGo packages found!")
        return

    print(f"\n[STEP 2] Checking all database files...")
    print("-" * 80)

    for package_dir in duckduckgo_packages:
        print(f"\n📦 Package: {package_dir.name}\n")

        # Find all potential database files
        db_files = []

        for ext in ['History', '*.db', '*.sqlite']:
            for file in package_dir.rglob(ext):
                if file.is_file():
                    db_files.append(file)

        db_files = list(set(db_files))

        print(f"📊 Found {len(db_files)} potential database file(s)\n")

        for db_file in sorted(db_files):
            size = db_file.stat().st_size
            relative_path = db_file.relative_to(package_dir)

            print(f"{'─' * 80}")
            print(f"📄 {relative_path}")
            print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")

            is_sqlite, has_urls, total, external, samples = try_decrypt_database(db_file, encryption_key)

            if not is_sqlite:
                print(f"   ⚠️  Not a SQLite database (might be encrypted at file level)")

                # Show first few bytes to identify format
                try:
                    with open(db_file, 'rb') as f:
                        header = f.read(16)
                        print(f"   🔍 Header (hex): {header.hex()}")
                        print(f"   🔍 Header (ascii): {header}")
                except:
                    pass

            elif has_urls:
                if external > 0:
                    print(f"   ✅ ✅ ✅ FOUND BROWSING HISTORY! ✅ ✅ ✅")
                    print(f"   📊 Total URLs: {total}")
                    print(f"   🌐 External websites: {external}")
                    print(f"   🏠 Internal pages: {total - external}")
                    print(f"\n   📖 Sample external URLs:")

                    for i, sample in enumerate(samples[:5], 1):
                        url = sample.get('url', sample[0]) if isinstance(sample, dict) else sample[0]
                        title = sample.get('title', sample[1]) if isinstance(sample, dict) else sample[1]

                        # Truncate long URLs
                        display_url = url if len(url) <= 70 else url[:67] + "..."

                        print(f"\n   {i}. {title}")
                        print(f"      {display_url}")

                    print(f"\n   🎯 THIS IS THE CORRECT DATABASE!")
                    print(f"   Full path: {db_file}")
                else:
                    print(f"   ⚠️  Has urls table but no external URLs")
                    print(f"   📊 Total URLs: {total} (all internal DuckDuckGo pages)")
            else:
                print(f"   ℹ️  SQLite database, but no browsing history found")

            print()

    print("=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
