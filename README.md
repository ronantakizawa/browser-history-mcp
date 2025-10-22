# browser-history-mcp

Access and search your browser history (Brave, Chrome, Firefox, Safari, Edge) through an MCP server for LLM chat apps.

## Features

This MCP server provides three tools to interact with your browser history:

- **search_history**: Search for specific terms in URLs and page titles
- **get_recent_history**: Get the most recent browsing history entries
- **get_most_visited**: Get your most frequently visited sites

All tools support Brave, Chrome, Firefox, Safari, and Microsoft Edge browsers via an optional `browser` parameter.

## Usage

Example prompts:
- "Search my Brave history for 'python tutorials'"
- "Search my Firefox history for 'machine learning'"
- "Show me my 20 most recent Safari browsing history entries"
- "What are my top 10 most visited Edge sites?"

## Install

- Install [Claude Desktop](https://claude.ai/download)
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Clone or navigate to this repository
- Setup environment: `uv venv && uv pip install -r pyproject.toml && source .venv/bin/activate`
- Install the MCP server: `fastmcp install claude-desktop mcp_server.py`
- Restart Claude Desktop

## MCP JSON Config

If you prefer to configure manually, add this to your Claude Desktop MCP configuration:

```json
"Browser History Service": {
  "command": "uv",
  "args": [
    "run",
    "--with",
    "fastmcp",
    "fastmcp",
    "run",
    "/Users/ronantakizawa/Documents/projects/bravebrowser/mcp_server.py"
  ],
  "env": {},
  "transport": "stdio"
}
```

**Note**: Replace the path with your actual path to `mcp_server.py`

## Browser Support

### Chromium-Based Browsers

All Chromium-based browsers share the same database format and work across all platforms.

#### Brave Browser
- **Windows**: `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\History`
- **macOS**: `~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History`
- **Linux**: `~/.config/BraveSoftware/Brave-Browser/Default/History`

#### Google Chrome
- **Windows**: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\History`
- **macOS**: `~/Library/Application Support/Google/Chrome/Default/History`
- **Linux**: `~/.config/google-chrome/Default/History`

#### Microsoft Edge
- **Windows**: `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\History`
- **macOS**: `~/Library/Application Support/Microsoft Edge/Default/History`
- **Linux**: `~/.config/microsoft-edge/Default/History`

### Firefox

Firefox uses a different database structure with profile folders:

- **Windows**: `%APPDATA%\Mozilla\Firefox\Profiles\[profile].default-release\places.sqlite`
- **macOS**: `~/Library/Application Support/Firefox/Profiles/[profile].default-release/places.sqlite`
- **Linux**: `~/.mozilla/firefox/[profile].default-release/places.sqlite`

**Note**: Firefox stores history in `places.sqlite`. The server automatically detects your active profile folder (prioritizing `.default-release` over `.default`).

### Safari Browser

Safari is supported on macOS only:
- **macOS**: `~/Library/Safari/History.db`

**Important**: Safari requires Full Disk Access permissions on macOS. If you encounter permission errors:

1. Open **System Settings** > **Privacy & Security** > **Full Disk Access**
2. Click the **+** button
3. Add the application running this MCP server:
   - For Claude Desktop: Add the Claude app
   - For terminal usage: Add Terminal.app or iTerm.app
   - For VS Code: Add Visual Studio Code.app
4. Restart the application after granting access

The server automatically detects your operating system and uses the appropriate path for each browser.

## Privacy Note

This server reads your local browser history databases in read-only mode. It creates temporary copies to avoid locking issues when browsers are running. No data is sent anywhere except to your local LLM chat application.
