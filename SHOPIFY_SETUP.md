# Shopify — local setup

`shopify/` holds two connectors, in the same style as `wazirx/`:

- `ShopifyClient` (`client.py`) — Admin API (REST + GraphQL), for
  store-management operations (products, orders, customers). Requires a
  store-scoped Admin API access token.
- `StorefrontClient` (`storefront.py`) — Storefront API (GraphQL only),
  for public-facing storefront data (products, collections, cart,
  checkout). Requires a Storefront access token, which is safe to expose
  client-side.

`shopify_connect.py` and `storefront_connect.py` verify each connection
and print basic status.

## Prerequisites

- Python 3.9+ with `requests` installed (`pip install -r requirements.txt`)
- Node.js 18+ and the Shopify CLI, for theme/app development and to generate
  a store-scoped access token:

  ```bash
  npm install -g @shopify/cli@latest
  shopify version
  ```

- A Shopify store, plus tokens for whichever connector(s) you use:
  - **Admin API token** — via the Shopify CLI (`shopify app dev` /
    `shopify auth login` when working inside an app project), or by
    creating a custom app in the store's admin under
    **Settings > Apps and sales channels > Develop apps**, installing it,
    and copying its Admin API access token.
  - **Storefront API token** — in the same custom app, enable Storefront
    API scopes and copy the generated Storefront access token (or use the
    token from the store's "Headless" sales channel, if enabled).

## Configure credentials

Copy `.env.example` to `.env` and fill in:

```bash
SHOPIFY_STORE_DOMAIN=my-shop.myshopify.com
SHOPIFY_ACCESS_TOKEN=
SHOPIFY_API_VERSION=2024-10                # optional, defaults to this
SHOPIFY_STOREFRONT_ACCESS_TOKEN=
SHOPIFY_STOREFRONT_API_VERSION=2024-10     # optional, defaults to this
```

Never commit `.env` — it's gitignored. Load it with a tool like
`python-dotenv`, or export the variables in your shell before running
scripts that use the connector.

## Verify the connections

```bash
python shopify_connect.py       # Admin API: shop name, plan, currency, timezone, 5 products
python storefront_connect.py    # Storefront API: shop name, storefront URL, 5 products
```

## Using the clients directly

```python
from shopify import ShopifyClient, StorefrontClient

admin = ShopifyClient()
shop = admin.shop()
products = admin.products(limit=10)
# raw GraphQL escape hatch for anything not covered by the REST helpers
result = admin.graphql("{ shop { name } }")

storefront = StorefrontClient()
info = storefront.shop_info()
products = storefront.products(first=10)
product = storefront.product_by_handle("some-product-handle")
cart = storefront.create_cart(merchandise_id=product["variants"]["edges"][0]["node"]["id"])
print(cart["cart"]["checkoutUrl"])
```
