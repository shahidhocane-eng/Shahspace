#!/usr/bin/env node
/**
 * MCP server for the Qikink Print on Demand / Dropshipping API.
 *
 * Exposes qikink_check_connection, qikink_create_order (confirmed schema),
 * and qikink_request (generic authenticated escape hatch for endpoints not
 * yet wrapped as dedicated tools).
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express from "express";
import { QikinkClient, type QikinkEnv } from "./qikink-client.js";
import { registerTools } from "./tools.js";

function loadConfig() {
  const clientId = process.env.QIKINK_CLIENT_ID;
  const clientSecret = process.env.QIKINK_CLIENT_SECRET;
  const env = (process.env.QIKINK_ENV ?? "sandbox") as QikinkEnv;

  if (!clientId || !clientSecret) {
    console.error("ERROR: QIKINK_CLIENT_ID and QIKINK_CLIENT_SECRET environment variables are required");
    process.exit(1);
  }
  if (env !== "sandbox" && env !== "live") {
    console.error(`ERROR: QIKINK_ENV must be "sandbox" or "live", got ${JSON.stringify(env)}`);
    process.exit(1);
  }

  return { clientId, clientSecret, env };
}

function buildServer(client: QikinkClient): McpServer {
  const server = new McpServer({ name: "qikink-mcp-server", version: "1.0.0" });
  registerTools(server, client);
  return server;
}

async function runStdio(client: QikinkClient): Promise<void> {
  const server = buildServer(client);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Qikink MCP server running via stdio");
}

async function runHttp(client: QikinkClient): Promise<void> {
  const app = express();
  app.use(express.json());

  app.post("/mcp", async (req, res) => {
    // Stateless: a fresh server + transport per request avoids request-ID collisions
    // across concurrent clients.
    const server = buildServer(client);
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });
    res.on("close", () => {
      transport.close();
      server.close();
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  });

  const port = parseInt(process.env.PORT ?? "3000", 10);
  app.listen(port, () => {
    console.error(`Qikink MCP server running on http://localhost:${port}/mcp`);
  });
}

const config = loadConfig();
const client = new QikinkClient(config.clientId, config.clientSecret, config.env);

const transportMode = process.env.TRANSPORT ?? "stdio";
const run = transportMode === "http" ? runHttp(client) : runStdio(client);

run.catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
