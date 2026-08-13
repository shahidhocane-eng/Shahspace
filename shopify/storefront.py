"""
Minimal client for the Shopify Storefront API (GraphQL only).

This is the public-facing, customer-scoped API (products, collections,
cart, checkout) — distinct from the Admin API in client.py. It uses a
Storefront access token, which is safe to expose to a browser/app since
it only grants read access to published storefront data (plus cart
mutations).

Credentials are read from environment variables only:
  SHOPIFY_STORE_DOMAIN              e.g. "my-shop.myshopify.com"
  SHOPIFY_STOREFRONT_ACCESS_TOKEN   Storefront API access token
  SHOPIFY_STOREFRONT_API_VERSION    optional, defaults to DEFAULT_API_VERSION

Never hardcode the token in source. Put it in a local `.env` file (see
`.env.example`) and load it with a tool like python-dotenv, or export
it in your shell before running scripts that use this client.
"""

import os

import requests

DEFAULT_API_VERSION = "2024-10"


class StorefrontAPIError(RuntimeError):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Shopify Storefront API error {status_code}: {payload}")


class StorefrontClient:
    def __init__(self, store_domain=None, access_token=None, api_version=None, timeout=10):
        self.store_domain = store_domain or os.environ.get("SHOPIFY_STORE_DOMAIN")
        self.access_token = access_token or os.environ.get("SHOPIFY_STOREFRONT_ACCESS_TOKEN")
        self.api_version = api_version or os.environ.get(
            "SHOPIFY_STOREFRONT_API_VERSION", DEFAULT_API_VERSION
        )
        self.timeout = timeout
        self._session = requests.Session()

    def _url(self):
        if not self.store_domain:
            raise EnvironmentError(
                "SHOPIFY_STORE_DOMAIN is not set. "
                "Export it or add it to a local .env file."
            )
        return f"https://{self.store_domain}/api/{self.api_version}/graphql.json"

    def graphql(self, query, variables=None):
        """Run a GraphQL query/mutation against the Storefront API."""
        if not self.access_token:
            raise EnvironmentError(
                "SHOPIFY_STOREFRONT_ACCESS_TOKEN is not set. "
                "Export it or add it to a local .env file."
            )
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        headers = {
            "X-Shopify-Storefront-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }
        response = self._session.post(
            self._url(), json=payload, headers=headers, timeout=self.timeout
        )
        if not response.ok:
            raise StorefrontAPIError(response.status_code, response.text)
        body = response.json()
        if "errors" in body:
            raise StorefrontAPIError(response.status_code, body["errors"])
        return body["data"]

    # -- convenience helpers built on graphql() --

    def shop_info(self):
        data = self.graphql("{ shop { name primaryDomain { url } } }")
        return data["shop"]

    def products(self, first=10):
        query = """
        query Products($first: Int!) {
          products(first: $first) {
            edges { node { id title handle } }
          }
        }
        """
        data = self.graphql(query, {"first": first})
        return [edge["node"] for edge in data["products"]["edges"]]

    def product_by_handle(self, handle):
        query = """
        query ProductByHandle($handle: String!) {
          product(handle: $handle) {
            id
            title
            description
            variants(first: 10) {
              edges { node { id title price { amount currencyCode } } }
            }
          }
        }
        """
        data = self.graphql(query, {"handle": handle})
        return data["product"]

    def create_cart(self, merchandise_id=None, quantity=1):
        """Create a cart, optionally with one line item. Returns the cart (with checkoutUrl)."""
        query = """
        mutation CartCreate($lines: [CartLineInput!]) {
          cartCreate(input: { lines: $lines }) {
            cart { id checkoutUrl }
            userErrors { field message }
          }
        }
        """
        lines = [{"merchandiseId": merchandise_id, "quantity": quantity}] if merchandise_id else []
        data = self.graphql(query, {"lines": lines})
        return data["cartCreate"]
