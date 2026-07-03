"""
Minimal client for the WazirX REST API (v2).

Credentials are read from environment variables only:
  WAZIRX_API_KEY
  WAZIRX_API_SECRET

Never hardcode the key/secret in source. Put them in a local `.env`
file (see `.env.example`) and load it with a tool like python-dotenv,
or export them in your shell before running scripts that use this
client.
"""

import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

import requests

BASE_URL = "https://api.wazirx.com/sapi/v1"


class WazirxAPIError(RuntimeError):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"WazirX API error {status_code}: {payload}")


class WazirxClient:
    def __init__(self, api_key=None, api_secret=None, base_url=BASE_URL, timeout=10):
        self.api_key = api_key or os.environ.get("WAZIRX_API_KEY")
        self.api_secret = api_secret or os.environ.get("WAZIRX_API_SECRET")
        self.base_url = base_url
        self.timeout = timeout
        self._session = requests.Session()

    def _signed_params(self, params=None):
        if not self.api_key or not self.api_secret:
            raise EnvironmentError(
                "WAZIRX_API_KEY / WAZIRX_API_SECRET are not set. "
                "Export them or add them to a local .env file."
            )
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method, path, params=None, signed=False):
        url = f"{self.base_url}{path}"
        headers = {}
        if signed:
            params = self._signed_params(params)
            headers["X-Api-Key"] = self.api_key
        response = self._session.request(
            method, url, params=params, headers=headers, timeout=self.timeout
        )
        if not response.ok:
            raise WazirxAPIError(response.status_code, response.text)
        return response.json()

    # -- public endpoints (no credentials required) --

    def ping(self):
        return self._request("GET", "/ping")

    def system_status(self):
        return self._request("GET", "/systemStatus")

    def exchange_info(self):
        return self._request("GET", "/exchangeInfo")

    def tickers(self):
        return self._request("GET", "/tickers/24hr")

    def ticker(self, symbol):
        return self._request("GET", "/ticker/24hr", params={"symbol": symbol})

    def depth(self, symbol, limit=50):
        return self._request("GET", "/depth", params={"symbol": symbol, "limit": limit})

    # -- signed endpoints (require API key + secret) --

    def account(self):
        """Account balances. Requires at least read-only key permission."""
        return self._request("GET", "/account", signed=True)

    def open_orders(self, symbol=None):
        params = {"symbol": symbol} if symbol else None
        return self._request("GET", "/openOrders", params=params, signed=True)

    def all_orders(self, symbol, limit=500):
        return self._request(
            "GET", "/allOrders", params={"symbol": symbol, "limit": limit}, signed=True
        )

    def create_order(self, symbol, side, order_type, quantity, price=None):
        """Places an order. Requires a key with SPOT Trade permission enabled."""
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if price is not None:
            params["price"] = price
        return self._request("POST", "/order", params=params, signed=True)

    def cancel_order(self, symbol, order_id):
        return self._request(
            "DELETE", "/order", params={"symbol": symbol, "orderId": order_id}, signed=True
        )
