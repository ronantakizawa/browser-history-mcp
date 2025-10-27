# search-history-mcp

<img width="1024" height="512" alt="browser-histo (2)" src="https://github.com/user-attachments/assets/9bd134ed-b400-45ae-8134-9c3f854989b3" />



Access and search your browser search history (Brave, Chrome, Firefox, Safari, Edge, Arc, Opera, DuckDuckGo) through an MCP server for LLM chat apps.

Supported for MacOS, Windows, and Linux.

## Features

This MCP server provides three tools to interact with your search history:

- **search_history**: Search for specific terms in URLs and page titles
- **get_recent_history**: Get the most recent browsing history entries
- **get_most_visited**: Get your most frequently visited sites

## Install

- Install [Claude Desktop](https://claude.ai/download)
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Clone or navigate to this repository
- Setup environment: `uv venv && uv pip install -r pyproject.toml && uv pip install cryptography && source .venv/bin/activate`
- Install the MCP server: `fastmcp install claude-desktop mcp_server.py`
- Restart Claude Desktop

## Privacy Note

This server reads your local browser history databases in read-only mode. It creates temporary copies to avoid locking issues when browsers are running. For DuckDuckGo on macOS, encryption keys are retrieved from your macOS Keychain and used only to decrypt your local history data. No data is sent anywhere except to your local LLM chat application.

**Browser Support**: Brave, Chrome, Edge, Opera, Arc, and DuckDuckGo are supported on Windows, macOS, and Linux. Firefox is supported on all platforms. Safari is macOS-only.

Browser file paths may have to be manually configured depending on your file structures. 
