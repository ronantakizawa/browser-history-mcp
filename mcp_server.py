import sqlite3
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP("Brave Browser History Service")


def get_history_db_path() -> Path:
    """
    Get the path to the Brave browser history database.
    Handles cross-platform paths (Windows, macOS, Linux).
    """
    if os.name == 'nt':  # Windows
        history_path = Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "History"
    elif os.uname().sysname == 'Darwin':  # macOS
        history_path = Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "Default" / "History"
    else:  # Linux
        history_path = Path.home() / ".config" / "BraveSoftware" / "Brave-Browser" / "Default" / "History"

    return history_path


def query_history_db(query: str, params: tuple = ()) -> list:
    """
    Query the Brave browser history database safely by creating a temporary copy.
    The database may be locked if Brave is running, so we copy it first.
    """
    history_path = get_history_db_path()

    if not history_path.exists():
        raise FileNotFoundError(f"Brave history database not found at {history_path}")

    # Create a temporary copy of the database to avoid locking issues
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        tmp_path = tmp_file.name

    try:
        shutil.copy2(history_path, tmp_path)

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


@mcp.tool
def search_history(search_term: str, limit: int = 50) -> str:
    """
    Search Brave browser history for URLs and titles containing the search term.

    Args:
        search_term: The text to search for in URLs and page titles
        limit: Maximum number of results to return (default: 50, max: 500)

    Returns:
        Formatted list of matching history entries with titles, URLs, and visit times
    """
    if limit > 500:
        limit = 500

    query = """
    SELECT url, title, visit_count, last_visit_time
    FROM urls
    WHERE url LIKE ? OR title LIKE ?
    ORDER BY last_visit_time DESC
    LIMIT ?
    """

    search_pattern = f"%{search_term}%"
    results = query_history_db(query, (search_pattern, search_pattern, limit))

    if not results:
        return f"No history entries found matching '{search_term}'"

    output = [f"Found {len(results)} history entries matching '{search_term}':\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']
        last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

        output.append(f"{i}. {title}")
        output.append(f"   URL: {url}")
        output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
        output.append("")

    return "\n".join(output)


@mcp.tool
def get_recent_history(limit: int = 50) -> str:
    """
    Get the most recent browsing history entries.

    Args:
        limit: Maximum number of results to return (default: 50, max: 500)

    Returns:
        Formatted list of recent history entries with titles, URLs, and visit times
    """
    if limit > 500:
        limit = 500

    query = """
    SELECT url, title, visit_count, last_visit_time
    FROM urls
    ORDER BY last_visit_time DESC
    LIMIT ?
    """

    results = query_history_db(query, (limit,))

    if not results:
        return "No history entries found"

    output = [f"Most recent {len(results)} browsing history entries:\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']
        last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

        output.append(f"{i}. {title}")
        output.append(f"   URL: {url}")
        output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
        output.append("")

    return "\n".join(output)


@mcp.tool
def get_most_visited(limit: int = 20) -> str:
    """
    Get the most frequently visited sites from browser history.

    Args:
        limit: Maximum number of results to return (default: 20, max: 100)

    Returns:
        Formatted list of most visited sites with visit counts
    """
    if limit > 100:
        limit = 100

    query = """
    SELECT url, title, visit_count, last_visit_time
    FROM urls
    WHERE visit_count > 1
    ORDER BY visit_count DESC
    LIMIT ?
    """

    results = query_history_db(query, (limit,))

    if not results:
        return "No frequently visited sites found"

    output = [f"Top {len(results)} most visited sites:\n"]

    for i, entry in enumerate(results, 1):
        title = entry['title'] or "No title"
        url = entry['url']
        visit_count = entry['visit_count']
        last_visit = chrome_timestamp_to_datetime(entry['last_visit_time'])

        output.append(f"{i}. {title}")
        output.append(f"   URL: {url}")
        output.append(f"   Visits: {visit_count} | Last visited: {last_visit}")
        output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    mcp.run()
