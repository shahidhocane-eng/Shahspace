"""
Groww MCP Server — exposes Groww trading account to Claude via MCP tools.

Required environment variable:
  GROWW_API_KEY  — your Groww Trading API key (from Groww app > Profile > Settings > Trading APIs)
"""

import os
import json
import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

try:
    from growwapi import GrowwAPI
except ImportError:
    raise SystemExit("growwapi not installed. Run: pip install growwapi")

API_KEY = os.environ.get("GROWW_API_KEY", "")
if not API_KEY:
    raise SystemExit("GROWW_API_KEY environment variable is not set.")

client = GrowwAPI(API_KEY)

server = Server("groww-mcp")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data: Any) -> list[types.TextContent]:
    text = data if isinstance(data, str) else json.dumps(data, indent=2, default=str)
    return [types.TextContent(type="text", text=text)]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"ERROR: {msg}")]


def _exchange_symbol(exchange: str, trading_symbol: str) -> str:
    """Format expected by get_ltp: 'NSE_RELIANCE'"""
    return f"{exchange}_{trading_symbol}"


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_profile",
            description="Fetch the Groww account profile (name, email, trading status).",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_holdings",
            description="Fetch current DEMAT holdings (long-term stock positions) with quantity, average price, current value, and P&L.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_positions",
            description="Fetch intraday (MIS) and F&O positions for the current trading session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "segment": {
                        "type": "string",
                        "enum": ["CASH", "FNO"],
                        "description": "Filter by segment (optional; omit for all)",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_order_list",
            description="Retrieve orders (today's orders by default). Supports pagination.",
            inputSchema={
                "type": "object",
                "properties": {
                    "segment": {
                        "type": "string",
                        "enum": ["CASH", "FNO"],
                        "description": "Filter by segment (optional)",
                    },
                    "page": {"type": "integer", "default": 0},
                    "page_size": {"type": "integer", "default": 25},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_order_detail",
            description="Get detailed information about a specific order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "groww_order_id": {"type": "string", "description": "The Groww order ID"},
                    "segment": {
                        "type": "string",
                        "enum": ["CASH", "FNO"],
                        "description": "Segment the order belongs to",
                    },
                },
                "required": ["groww_order_id", "segment"],
            },
        ),
        types.Tool(
            name="place_order",
            description=(
                "Place a buy or sell equity/F&O order on Groww. "
                "Supports MARKET, LIMIT, SL, and SL_M order types. "
                "Always confirm intent with the user before executing."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "trading_symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g. RELIANCE, INFY, TCS)",
                    },
                    "quantity": {"type": "integer", "description": "Number of shares"},
                    "transaction_type": {
                        "type": "string",
                        "enum": ["BUY", "SELL"],
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["MARKET", "LIMIT", "SL", "SL_M"],
                    },
                    "product": {
                        "type": "string",
                        "enum": ["CNC", "MIS", "NRML"],
                        "description": "CNC=delivery, MIS=intraday, NRML=F&O carry-forward",
                    },
                    "exchange": {
                        "type": "string",
                        "enum": ["NSE", "BSE"],
                    },
                    "segment": {
                        "type": "string",
                        "enum": ["CASH", "FNO"],
                        "default": "CASH",
                    },
                    "validity": {
                        "type": "string",
                        "enum": ["DAY", "IOC", "GTC"],
                        "default": "DAY",
                    },
                    "price": {
                        "type": "number",
                        "description": "Limit price (required for LIMIT and SL orders)",
                    },
                    "trigger_price": {
                        "type": "number",
                        "description": "Trigger price (required for SL and SL_M orders)",
                    },
                },
                "required": [
                    "trading_symbol",
                    "quantity",
                    "transaction_type",
                    "order_type",
                    "product",
                    "exchange",
                ],
            },
        ),
        types.Tool(
            name="modify_order",
            description="Modify a pending order's quantity, price, or order type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "groww_order_id": {"type": "string"},
                    "segment": {"type": "string", "enum": ["CASH", "FNO"]},
                    "order_type": {
                        "type": "string",
                        "enum": ["MARKET", "LIMIT", "SL", "SL_M"],
                    },
                    "quantity": {"type": "integer"},
                    "price": {"type": "number"},
                    "trigger_price": {"type": "number"},
                },
                "required": ["groww_order_id", "segment", "order_type", "quantity"],
            },
        ),
        types.Tool(
            name="cancel_order",
            description="Cancel a pending order by its Groww order ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "groww_order_id": {"type": "string"},
                    "segment": {"type": "string", "enum": ["CASH", "FNO"]},
                },
                "required": ["groww_order_id", "segment"],
            },
        ),
        types.Tool(
            name="get_ltp",
            description="Get the Last Traded Price (LTP) for one or more instruments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of symbols e.g. ['RELIANCE', 'INFY']",
                    },
                    "exchange": {
                        "type": "string",
                        "enum": ["NSE", "BSE"],
                        "default": "NSE",
                    },
                    "segment": {
                        "type": "string",
                        "enum": ["CASH", "FNO"],
                        "default": "CASH",
                    },
                },
                "required": ["symbols"],
            },
        ),
        types.Tool(
            name="get_quote",
            description="Get a full live market quote (bid, ask, OHLC, volume, LTP, circuit limits) for a single stock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trading_symbol": {"type": "string", "description": "e.g. RELIANCE"},
                    "exchange": {"type": "string", "enum": ["NSE", "BSE"], "default": "NSE"},
                    "segment": {"type": "string", "enum": ["CASH", "FNO"], "default": "CASH"},
                },
                "required": ["trading_symbol"],
            },
        ),
        types.Tool(
            name="get_historical_data",
            description="Fetch historical OHLCV candle data for a stock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trading_symbol": {"type": "string"},
                    "exchange": {"type": "string", "enum": ["NSE", "BSE"], "default": "NSE"},
                    "segment": {"type": "string", "enum": ["CASH", "FNO"], "default": "CASH"},
                    "interval": {
                        "type": "string",
                        "enum": ["1minute", "2minute", "3minute", "5minute", "10minute",
                                 "15minute", "30minute", "1hour", "4hour", "1day", "1week", "1month"],
                        "default": "1day",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                },
                "required": ["trading_symbol", "start_date", "end_date"],
            },
        ),
        types.Tool(
            name="get_margin",
            description="Check available trading margin and buying power in the account.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_order_margin",
            description="Calculate the margin required before placing an order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trading_symbol": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "transaction_type": {"type": "string", "enum": ["BUY", "SELL"]},
                    "order_type": {"type": "string", "enum": ["MARKET", "LIMIT", "SL", "SL_M"]},
                    "product": {"type": "string", "enum": ["CNC", "MIS", "NRML"]},
                    "exchange": {"type": "string", "enum": ["NSE", "BSE"]},
                    "segment": {"type": "string", "enum": ["CASH", "FNO"], "default": "CASH"},
                    "price": {"type": "number"},
                    "trigger_price": {"type": "number"},
                },
                "required": ["trading_symbol", "quantity", "transaction_type",
                             "order_type", "product", "exchange"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "get_profile":
            return _ok(client.get_user_profile())

        elif name == "get_holdings":
            return _ok(client.get_holdings_for_user())

        elif name == "get_positions":
            return _ok(client.get_positions_for_user(segment=arguments.get("segment")))

        elif name == "get_order_list":
            return _ok(client.get_order_list(
                page=arguments.get("page", 0),
                page_size=arguments.get("page_size", 25),
                segment=arguments.get("segment"),
            ))

        elif name == "get_order_detail":
            return _ok(client.get_order_detail(
                segment=arguments["segment"],
                groww_order_id=arguments["groww_order_id"],
            ))

        elif name == "place_order":
            return _ok(client.place_order(
                validity=arguments.get("validity", GrowwAPI.VALIDITY_DAY),
                exchange=arguments["exchange"],
                order_type=arguments["order_type"],
                product=arguments["product"],
                quantity=arguments["quantity"],
                segment=arguments.get("segment", GrowwAPI.SEGMENT_CASH),
                trading_symbol=arguments["trading_symbol"],
                transaction_type=arguments["transaction_type"],
                price=arguments.get("price", 0.0),
                trigger_price=arguments.get("trigger_price"),
            ))

        elif name == "modify_order":
            return _ok(client.modify_order(
                order_type=arguments["order_type"],
                segment=arguments["segment"],
                groww_order_id=arguments["groww_order_id"],
                quantity=arguments["quantity"],
                price=arguments.get("price"),
                trigger_price=arguments.get("trigger_price"),
            ))

        elif name == "cancel_order":
            return _ok(client.cancel_order(
                groww_order_id=arguments["groww_order_id"],
                segment=arguments["segment"],
            ))

        elif name == "get_ltp":
            exchange = arguments.get("exchange", "NSE")
            segment = arguments.get("segment", "CASH")
            exchange_symbols = tuple(
                _exchange_symbol(exchange, sym) for sym in arguments["symbols"]
            )
            return _ok(client.get_ltp(
                exchange_trading_symbols=exchange_symbols,
                segment=segment,
            ))

        elif name == "get_quote":
            return _ok(client.get_quote(
                trading_symbol=arguments["trading_symbol"],
                exchange=arguments.get("exchange", "NSE"),
                segment=arguments.get("segment", "CASH"),
            ))

        elif name == "get_historical_data":
            return _ok(client.get_historical_candles(
                trading_symbol=arguments["trading_symbol"],
                exchange=arguments.get("exchange", "NSE"),
                segment=arguments.get("segment", "CASH"),
                interval=arguments.get("interval", GrowwAPI.CANDLE_INTERVAL_DAY),
                start_date=arguments["start_date"],
                end_date=arguments["end_date"],
            ))

        elif name == "get_margin":
            return _ok(client.get_available_margin_details())

        elif name == "get_order_margin":
            return _ok(client.get_order_margin_details(
                trading_symbol=arguments["trading_symbol"],
                quantity=arguments["quantity"],
                transaction_type=arguments["transaction_type"],
                order_type=arguments["order_type"],
                product=arguments["product"],
                exchange=arguments["exchange"],
                segment=arguments.get("segment", "CASH"),
                price=arguments.get("price", 0.0),
                trigger_price=arguments.get("trigger_price"),
            ))

        else:
            return _err(f"Unknown tool: {name}")

    except Exception as exc:
        return _err(str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
