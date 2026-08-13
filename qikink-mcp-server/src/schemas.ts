import { z } from "zod";

export const DesignSchema = z
  .object({
    design_code: z.string().describe("Identifier of the design asset in your Qikink design library"),
    width_inches: z.string().default("").describe("Print width in inches, or empty string to use the default"),
    height_inches: z.string().default("").describe("Print height in inches, or empty string to use the default"),
    placement_sku: z.string().describe("Placement code, e.g. 'fr' for front, 'bk' for back"),
    design_link: z.string().url().describe("Publicly reachable URL of the print-ready design file"),
    mockup_link: z.string().url().describe("Publicly reachable URL of the mockup preview image"),
  })
  .strict();

export const LineItemSchema = z
  .object({
    search_from_my_products: z
      .number()
      .int()
      .default(0)
      .describe("Set to 1 to resolve the SKU from your saved product catalog, 0 otherwise"),
    quantity: z.string().describe("Quantity as a string, e.g. \"1\""),
    print_type_id: z.number().int().describe("Qikink print type ID for this line item"),
    price: z.string().describe("Unit price as a string, e.g. \"499\""),
    sku: z.string().describe("Product variant SKU, e.g. \"MVnHs-Wh-S\" (style-color-size)"),
    designs: z.array(DesignSchema).min(1).describe("Design(s) to print on this item"),
  })
  .strict();

export const ShippingAddressSchema = z
  .object({
    first_name: z.string(),
    last_name: z.string(),
    address1: z.string(),
    phone: z.string(),
    email: z.string(),
    city: z.string(),
    zip: z.string(),
    province: z.string(),
    country_code: z.string().length(2).describe("ISO 3166-1 alpha-2 country code, e.g. \"IN\""),
  })
  .strict();

export const CreateOrderInputSchema = z
  .object({
    order_number: z.string().min(1).describe("Your own unique order reference"),
    total_order_value: z.string().describe("Order total as a string, e.g. \"499\""),
    line_items: z.array(LineItemSchema).min(1),
    shipping_address: ShippingAddressSchema,
    gateway: z.enum(["COD", "PREPAID"]).default("COD").describe("Payment gateway for this order"),
    qikink_shipping: z
      .enum(["0", "1"])
      .default("1")
      .describe("\"1\" to have Qikink handle shipping, \"0\" if you ship it yourself"),
  })
  .strict();

export type CreateOrderInput = z.infer<typeof CreateOrderInputSchema>;

export const RawRequestInputSchema = z
  .object({
    method: z.enum(["GET", "POST", "PUT", "DELETE"]).describe("HTTP method for the Qikink API call"),
    path: z
      .string()
      .min(1)
      .describe("API path starting with \"/\", e.g. \"/api/order_status\" (relative to the sandbox/live base URL)"),
    body: z.record(z.unknown()).optional().describe("JSON body for POST/PUT requests"),
    query: z.record(z.unknown()).optional().describe("Query string parameters for GET/DELETE requests"),
  })
  .strict();

export type RawRequestInput = z.infer<typeof RawRequestInputSchema>;

export const CheckConnectionInputSchema = z.object({}).strict();
