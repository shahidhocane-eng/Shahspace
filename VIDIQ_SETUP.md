# vidIQ — local setup

vidIQ doesn't publish a general-purpose REST API. Its supported integration
path is the **vidIQ MCP server** (`https://mcp.vidiq.com/mcp`), which exposes
read-only YouTube channel/keyword/analytics data as MCP tools — available on
the vidIQ Max plan. This repo connects to it directly via `.mcp.json`, the
same way `openart` is registered there, instead of a hand-rolled Python
client.

## Prerequisites

- A vidIQ Max plan account.
- An MCP API key, generated at
  [app.vidiq.com/account/settings/mcp](https://app.vidiq.com/account/settings/mcp).
  Keys are scoped to MCP access only and can be revoked with one click.

## Configure credentials

Copy `.env.example` to `.env` and fill in:

```bash
VIDIQ_API_KEY=
```

Never commit `.env` — it's gitignored. `.mcp.json` reads `VIDIQ_API_KEY` from
the process environment via `${VIDIQ_API_KEY}` expansion, so export it in
your shell (or source `.env`) *before* launching Claude Code:

```bash
set -a; source .env; set +a
```

## Using it

Once `VIDIQ_API_KEY` is set and Claude Code (re)starts in this repo, the
`vidiq` MCP server in `.mcp.json` connects automatically and its tools
(channel stats, keyword/competitor research, etc.) become available directly
in the session — no separate client script needed. Run `/mcp` inside Claude
Code to confirm the `vidiq` server shows as connected.
