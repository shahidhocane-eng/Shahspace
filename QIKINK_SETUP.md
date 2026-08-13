# Qikink — local setup

`qikink/` is a minimal connector for the [Qikink](https://qikink.com) Print
on Demand / Dropshipping API, in the same style as `wazirx/` and `shopify/`.

**Scope note:** `POST /api/token` and `POST /api/order/create` are
confirmed against documented example payloads (see `create_order()` below).
Other endpoints (order status, product catalog, etc.) live in a private
Postman collection that requires a Qikink account to view, and weren't
reachable from this environment when the connector was built.
`QikinkClient.request()` is a generic authenticated-request helper for
those — confirm exact paths and payload shapes in your own Postman
collection (dashboard.qikink.com → Integration → Custom API) first.

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
client.authenticate()  # optional — auth also happens lazily on first request

order = client.create_order(
    order_number="api1",
    total_order_value="1",
    line_items=[
        {
            "search_from_my_products": 0,
            "quantity": "1",
            "print_type_id": 1,
            "price": "1",
            "sku": "MVnHs-Wh-S",
            "designs": [
                {
                    "design_code": "iPhoneXR",
                    "width_inches": "",
                    "height_inches": "",
                    "placement_sku": "fr",
                    "design_link": "https://sgp1.digitaloceanspaces.com/cdn.qikink.com/erp2/assets/designs/83/1696668376.jpg",
                    "mockup_link": "https://sgp1.digitaloceanspaces.com/cdn.qikink.com/erp2/assets/designs/83/1696668376.jpg",
                }
            ],
        }
    ],
    shipping_address={
        "first_name": "sdf",
        "last_name": "ds",
        "address1": "sdsfsdf3",
        "phone": "fasda",
        "email": "adf",
        "city": "sda",
        "zip": "sdfs",
        "province": "sdfa",
        "country_code": "IN",
    },
)

# generic authenticated call for any other endpoint, once you've confirmed
# the real path/payload against your Postman collection
data = client.request("GET", "/api/order_status", params={"order_number": "api1"})
```
