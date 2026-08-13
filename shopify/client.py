"""
Minimal client for the Shopify Admin API (REST + GraphQL).

Credentials are read from environment variables only:
  SHOPIFY_STORE_DOMAIN   e.g. "my-shop.myshopify.com"
  SHOPIFY_ACCESS_TOKEN   Admin API access token (custom app or CLI-generated)
  SHOPIFY_API_VERSION    optional, defaults to DEFAULT_API_VERSION below

Never hardcode the token in source. Put it in a local `.env` file (see
`.env.example`) and load it with a tool like python-dotenv, or export
it in your shell before running scripts that use this client.
"""

import os

import requests

DEFAULT_API_VERSION = "2024-10"


class ShopifyAPIError(RuntimeError):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Shopify API error {status_code}: {payload}")


class ShopifyClient:
    def __init__(self, store_domain=None, access_token=None, api_version=None, timeout=10):
        self.store_domain = store_domain or os.environ.get("SHOPIFY_STORE_DOMAIN")
        self.access_token = access_token or os.environ.get("SHOPIFY_ACCESS_TOKEN")
        self.api_version = api_version or os.environ.get("SHOPIFY_API_VERSION", DEFAULT_API_VERSION)
        self.timeout = timeout
        self._session = requests.Session()

    def _base_url(self):
        if not self.store_domain:
            raise EnvironmentError(
                "SHOPIFY_STORE_DOMAIN is not set. "
                "Export it or add it to a local .env file."
            )
        return f"https://{self.store_domain}/admin/api/{self.api_version}"

    def _request(self, method, path, params=None, json=None):
        if not self.access_token:
            raise EnvironmentError(
                "SHOPIFY_ACCESS_TOKEN is not set. "
                "Export it or add it to a local .env file."
            )
        url = f"{self._base_url()}{path}"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }
        response = self._session.request(
            method, url, params=params, json=json, headers=headers, timeout=self.timeout
        )
        if not response.ok:
            raise ShopifyAPIError(response.status_code, response.text)
        return response.json()

    # -- REST endpoints --

    def shop(self):
        """Basic info about the connected shop."""
        return self._request("GET", "/shop.json")["shop"]

    def products(self, limit=50):
        return self._request("GET", "/products.json", params={"limit": limit})["products"]

    def product(self, product_id):
        return self._request("GET", f"/products/{product_id}.json")["product"]

    def orders(self, limit=50, status="any"):
        return self._request(
            "GET", "/orders.json", params={"limit": limit, "status": status}
        )["orders"]

    def order(self, order_id):
        return self._request("GET", f"/orders/{order_id}.json")["order"]

    def customers(self, limit=50):
        return self._request("GET", "/customers.json", params={"limit": limit})["customers"]

    # -- GraphQL escape hatch --

    def graphql(self, query, variables=None):
        """Run a raw GraphQL query/mutation against the Admin API."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        return self._request("POST", "/graphql.json", json=payload)
