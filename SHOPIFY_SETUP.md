# Shopify — local setup

`shopify/` is a minimal Admin API connector (REST + GraphQL), in the same
style as `wazirx/`. `shopify_connect.py` verifies the connection and prints
basic shop status.

## Prerequisites

- Python 3.9+ with `requests` installed (`pip install -r requirements.txt`)
- Node.js 18+ and the Shopify CLI, for theme/app development and to generate
  a store-scoped access token:

  ```bash
  npm install -g @shopify/cli@latest
  shopify version
  ```

- A Shopify store, plus an Admin API access token. Get one either:
  - via the Shopify CLI (`shopify app dev` / `shopify auth login` when working
    inside an app project), or
  - by creating a custom app in the store's admin under
    **Settings > Apps and sales channels > Develop apps**, installing it, and
    copying its Admin API access token.

## Configure credentials

Copy `.env.example` to `.env` and fill in:

```bash
SHOPIFY_STORE_DOMAIN=my-shop.myshopify.com
SHOPIFY_ACCESS_TOKEN=
SHOPIFY_API_VERSION=2024-10   # optional, defaults to this
```

Never commit `.env` — it's gitignored. Load it with a tool like
`python-dotenv`, or export the variables in your shell before running
scripts that use the connector.

## Verify the connection

```bash
python shopify_connect.py
```

This prints the shop name, plan, currency, and timezone, then lists up to
5 products.

## Using the client directly

```python
from shopify import ShopifyClient

client = ShopifyClient()
shop = client.shop()
products = client.products(limit=10)

# raw GraphQL escape hatch for anything not covered by the REST helpers
result = client.graphql("{ shop { name } }")
```
