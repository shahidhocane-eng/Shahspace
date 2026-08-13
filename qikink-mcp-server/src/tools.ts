import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { QikinkClient } from "./qikink-client.js";
import { describeError } from "./errors.js";
import {
  CreateOrderInputSchema,
  RawRequestInputSchema,
  CheckConnectionInputSchema,
  type CreateOrderInput,
  type RawRequestInput,
} from "./schemas.js";

const CHARACTER_LIMIT = 25000;

function truncate(text: string): string {
  if (text.length <= CHARACTER_LIMIT) return text;
  return (
    text.slice(0, CHARACTER_LIMIT) +
    `\n\n[truncated: response was ${text.length} characters, showing first ${CHARACTER_LIMIT}]`
  );
}

export function registerTools(server: McpServer, client: QikinkClient): void {
  server.registerTool(
    "qikink_check_connection",
    {
      title: "Check Qikink Connection",
      description: `Verify Qikink API credentials by exchanging them for an access token.

Does not place an order or modify any data. Use this first to confirm QIKINK_CLIENT_ID / QIKINK_CLIENT_SECRET / QIKINK_ENV are configured correctly before calling other Qikink tools.

Returns:
  { "connected": true, "environment": "sandbox" | "live", "base_url": string }`,
      inputSchema: CheckConnectionInputSchema.shape,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
      },
    },
    async () => {
      try {
        await client.authenticate();
        const output = { connected: true, environment: client.env, base_url: client.baseUrl };
        return {
          content: [{ type: "text", text: JSON.stringify(output, null, 2) }],
          structuredContent: output,
        };
      } catch (error) {
        return { isError: true, content: [{ type: "text", text: describeError(error) }] };
      }
    }
  );

  server.registerTool(
    "qikink_create_order",
    {
      title: "Create Qikink Order",
      description: `Create a Print on Demand / Dropshipping order via POST /api/order/create.

This places a real order in whichever environment QIKINK_ENV is set to (sandbox is safe to use for testing; live creates a real, billable order). Not idempotent — calling it twice with the same order_number may create a duplicate depending on your account settings, or be rejected by Qikink as a duplicate; check with qikink_request first if unsure.

Args:
  - order_number (string): Your own unique order reference
  - total_order_value (string): Order total, e.g. "499"
  - line_items (array): Each item needs quantity, print_type_id, price, sku, and at least one design (design_code, placement_sku, design_link, mockup_link)
  - shipping_address (object): first_name, last_name, address1, phone, email, city, zip, province, country_code
  - gateway ("COD" | "PREPAID", default "COD")
  - qikink_shipping ("0" | "1", default "1")

Returns: the raw Qikink order/create response (order id and status on success).

Error Handling:
  - Returns an error if credentials are invalid or the payload is rejected by Qikink (e.g. unknown sku or print_type_id) — the error message includes Qikink's response body.`,
      inputSchema: CreateOrderInputSchema.shape,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
      },
    },
    async (params: CreateOrderInput) => {
      try {
        const result = await client.createOrder(params);
        const text = truncate(JSON.stringify(result, null, 2));
        return {
          content: [{ type: "text", text }],
          structuredContent: result as Record<string, unknown>,
        };
      } catch (error) {
        return { isError: true, content: [{ type: "text", text: describeError(error) }] };
      }
    }
  );

  server.registerTool(
    "qikink_request",
    {
      title: "Raw Qikink API Request",
      description: `Make an authenticated request to any Qikink Admin API endpoint not covered by a dedicated tool (e.g. order status lookups, product catalog).

Only /api/token and /api/order/create are independently confirmed by this server (see qikink_create_order). Other endpoint paths and payload shapes must be sourced from your own Qikink Postman collection (dashboard.qikink.com -> Integration -> Custom API) — this tool does not validate them.

Args:
  - method ("GET" | "POST" | "PUT" | "DELETE")
  - path (string): API path starting with "/", e.g. "/api/order_status"
  - body (object, optional): JSON body for POST/PUT
  - query (object, optional): query string parameters for GET/DELETE

Returns: the raw JSON response from Qikink.

Error Handling:
  - Returns "Error: Qikink endpoint not found" (404) if the path is wrong — double-check it against your Postman collection.`,
      inputSchema: RawRequestInputSchema.shape,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        idempotentHint: false,
        openWorldHint: true,
      },
    },
    async (params: RawRequestInput) => {
      try {
        const result = await client.request(params.method, params.path, {
          json: params.body,
          params: params.query,
        });
        const text = truncate(JSON.stringify(result, null, 2));
        return {
          content: [{ type: "text", text }],
          structuredContent: (typeof result === "object" && result !== null
            ? (result as Record<string, unknown>)
            : { result }),
        };
      } catch (error) {
        return { isError: true, content: [{ type: "text", text: describeError(error) }] };
      }
    }
  );
}
