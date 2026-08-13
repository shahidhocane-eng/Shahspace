"""
Minimal client for the Qikink API (Print on Demand / Dropshipping).

Qikink's auth flow: exchange a ClientId + client_secret for a bearer
access token via POST /api/token, then send that token on subsequent
requests.

Credentials are read from environment variables only:
  QIKINK_CLIENT_ID       Qikink ClientId
  QIKINK_CLIENT_SECRET   Qikink client_secret
  QIKINK_ENV             "sandbox" (default) or "live"

Never hardcode credentials in source. Put them in a local `.env` file
(see `.env.example`) and load it with a tool like python-dotenv, or
export them in your shell before running scripts that use this client.

Only the token endpoint's request/response shape is confirmed here.
Qikink's order/product endpoint paths and payload fields live in a
private Postman collection (requires a Qikink account to view) that
wasn't reachable when this client was written — verify exact
paths/fields there before relying on `request()` for order creation.
"""

import os

import requests

BASE_URLS = {
    "sandbox": "https://sandbox.qikink.com",
    "live": "https://api.qikink.com",
}


class QikinkAPIError(RuntimeError):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Qikink API error {status_code}: {payload}")


class QikinkClient:
    def __init__(self, client_id=None, client_secret=None, env=None, timeout=10):
        self.client_id = client_id or os.environ.get("QIKINK_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("QIKINK_CLIENT_SECRET")
        self.env = env or os.environ.get("QIKINK_ENV", "sandbox")
        if self.env not in BASE_URLS:
            raise ValueError(f"QIKINK_ENV must be one of {list(BASE_URLS)}, got {self.env!r}")
        self.base_url = BASE_URLS[self.env]
        self.timeout = timeout
        self._session = requests.Session()
        self._access_token = None

    def authenticate(self):
        """Exchange ClientId + client_secret for an access token. Returns the token."""
        if not self.client_id or not self.client_secret:
            raise EnvironmentError(
                "QIKINK_CLIENT_ID / QIKINK_CLIENT_SECRET are not set. "
                "Export them or add them to a local .env file."
            )
        response = self._session.post(
            f"{self.base_url}/api/token",
            data={"ClientId": self.client_id, "client_secret": self.client_secret},
            timeout=self.timeout,
        )
        if not response.ok:
            raise QikinkAPIError(response.status_code, response.text)
        body = response.json()
        token = body.get("Accesstoken") or body.get("access_token") or body.get("token")
        if not token:
            raise QikinkAPIError(response.status_code, f"No access token in response: {body}")
        self._access_token = token
        return token

    @property
    def access_token(self):
        if not self._access_token:
            self.authenticate()
        return self._access_token

    def request(self, method, path, **kwargs):
        """
        Authenticated request against any Qikink endpoint.

        Verify the exact path and payload shape against your Qikink Postman
        collection first — only /api/token is confirmed by this client.
        """
        headers = kwargs.pop("headers", {})
        headers.update({"ClientId": self.client_id, "Accesstoken": self.access_token})
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        response = self._session.request(
            method, url, headers=headers, timeout=self.timeout, **kwargs
        )
        if response.status_code == 401 and self._access_token:
            self._access_token = None
            headers["Accesstoken"] = self.access_token
            response = self._session.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
        if not response.ok:
            raise QikinkAPIError(response.status_code, response.text)
        return response.json()
