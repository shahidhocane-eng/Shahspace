# qikink-mcp-server

An MCP server for the [Qikink](https://qikink.com) Print on Demand /
Dropshipping API. Exposes:

- `qikink_check_connection` — verify credentials (read-only)
- `qikink_create_order` — `POST /api/order/create`, confirmed against a
  documented example payload
- `qikink_request` — generic authenticated request for any other Qikink
  endpoint (order status, product catalog, etc.), whose exact paths/payloads
  aren't verified by this server — confirm them in your own Qikink Postman
  collection first (dashboard.qikink.com → Integration → Custom API)

This is a sibling to the plain Python `qikink/` client library elsewhere in
this repo. That one is a library you import into scripts; this one is a
standalone server you deploy so it can be added as a Connector in Claude
(or any other MCP client) without running any code yourself.

## Configuration

Environment variables:

| Variable                | Required | Default     | Notes                                   |
|--------------------------|----------|-------------|------------------------------------------|
| `QIKINK_CLIENT_ID`       | yes      | —           | Qikink `ClientId`                        |
| `QIKINK_CLIENT_SECRET`   | yes      | —           | Qikink `client_secret`                   |
| `QIKINK_ENV`             | no       | `sandbox`   | `sandbox` or `live`                      |
| `TRANSPORT`              | no       | `stdio`     | `stdio` or `http`                        |
| `PORT`                   | no       | `3000`      | Only used when `TRANSPORT=http`          |

## Local development

```bash
npm install
npm run build
npm start                       # stdio, for local MCP clients (e.g. Claude Desktop config)
TRANSPORT=http npm start        # streamable HTTP on :3000, for remote/connector use
```

Or without building first: `npm run dev` (stdio only, auto-reloads on change).

## Deploying as a Connector

To show up in Claude's Connectors list, this needs to run somewhere
reachable over HTTPS with `TRANSPORT=http`. Any Node-capable host works —
Render, Fly.io, Railway, a VPS behind a reverse proxy, etc. In broad strokes:

1. Deploy this directory (it's self-contained: `npm install && npm run build && npm start`
   with `TRANSPORT=http` and the `QIKINK_*` env vars set on the host).
2. Put it behind HTTPS (most platforms do this for you; if self-hosting,
   terminate TLS with a reverse proxy).
3. Confirm `https://<your-host>/mcp` responds to an MCP `initialize` request
   (see the smoke test below).
4. In claude.ai, go to **Settings → Connectors → Add custom connector** and
   enter that URL (with `/mcp` on the end) as the Remote MCP server URL.

### Deploying on Render

This repo is a monorepo (this server is one subdirectory among several
unrelated projects), so use Render's manual **Web Service** flow rather
than Blueprint auto-detect, so you can point it at the right subfolder:

1. [render.com](https://render.com) → **New +** → **Web Service** → connect
   the `shahidhocane-eng/Shahspace` GitHub repo.
2. **Root Directory**: `qikink-mcp-server`
3. **Runtime**: Node
4. **Build Command**: `npm install && npm run build`
5. **Start Command**: `npm start`
6. **Environment variables**:
   - `TRANSPORT` = `http`
   - `QIKINK_ENV` = `sandbox` (or `live`)
   - `QIKINK_CLIENT_ID` = *(your Qikink ClientId)*
   - `QIKINK_CLIENT_SECRET` = *(your Qikink client_secret)*
   - Render sets `PORT` itself — leave it unset here, the server reads it automatically.
7. Deploy. Render gives you a URL like `https://qikink-mcp-server.onrender.com`
   — the connector URL is that plus `/mcp`.

`render.yaml` in this directory documents the same config as
infrastructure-as-code, for reference or if you use Render's CLI/Blueprints
instead of the dashboard.

**Free tier note:** Render's free web services spin down after ~15 minutes
idle and take a few seconds to wake on the next request — the first tool
call after a quiet period may time out or feel slow. Fine for testing; for
reliable use you'd want a paid instance type (or a different platform).

**Smoke test after deploying:**

```bash
curl -s -X POST https://<your-host>/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke-test","version":"0.0.1"}}}'
```

A healthy server responds with a `result.serverInfo.name` of
`"qikink-mcp-server"`.

**Security note:** this server has no built-in authentication of its own —
anyone who can reach the URL can call your Qikink account's tools. Put it
behind your host's access controls (e.g. a private network, an API gateway
with auth, or IP allowlisting) unless your platform's MCP connector flow
adds its own auth in front of it.

## Scope note

Only `/api/token` and `/api/order/create` are confirmed against documented
example payloads. Everything else goes through `qikink_request`, which is a
thin authenticated pass-through — verify paths and payload shapes in your
own Qikink Postman collection before relying on it.
