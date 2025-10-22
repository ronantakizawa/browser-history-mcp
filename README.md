# search-history-mcp

<img width="1024" height="512" alt="browser-histo (2)" src="https://github.com/user-attachments/assets/9bd134ed-b400-45ae-8134-9c3f854989b3" />



Access and search your browser search history (Brave, Chrome, Firefox, Safari, Edge, Arc, Opera, DuckDuckGo) through an MCP server for LLM chat apps.

## Features

This MCP server provides three tools to interact with your search history:

- **search_history**: Search for specific terms in URLs and page titles
- **get_recent_history**: Get the most recent browsing history entries
- **get_most_visited**: Get your most frequently visited sites

All tools support Brave, Chrome, Firefox, Safari, Microsoft Edge, Arc, Opera, and DuckDuckGo via an optional `browser` parameter.

## Usage

Example prompts:
- "Search my Brave history for 'python tutorials'"
- "Search my Firefox history for 'machine learning'"
- "Show me my 20 most recent Safari browsing history entries"
- "What are my top 10 most visited Arc sites?"
- "Search my Opera history for 'web development'"
- "Show me my recent DuckDuckGo browsing history"

## Install

- Install [Claude Desktop](https://claude.ai/download)
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Clone or navigate to this repository
- Setup environment: `uv venv && uv pip install -r pyproject.toml && uv pip install cryptography && source .venv/bin/activate`
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

#### Arc Browser
- **macOS**: `~/Library/Application Support/Arc/User Data/Default/History`

**Note**: Arc is currently only available on macOS.

#### Opera
- **Windows**: `%APPDATA%\Opera Software\Opera Stable\History`
- **macOS**: `~/Library/Application Support/com.operasoftware.Opera/Default/History`
- **Linux**: `~/.config/opera/Default/History`

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

### DuckDuckGo Browser

DuckDuckGo is supported on macOS only and uses encrypted storage:
- **macOS**: `~/Library/Containers/com.duckduckgo.mobile.ios/Data/Library/Application Support/Database.sqlite`

**Important**: DuckDuckGo stores history in encrypted format. This server:
- Retrieves the encryption key from macOS Keychain (service: "DuckDuckGo Privacy Browser Encryption Key v2")
- Decrypts URLs and titles using ChaCha20-Poly1305 encryption
- Displays additional privacy metrics like trackers blocked per site

**Permissions**: Similar to Safari, DuckDuckGo may require Full Disk Access permissions on macOS. Follow the same steps as Safari if you encounter permission errors.

**Unique Features**: When querying DuckDuckGo history, you'll also see:
- Number of trackers blocked per site
- All standard browsing history information (visits, timestamps, etc.)

The server automatically detects your operating system and uses the appropriate path for each browser.

## Privacy Note

This server reads your local browser history databases in read-only mode. It creates temporary copies to avoid locking issues when browsers are running. For DuckDuckGo, encryption keys are retrieved from your macOS Keychain and used only to decrypt your local history data. No data is sent anywhere except to your local LLM chat application.
