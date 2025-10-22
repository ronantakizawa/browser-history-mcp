# brave-history-mcp

Access and search your Brave browser history through an MCP server for LLM chat apps.

## Features

This MCP server provides three tools to interact with your Brave browser history:

- **search_history**: Search for specific terms in URLs and page titles
- **get_recent_history**: Get the most recent browsing history entries
- **get_most_visited**: Get your most frequently visited sites

## Usage

Example prompts:
- "Search my Brave history for 'python tutorials'"
- "Show me my 20 most recent browsing history entries"
- "What are my top 10 most visited sites?"

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
"Brave Browser History Service": {
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

## Platform Support

This server supports:
- **Windows**: `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\History`
- **macOS**: `~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History`
- **Linux**: `~/.config/BraveSoftware/Brave-Browser/Default/History`

The server automatically detects your operating system and uses the appropriate path.

## Privacy Note

This server reads your local Brave browser history database in read-only mode. It creates temporary copies to avoid locking issues when Brave is running. No data is sent anywhere except to your local LLM chat application.
