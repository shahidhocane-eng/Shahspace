# Qikink — local setup

`qikink/` is a minimal connector for the [Qikink](https://qikink.com) Print
on Demand / Dropshipping API, in the same style as `wazirx/` and `shopify/`.

**Scope note:** only the token endpoint (`POST /api/token`) is verified.
Qikink's order/product endpoints live in a private Postman collection that
requires a Qikink account to view, and wasn't reachable from this
environment when the connector was built. `QikinkClient.request()` is a
generic authenticated-request helper — confirm exact paths and payload
shapes in your own Postman collection (dashboard.qikink.com → Integration →
Custom API) before relying on it for orders.

## Prerequisites

- Python 3.9+ with `requests` installed (`pip install -r requirements.txt`)
- A Qikink account with API access enabled, and a `ClientId` +
  `client_secret` pair (dashboard.qikink.com → Integration → Custom API)

## Configure credentials

Copy `.env.example` to `.env` and fill in:

```bash
QIKINK_CLIENT_ID=
QIKINK_CLIENT_SECRET=
QIKINK_ENV=sandbox   # or "live" for https://api.qikink.com
```

Never commit `.env` — it's gitignored.

## Verify the connection

```bash
python qikink_connect.py
```

Exchanges your credentials for an access token against
`https://sandbox.qikink.com/api/token` (or the live endpoint, if
`QIKINK_ENV=live`) and prints a truncated token on success.

## Using the client directly

```python
from qikink import QikinkClient

client = QikinkClient()
client.authenticate()  # optional — request() calls this lazily on first use

# generic authenticated call once you've confirmed the real path/payload
data = client.request("POST", "/api/order/create", json={...})
```
