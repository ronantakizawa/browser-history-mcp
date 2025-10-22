import sqlite3
import os
import shutil
import tempfile
import base64
import subprocess
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP
from typing import Literal
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import plistlib

mcp = FastMCP("Browser History Service")


def get_duckduckgo_encryption_key():
    """Retrieve the DuckDuckGo encryption key from macOS Keychain."""
    try:
        result = subprocess.run(
            [
                'security', 'find-generic-password',
                '-s', 'DuckDuckGo Privacy Browser Encryption Key v2',
                '-a', 'com.duckduckgo.mobile.ios',
                '-w'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        key_b64 = result.stdout.strip()
        return base64.b64decode(key_b64)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to retrieve DuckDuckGo encryption key from keychain: {e}")


def decrypt_chacha_poly(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt data encrypted with ChaCha20-Poly1305."""
    if not encrypted_data or len(encrypted_data) < 28:
        raise ValueError("Encrypted data too short")

    try:
        chacha = ChaCha20Poly1305(key)
        nonce = encrypted_data[:12]
        ciphertext_with_tag = encrypted_data[12:]
        plaintext = chacha.decrypt(nonce, ciphertext_with_tag, None)
        return plaintext
    except Exception as e:
        raise Exception(f"Decryption failed: {e}")


def decode_nskeyedarchiver(data: bytes) -> str:
    """Decode NSKeyedArchiver data to get the original string or URL."""
    try:
        plist = plistlib.loads(data)
        if isinstance(plist, dict) and '$objects' in plist:
            objects = plist['$objects']
            for obj in objects:
                if isinstance(obj, str) and obj and obj != '$null':
                    if obj.startswith('http') or obj.startswith('file'):
                        return obj
                    if len(obj) > 0 and not obj.startswith('NS'):
                        return obj

        text = data.decode('utf-8', errors='ignore')
        parts = [p for p in text.split('\x00') if p and len(p) > 3 and not p.startswith('NS')]
        if parts:
            for part in sorted(parts, key=len, reverse=True):
                if part.startswith('http') or part.startswith('file'):
                    return part
                if len(part) > 5 and part.isprintable():
                    return part

        return "[Could not decode]"
    except Exception as e:
        return f"[Decode error: {e}]"


def decrypt_duckduckgo_field(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt and decode an encrypted DuckDuckGo field (URL or title)."""
    if not encrypted_data:
        return "[Empty]"

    try:
        decrypted_data = decrypt_chacha_poly(encrypted_data, key)
        decoded_string = decode_nskeyedarchiver(decrypted_data)
        return decoded_string
    except Exception as e:
        return f"[Error: {e}]"


def cocoa_timestamp_to_datetime(cocoa_timestamp: float) -> str:
    """Convert Cocoa/Apple timestamp to readable datetime."""
    if not cocoa_timestamp or cocoa_timestamp == 0:
        return "Never"

    try:
        mac_epoch = datetime(2001, 1, 1)
        dt = datetime.fromtimestamp(mac_epoch.timestamp() + cocoa_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid timestamp"


def get_history_db_path(browser: Literal["brave", "safari", "chrome", "firefox", "edge", "arc", "opera", "duckduckgo"] = "brave") -> Path:
    """
    Get the path to the browser history database.
    Handles cross-platform paths (Windows, macOS, Linux) for various browsers.
    Safari and DuckDuckGo only supported on macOS. Arc currently only on macOS.

    Args:
        browser: Which browser to get history from ("brave", "safari", "chrome", "firefox", "edge", "arc", "opera", or "duckduckgo")
    """
    if browser == "duckduckgo":
        # DuckDuckGo only available on macOS
        if os.uname().sysname != 'Darwin':
            raise ValueError("DuckDuckGo is only available on macOS")
        return Path.home() / "Library/Containers/com.duckduckgo.mobile.ios/Data/Library/Application Support/Database.sqlite"

    if browser == "safari":
        # Safari only available on macOS
        if os.uname().sysname != 'Darwin':
            raise ValueError("Safari is only available on macOS")
        return Path.home() / "Library" / "Safari" / "History.db"

    # Chromium-based browsers (Brave, Chrome, Edge)
    if browser == "chrome":
        if os.name == 'nt':  # Windows
            history_path = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "History"
        elif os.uname().sysname == 'Darwin':  # macOS
            history_path = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "History"
        else:  # Linux
            history_path = Path.home() / ".config" / "google-chrome" / "Default" / "History"

    elif browser == "edge":
        # Microsoft Edge (Chromium-based)
        if os.name == 'nt':  # Windows
            history_path = Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default" / "History"
        elif os.uname().sysname == 'Darwin':  # macOS
            history_path = Path.home() / "Library" / "Application Support" / "Microsoft Edge" / "Default" / "History"
        else:  # Linux
            history_path = Path.home() / ".config" / "microsoft-edge" / "Default" / "History"

    elif browser == "arc":
        # Arc Browser (Chromium-based, currently macOS only)
        if os.uname().sysname == 'Darwin':  # macOS
            history_path = Path.home() / "Library" / "Application Support" / "Arc" / "User Data" / "Default" / "History"
        else:
            raise ValueError("Arc browser is currently only available on macOS")

    elif browser == "opera":
        # Opera (Chromium-based)
        if os.name == 'nt':  # Windows
            history_path = Path.home() / "AppData" / "Roaming" / "Opera Software" / "Opera Stable" / "History"
        elif os.uname().sysname == 'Darwin':  # macOS
            history_path = Path.home() / "Library" / "Application Support" / "com.operasoftware.Opera" / "Default" / "History"
        else:  # Linux
            history_path = Path.home() / ".config" / "opera" / "Default" / "History"

    elif browser == "firefox":
        # Firefox uses a different structure with profile folders
        if os.name == 'nt':  # Windows
            profiles_path = Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
        elif os.uname().sysname == 'Darwin':  # macOS
            profiles_path = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
        else:  # Linux
            profiles_path = Path.home() / ".mozilla" / "firefox"

        # Firefox stores history in places.sqlite in the profile directory
        # Look for the default profile (prioritize .default-release over .default)
        if profiles_path.exists():
            # Try .default-release first (newer Firefox versions)
            profile_folders = list(profiles_path.glob("*.default-release"))
            if not profile_folders:
                # Fall back to .default
                profile_folders = list(profiles_path.glob("*.default"))

            if profile_folders:
                # Check if places.sqlite actually exists in the profile
                for profile in profile_folders:
                    potential_path = profile / "places.sqlite"
                    if potential_path.exists():
                        history_path = potential_path
                        break
                else:
                    raise FileNotFoundError(f"places.sqlite not found in Firefox profile folders at {profiles_path}")
            else:
                raise FileNotFoundError(f"Firefox profile folder not found in {profiles_path}")
        else:
            raise FileNotFoundError(f"Firefox profiles directory not found at {profiles_path}")

    else:  # brave
        if os.name == 'nt':  # Windows
            history_path = Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "History"
        elif os.uname().sysname == 'Darwin':  # macOS
            history_path = Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "Default" / "History"
        else:  # Linux
            history_path = Path.home() / ".config" / "BraveSoftware" / "Brave-Browser" / "Default" / "History"

    return history_path


def query_history_db(query: str, params: tuple = (), browser: Literal["brave", "safari", "chrome", "firefox", "edge", "arc", "opera"] = "brave") -> list:
    """
    Query the browser history database safely by creating a temporary copy.
    The database may be locked if browser is running, so we copy it first.

    Args:
        query: SQL query to execute
        params: Query parameters
        browser: Which browser to query ("brave", "safari", "chrome", "firefox", "edge", "arc", or "opera")
    """
    history_path = get_history_db_path(browser)

    if not history_path.exists():
        raise FileNotFoundError(f"{browser.capitalize()} history database not found at {history_path}")

    # Create a temporary copy of the database to avoid locking issues
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        tmp_path = tmp_file.name

    try:
        shutil.copy2(history_path, tmp_path)
    except PermissionError as e:
        # Clean up temp file if copy failed
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

        if browser == "safari":
            raise PermissionError(
                f"Permission denied to access Safari history.\n\n"
                f"To fix this, grant Full Disk Access:\n"
                f"1. Open System Settings > Privacy & Security > Full Disk Access\n"
                f"2. Click the '+' button\n"
                f"3. Add your terminal app (Terminal.app or iTerm.app) or IDE (VS Code, etc.)\n"
                f"4. Restart the application\n\n"
                f"Alternatively, you can access Brave history which doesn't require special permissions."
            ) from e
        else:
            raise

    try:
        # Query the temporary database
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def query_duckduckgo_db(query: str, params: tuple = ()) -> list:
    """
    Query the DuckDuckGo history database with decryption support.
    DuckDuckGo stores URLs and titles in encrypted format using ChaCha20-Poly1305.

    Args:
        query: SQL query to execute
        params: Query parameters

    Returns:
        List of dictionaries with decrypted data
    """
    # Get encryption key
    try:
        key = get_duckduckgo_encryption_key()
    except Exception as e:
        raise Exception(f"Failed to get DuckDuckGo encryption key: {e}")

    history_path = get_history_db_path("duckduckgo")

    if not history_path.exists():
        raise FileNotFoundError(f"DuckDuckGo history database not found at {history_path}")

    # Create a temporary copy of the database to avoid locking issues
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        tmp_path = tmp_file.name

    try:
        shutil.copy2(history_path, tmp_path)
    except PermissionError as e:
        # Clean up temp file if copy failed
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise PermissionError(
            f"Permission denied to access DuckDuckGo history.\n\n"
            f"To fix this, grant Full Disk Access:\n"
            f"1. Open System Settings > Privacy & Security > Full Disk Access\n"
            f"2. Click the '+' button\n"
            f"3. Add your terminal app (Terminal.app or iTerm.app) or IDE (VS Code, etc.)\n"
            f"4. Restart the application"
        ) from e

    try:
        # Query the temporary database
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        raw_results = cursor.fetchall()
        conn.close()

        # Decrypt the results
        decrypted_results = []
        for row in raw_results:
            # DuckDuckGo schema: ZURLENCRYPTED, ZTITLEENCRYPTED, ZNUMBEROFTOTALVISITS, ZNUMBEROFTRACKERSBLOCKED, ZLASTVISIT
            url_encrypted, title_encrypted, visits, trackers_blocked, last_visit = row

            # Decrypt URL and title
            url = decrypt_duckduckgo_field(url_encrypted, key)
            title = decrypt_duckduckgo_field(title_encrypted, key) if title_encrypted else "No title"

            decrypted_results.append({
                'url': url,
                'title': title,
                'visit_count': visits or 0,
                'trackers_blocked': trackers_blocked or 0,
                'last_visit_time': last_visit
            })

        return decrypted_results
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def chrome_timestamp_to_datetime(chrome_timestamp: int) -> str:
    """
    Convert Chrome/Brave timestamp (microseconds since 1601-01-01) to readable datetime.
    """
    if chrome_timestamp == 0:
        return "Never"

    # Chrome timestamps are in microseconds since January 1, 1601
    epoch_start = datetime(1601, 1, 1)
    delta = chrome_timestamp / 1_000_000  # Convert to seconds

    try:
        dt = datetime.fromtimestamp(epoch_start.timestamp() + delta)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid timestamp"


def safari_timestamp_to_datetime(safari_timestamp: float) -> str:
    """
    Convert Safari timestamp (seconds since 2001-01-01) to readable datetime.
    """
    if safari_timestamp == 0:
        return "Never"

    # Safari timestamps are seconds since January 1, 2001 (macOS epoch)
    mac_epoch = datetime(2001, 1, 1)

    try:
        dt = datetime.fromtimestamp(mac_epoch.timestamp() + safari_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid timestamp"


def firefox_timestamp_to_datetime(firefox_timestamp: int) -> str:
    """
    Convert Firefox timestamp (microseconds since 1970-01-01) to readable datetime.
    """
    if firefox_timestamp == 0 or firefox_timestamp is None:
        return "Never"

    # Firefox timestamps are in microseconds since January 1, 1970 (Unix epoch)
    try:
        dt = datetime.fromtimestamp(firefox_timestamp / 1_000_000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid timestamp"


@mcp.tool
def search_history(search_term: str, limit: int = 50, browser: Literal["brave", "safari", "chrome", "firefox", "edge", "arc", "opera", "duckduckgo"] = "brave") -> str:
    """
    Search browser history for URLs and titles containing the search term.

    Args:
        search_term: The text to search for in URLs and page titles
        limit: Maximum number of results to return (default: 50, max: 500)
        browser: Which browser to search ("brave", "safari", "chrome", "firefox", "edge", "arc", "opera", or "duckduckgo")

    Returns:
        Formatted list of matching history entries with titles, URLs, and visit times
    """
    if limit > 500:
        limit = 500

    if browser == "duckduckgo":
        # DuckDuckGo database schema with encrypted fields
        query = """
            SELECT
                ZURLENCRYPTED,
                ZTITLEENCRYPTED,
                ZNUMBEROFTOTALVISITS,
                ZNUMBEROFTRACKERSBLOCKED,
                ZLASTVISIT
            FROM ZHISTORYENTRYMANAGEDOBJECT
            WHERE ZURLENCRYPTED IS NOT NULL
            ORDER BY ZLASTVISIT DESC
            LIMIT ?
        """
        # DuckDuckGo needs special handling - decrypt first, then filter
        all_results = query_duckduckgo_db(query, (limit * 2,))  # Get more results to account for filtering

        # Filter results by search term after decryption
        results = [
            entry for entry in all_results
            if search_term.lower() in entry['url'].lower() or search_term.lower() in entry['title'].lower()
        ][:limit]

    elif browser == "safari":
        # Safari database schema
        query = """
        SELECT
            history_items.url as url,
            history_visits.title as title,
            COUNT(history_visits.id) as visit_count,
            MAX(history_visits.visit_time) as last_visit_time
        FROM history_items
        JOIN history_visits ON history_items.id = history_visits.history_item
        WHERE history_items.url LIKE ? OR history_visits.title LIKE ?
        GROUP BY history_items.url
        ORDER BY last_visit_time DESC
        LIMIT ?
        """
    elif browser == "firefox":
        # Firefox database schema (places.sqlite)
        query = """
        SELECT
            moz_places.url as url,
            moz_places.title as title,
            moz_places.visit_count as visit_count,
            moz_places.last_visit_date as last_visit_time
        FROM moz_places
        WHERE (moz_places.url LIKE ? OR moz_places.title LIKE ?)
        AND moz_places.hidden = 0
        ORDER BY last_visit_time DESC
        LIMIT ?
        """
    else:
        # Chromium-based browsers (Brave/Chrome/Edge/Arc/Opera) database schema
        query = """
        SELECT url, title, visit_count, last_visit_time
        FROM urls
        WHERE url LIKE ? OR title LIKE ?
        ORDER BY last_visit_time DESC
        LIMIT ?
        """

    # Query databases (DuckDuckGo already queried above)
    if browser != "duckduckgo":
        search_pattern = f"%{search_term}%"
        results = query_history_db(query, (search_pattern, search_pattern, limit), browser)

    if not results:
        return f"No history entries found matching '{search_term}' in {browser.capitalize()}"

    output = [f"Found {len(results)} {browser.capitalize()} history entries matching '{search_term}':\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']

        if browser == "duckduckgo":
            last_visit = cocoa_timestamp_to_datetime(entry['last_visit_time'])
            trackers_blocked = entry.get('trackers_blocked', 0)
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Trackers blocked: {trackers_blocked} | Last visited: {last_visit}")
            output.append("")
        elif browser == "safari":
            last_visit = safari_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")
        elif browser == "firefox":
            last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")
        else:
            last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")

    return "\n".join(output)


@mcp.tool
def get_recent_history(limit: int = 50, browser: Literal["brave", "safari", "chrome", "firefox", "edge", "arc", "opera", "duckduckgo"] = "brave") -> str:
    """
    Get the most recent browsing history entries.

    Args:
        limit: Maximum number of results to return (default: 50, max: 500)
        browser: Which browser to query ("brave", "safari", "chrome", "firefox", "edge", "arc", "opera", or "duckduckgo")

    Returns:
        Formatted list of recent history entries with titles, URLs, and visit times
    """
    if limit > 500:
        limit = 500

    if browser == "duckduckgo":
        # DuckDuckGo database schema with encrypted fields
        query = """
            SELECT
                ZURLENCRYPTED,
                ZTITLEENCRYPTED,
                ZNUMBEROFTOTALVISITS,
                ZNUMBEROFTRACKERSBLOCKED,
                ZLASTVISIT
            FROM ZHISTORYENTRYMANAGEDOBJECT
            WHERE ZURLENCRYPTED IS NOT NULL
            ORDER BY ZLASTVISIT DESC
            LIMIT ?
        """
        results = query_duckduckgo_db(query, (limit,))

    elif browser == "safari":
        # Safari database schema
        query = """
        SELECT
            history_items.url as url,
            history_visits.title as title,
            COUNT(history_visits.id) as visit_count,
            MAX(history_visits.visit_time) as last_visit_time
        FROM history_items
        JOIN history_visits ON history_items.id = history_visits.history_item
        GROUP BY history_items.url
        ORDER BY last_visit_time DESC
        LIMIT ?
        """
    elif browser == "firefox":
        # Firefox database schema (places.sqlite)
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
        # Chromium-based browsers (Brave/Chrome/Edge/Arc/Opera) database schema
        query = """
        SELECT url, title, visit_count, last_visit_time
        FROM urls
        ORDER BY last_visit_time DESC
        LIMIT ?
        """

    # Query databases (DuckDuckGo already queried above)
    if browser != "duckduckgo":
        results = query_history_db(query, (limit,), browser)

    if not results:
        return f"No history entries found in {browser.capitalize()}"

    output = [f"Most recent {len(results)} {browser.capitalize()} browsing history entries:\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']

        if browser == "duckduckgo":
            last_visit = cocoa_timestamp_to_datetime(entry['last_visit_time'])
            trackers_blocked = entry.get('trackers_blocked', 0)
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Trackers blocked: {trackers_blocked} | Last visited: {last_visit}")
            output.append("")
        elif browser == "safari":
            last_visit = safari_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")
        elif browser == "firefox":
            last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")
        else:
            last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")

    return "\n".join(output)


@mcp.tool
def get_most_visited(limit: int = 20, browser: Literal["brave", "safari", "chrome", "firefox", "edge", "arc", "opera", "duckduckgo"] = "brave") -> str:
    """
    Get the most frequently visited sites from browser history.

    Args:
        limit: Maximum number of results to return (default: 20, max: 100)
        browser: Which browser to query ("brave", "safari", "chrome", "firefox", "edge", "arc", "opera", or "duckduckgo")

    Returns:
        Formatted list of most visited sites with visit counts
    """
    if limit > 100:
        limit = 100

    if browser == "duckduckgo":
        # DuckDuckGo database schema with encrypted fields
        query = """
            SELECT
                ZURLENCRYPTED,
                ZTITLEENCRYPTED,
                ZNUMBEROFTOTALVISITS,
                ZNUMBEROFTRACKERSBLOCKED,
                ZLASTVISIT
            FROM ZHISTORYENTRYMANAGEDOBJECT
            WHERE ZURLENCRYPTED IS NOT NULL AND ZNUMBEROFTOTALVISITS > 1
            ORDER BY ZNUMBEROFTOTALVISITS DESC
            LIMIT ?
        """
        results = query_duckduckgo_db(query, (limit,))

    elif browser == "safari":
        # Safari database schema
        query = """
        SELECT
            history_items.url as url,
            history_visits.title as title,
            COUNT(history_visits.id) as visit_count,
            MAX(history_visits.visit_time) as last_visit_time
        FROM history_items
        JOIN history_visits ON history_items.id = history_visits.history_item
        GROUP BY history_items.url
        HAVING visit_count > 1
        ORDER BY visit_count DESC
        LIMIT ?
        """
    elif browser == "firefox":
        # Firefox database schema (places.sqlite)
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
        # Chromium-based browsers (Brave/Chrome/Edge) database schema
        query = """
        SELECT url, title, visit_count, last_visit_time
        FROM urls
        WHERE visit_count > 1
        ORDER BY visit_count DESC
        LIMIT ?
        """

    # Query databases (DuckDuckGo already queried above)
    if browser != "duckduckgo":
        results = query_history_db(query, (limit,), browser)

    if not results:
        return f"No frequently visited sites found in {browser.capitalize()}"

    output = [f"Top {len(results)} most visited {browser.capitalize()} sites:\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']

        if browser == "duckduckgo":
            last_visit = cocoa_timestamp_to_datetime(entry['last_visit_time'])
            trackers_blocked = entry.get('trackers_blocked', 0)
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Trackers blocked: {trackers_blocked} | Last visited: {last_visit}")
            output.append("")
        elif browser == "safari":
            last_visit = safari_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")
        elif browser == "firefox":
            last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")
        else:
            last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])
            output.append(f"{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
            output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    mcp.run()
