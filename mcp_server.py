import sqlite3
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP
from typing import Literal

mcp = FastMCP("Browser History Service")


def get_history_db_path(browser: Literal["brave", "safari", "chrome", "firefox", "edge"] = "brave") -> Path:
    """
    Get the path to the browser history database.
    Handles cross-platform paths (Windows, macOS, Linux) for various browsers.
    Safari only supported on macOS.

    Args:
        browser: Which browser to get history from ("brave", "safari", "chrome", "firefox", or "edge")
    """
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


def query_history_db(query: str, params: tuple = (), browser: Literal["brave", "safari", "chrome", "firefox", "edge"] = "brave") -> list:
    """
    Query the browser history database safely by creating a temporary copy.
    The database may be locked if browser is running, so we copy it first.

    Args:
        query: SQL query to execute
        params: Query parameters
        browser: Which browser to query ("brave", "safari", "chrome", "firefox", or "edge")
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
def search_history(search_term: str, limit: int = 50, browser: Literal["brave", "safari", "chrome", "firefox", "edge"] = "brave") -> str:
    """
    Search browser history for URLs and titles containing the search term.

    Args:
        search_term: The text to search for in URLs and page titles
        limit: Maximum number of results to return (default: 50, max: 500)
        browser: Which browser to search ("brave", "safari", "chrome", "firefox", or "edge")

    Returns:
        Formatted list of matching history entries with titles, URLs, and visit times
    """
    if limit > 500:
        limit = 500

    if browser == "safari":
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
        # Chromium-based browsers (Brave/Chrome/Edge) database schema
        query = """
        SELECT url, title, visit_count, last_visit_time
        FROM urls
        WHERE url LIKE ? OR title LIKE ?
        ORDER BY last_visit_time DESC
        LIMIT ?
        """

    search_pattern = f"%{search_term}%"
    results = query_history_db(query, (search_pattern, search_pattern, limit), browser)

    if not results:
        return f"No history entries found matching '{search_term}' in {browser.capitalize()}"

    output = [f"Found {len(results)} {browser.capitalize()} history entries matching '{search_term}':\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']

        if browser == "safari":
            last_visit = safari_timestamp_to_datetime(entry['last_visit_time'])
        elif browser == "firefox":
            last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
        else:
            last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

        output.append(f"{i}. {title}")
        output.append(f"   URL: {url}")
        output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
        output.append("")

    return "\n".join(output)


@mcp.tool
def get_recent_history(limit: int = 50, browser: Literal["brave", "safari", "chrome", "firefox", "edge"] = "brave") -> str:
    """
    Get the most recent browsing history entries.

    Args:
        limit: Maximum number of results to return (default: 50, max: 500)
        browser: Which browser to query ("brave", "safari", "chrome", "firefox", or "edge")

    Returns:
        Formatted list of recent history entries with titles, URLs, and visit times
    """
    if limit > 500:
        limit = 500

    if browser == "safari":
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
        # Chromium-based browsers (Brave/Chrome/Edge) database schema
        query = """
        SELECT url, title, visit_count, last_visit_time
        FROM urls
        ORDER BY last_visit_time DESC
        LIMIT ?
        """

    results = query_history_db(query, (limit,), browser)

    if not results:
        return f"No history entries found in {browser.capitalize()}"

    output = [f"Most recent {len(results)} {browser.capitalize()} browsing history entries:\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']

        if browser == "safari":
            last_visit = safari_timestamp_to_datetime(entry['last_visit_time'])
        elif browser == "firefox":
            last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
        else:
            last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

        output.append(f"{i}. {title}")
        output.append(f"   URL: {url}")
        output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
        output.append("")

    return "\n".join(output)


@mcp.tool
def get_most_visited(limit: int = 20, browser: Literal["brave", "safari", "chrome", "firefox", "edge"] = "brave") -> str:
    """
    Get the most frequently visited sites from browser history.

    Args:
        limit: Maximum number of results to return (default: 20, max: 100)
        browser: Which browser to query ("brave", "safari", "chrome", "firefox", or "edge")

    Returns:
        Formatted list of most visited sites with visit counts
    """
    if limit > 100:
        limit = 100

    if browser == "safari":
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

    results = query_history_db(query, (limit,), browser)

    if not results:
        return f"No frequently visited sites found in {browser.capitalize()}"

    output = [f"Top {len(results)} most visited {browser.capitalize()} sites:\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']

        if browser == "safari":
            last_visit = safari_timestamp_to_datetime(entry['last_visit_time'])
        elif browser == "firefox":
            last_visit = firefox_timestamp_to_datetime(entry['last_visit_time'])
        else:
            last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

        output.append(f"{i}. {title}")
        output.append(f"   URL: {url}")
        output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
        output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    mcp.run()
