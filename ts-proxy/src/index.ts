#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "../../");

// Load local .env from project root
const ROOT_ENV_PATH = path.join(ROOT_DIR, ".env");
if (fs.existsSync(ROOT_ENV_PATH)) {
    dotenv.config({ path: ROOT_ENV_PATH });
}

// Hub URL and API Key
const GEMINI_API_KEY = process.env.FS_GEMINI_API_KEY || "";

/**
 * Calls Gemini API locally using the user's key.
 * Used for Reverse Intelligence Flow.
 */
async function callGeminiLocally(prompt: string): Promise<string> {
    if (!GEMINI_API_KEY) {
        throw new Error("Local Gemini API Key (FS_GEMINI_API_KEY) is missing.");
    }

    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }]
        })
    });

    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Local Gemini Call Failed: ${err}`);
    }

    const data: any = await response.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text || "";
}

// Hub URL from arguments or environment
const args = process.argv.slice(2);
let HUB_URL = process.env.FS_HUB_URL || "http://localhost:8000";
const hubUrlArgIndex = args.indexOf("--hub-url");
if (hubUrlArgIndex !== -1 && args[hubUrlArgIndex + 1]) {
    HUB_URL = args[hubUrlArgIndex + 1];
}

/**
 * Helper to call Python MCP Tools via CLI.
 * This ensures single ownership of the DuckDB file by the Python process.
 */
function callPythonTool(toolName: string, args: any): any {
    try {
        const payload = JSON.stringify(args).replace(/"/g, '\\"');
        // We use 'uv run' to ensure the correct environment. 
        // Note: For real performance, we'd use a persistent JSON-RPC bridge.
        const cmd = `uv run python -c "from edge.orchestrator import do_${toolName.replace('save_function', 'save')}_impl; import json; print(json.dumps(do_${toolName.replace('save_function', 'save')}_impl(**json.loads('${payload}'))))"`;
        const result = execSync(cmd, { cwd: ROOT_DIR, encoding: "utf-8" });
        return JSON.parse(result);
    } catch (e: any) {
        throw new Error(`Python Bridge Error (${toolName}): ${e.message}`);
    }
}

const server = new Server(
    {
        name: "function-store-proxy",
        version: "3.1.0", // Hybrid Edition - Slim Proxy
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "save_function",
                description: "Saves a function locally and verifies its intelligence via Cloud Hub.",
                inputSchema: {
                    type: "object",
                    properties: {
                        name: { type: "string" },
                        code: { type: "string" },
                        description: { type: "string" },
                        tags: { type: "array", items: { type: "string" } },
                        dependencies: { type: "array", items: { type: "string" } },
                        test_cases: { type: "array", items: { type: "object" } },
                    },
                    required: ["name", "code"],
                },
            },
            {
                name: "search_functions",
                description: "Semantic search combined with Cloud-based reranking.",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: { type: "string" },
                        limit: { type: "number" },
                    },
                    required: ["query"],
                },
            },
            {
                name: "list_functions",
                description: "Lists all stored functions from Local Edge DB.",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: { type: "string" },
                        tag: { type: "string" },
                        limit: { type: "number" },
                    },
                },
            },
            {
                name: "get_function_details",
                description: "Retrieves full metadata from Local Edge DB.",
                inputSchema: {
                    type: "object",
                    properties: {
                        name: { type: "string" },
                    },
                    required: ["name"],
                },
            },
            {
                name: "smart_search_and_get",
                description: "Hybrid flow: Local Search -> Cloud Intelligence -> Local Injection.",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: { type: "string" },
                        target_dir: { type: "string" },
                    },
                    required: ["query"],
                },
            },
        ],
    };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: toolArgs } = request.params;

    try {
        switch (name) {
            case "list_functions": {
                // Delegate to Python
                const results = callPythonTool("list", { limit: toolArgs?.limit || 100 });
                return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
            }

            case "get_function_details": {
                const detail = callPythonTool("get_details", { name: toolArgs?.name });
                return { content: [{ type: "text", text: JSON.stringify(detail, null, 2) }] };
            }

            case "save_function": {
                // 1. Initial Local Save (Delegated to Python)
                const saveResult = callPythonTool("save_function", {
                    asset_name: toolArgs?.name,
                    code: toolArgs?.code,
                    description: toolArgs?.description,
                    tags: toolArgs?.tags,
                    dependencies: toolArgs?.dependencies,
                    test_cases: toolArgs?.test_cases
                });

                // 2. Cloud Intelligence (Keep in Proxy for hybrid orchestration)
                try {
                    const promptRes = await fetch(`${HUB_URL}/api/v1/intelligence/verify/get-prompt`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(toolArgs)
                    });
                    if (promptRes.ok) {
                        const { prompt } = await promptRes.json();
                        const llmOutput = await callGeminiLocally(prompt);

                        await fetch(`${HUB_URL}/api/v1/intelligence/verify/finalize`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                name: toolArgs?.name,
                                code: toolArgs?.code,
                                llm_output: llmOutput
                            })
                        });
                    }
                } catch (e) {
                    console.error("Cloud verification skip/fail (non-blocking):", e);
                }

                return { content: [{ type: "text", text: saveResult }] };
            }

            case "smart_search_and_get": {
                // Delegate the entire complex flow to Python
                const result = callPythonTool("smart_get", {
                    query: toolArgs?.query,
                    target_dir: toolArgs?.target_dir || "./"
                });
                return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
            }

            case "search_functions": {
                const results = callPythonTool("search", {
                    query: toolArgs?.query,
                    limit: toolArgs?.limit || 5
                });
                return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
            }

            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    } catch (error) {
        return {
            isError: true,
            content: [{ type: "text", text: `Slim Proxy Error: ${error instanceof Error ? error.message : String(error)}` }],
        };
    }
});

async function main() {
    // Security check: Warn if remote Hub is used without HTTPS
    if (HUB_URL.startsWith("http://") && !HUB_URL.includes("localhost") && !HUB_URL.includes("127.0.0.1")) {
        console.warn("\x1b[33m%s\x1b[0m", "SECURITY WARNING: You are connecting to a remote Hub via insecure HTTP.");
    }

    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error(`Function Store Slim Proxy running (Python delegated). Hub: ${HUB_URL}`);
}

main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});
