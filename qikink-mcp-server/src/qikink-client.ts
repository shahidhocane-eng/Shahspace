import axios, { type AxiosInstance } from "axios";

export type QikinkEnv = "sandbox" | "live";

const BASE_URLS: Record<QikinkEnv, string> = {
  sandbox: "https://sandbox.qikink.com",
  live: "https://api.qikink.com",
};

export class QikinkApiError extends Error {
  constructor(
    public statusCode: number | undefined,
    public payload: unknown
  ) {
    super(`Qikink API error ${statusCode ?? "(no status)"}: ${formatPayload(payload)}`);
    this.name = "QikinkApiError";
  }
}

function formatPayload(payload: unknown): string {
  if (typeof payload === "string") return payload;
  try {
    return JSON.stringify(payload);
  } catch {
    return String(payload);
  }
}

function toApiError(error: unknown): QikinkApiError {
  if (axios.isAxiosError(error)) {
    return new QikinkApiError(error.response?.status, error.response?.data ?? error.message);
  }
  return new QikinkApiError(undefined, error instanceof Error ? error.message : String(error));
}

export interface QikinkRequestOptions {
  json?: unknown;
  params?: Record<string, unknown>;
}

/**
 * Auth: exchange ClientId + client_secret for a bearer token via POST /api/token,
 * then send it as an Accesstoken header (alongside ClientId) on every other call.
 * Confirmed against documented example payloads for /api/token and
 * /api/order/create; other endpoints are reached via request() as a generic
 * escape hatch, unverified.
 */
export class QikinkClient {
  readonly baseUrl: string;
  private readonly http: AxiosInstance;
  private accessToken: string | null = null;

  constructor(
    private readonly clientId: string,
    private readonly clientSecret: string,
    readonly env: QikinkEnv = "sandbox"
  ) {
    this.baseUrl = BASE_URLS[env];
    this.http = axios.create({ baseURL: this.baseUrl, timeout: 15000 });
  }

  async authenticate(): Promise<string> {
    let response;
    try {
      response = await this.http.post(
        "/api/token",
        new URLSearchParams({ ClientId: this.clientId, client_secret: this.clientSecret }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );
    } catch (error) {
      throw toApiError(error);
    }

    const body = response.data as Record<string, unknown>;
    const token = (body.Accesstoken ?? body.access_token ?? body.token) as string | undefined;
    if (!token) {
      throw new QikinkApiError(response.status, `No access token in response: ${formatPayload(body)}`);
    }
    this.accessToken = token;
    return token;
  }

  private async getAccessToken(): Promise<string> {
    if (!this.accessToken) {
      await this.authenticate();
    }
    return this.accessToken as string;
  }

  /** Authenticated request against any Qikink endpoint, retrying once on 401. */
  async request<T = unknown>(
    method: "GET" | "POST" | "PUT" | "DELETE",
    path: string,
    options: QikinkRequestOptions = {}
  ): Promise<T> {
    const token = await this.getAccessToken();

    const attempt = (accessToken: string) =>
      this.http.request({
        method,
        url: path,
        data: options.json,
        params: options.params,
        headers: { ClientId: this.clientId, Accesstoken: accessToken },
      });

    try {
      const response = await attempt(token);
      return response.data as T;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        const freshToken = await this.authenticate();
        try {
          const retryResponse = await attempt(freshToken);
          return retryResponse.data as T;
        } catch (retryError) {
          throw toApiError(retryError);
        }
      }
      throw toApiError(error);
    }
  }

  createOrder(payload: unknown): Promise<unknown> {
    return this.request("POST", "/api/order/create", { json: payload });
  }
}
