import { QikinkApiError } from "./qikink-client.js";

export function describeError(error: unknown): string {
  if (error instanceof QikinkApiError) {
    switch (error.statusCode) {
      case 401:
        return "Error: Qikink rejected the access token. Check QIKINK_CLIENT_ID / QIKINK_CLIENT_SECRET and QIKINK_ENV (sandbox vs live).";
      case 404:
        return `Error: Qikink endpoint not found. Verify the path against your Qikink Postman collection. Details: ${error.message}`;
      case 429:
        return "Error: Qikink rate limit exceeded. Wait before retrying.";
      default:
        return `Error: ${error.message}`;
    }
  }
  return `Error: Unexpected error: ${error instanceof Error ? error.message : String(error)}`;
}
