#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { spawn, execSync } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import duckdb from "duckdb";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "../../");
const DB_PATH = path.join(ROOT_DIR, "functions.duckdb");

// Hub URL from arguments or environment
const args = process.argv.slice(2);
let HUB_URL = process.env.FS_HUB_URL || "http://localhost:8000";
const hubUrlArgIndex = args.indexOf("--hub-url");
if (hubUrlArgIndex !== -1 && args[hubUrlArgIndex + 1]) {
    HUB_URL = args[hubUrlArgIndex + 1];
}

/**
 * Local Database Management (DuckDB)
 */
class LocalDB {
    private db: duckdb.Database;

    constructor(path: string) {
        this.db = new duckdb.Database(path);
    }

    private query(sql: string, params: any[] = []): Promise<any[]> {
        return new Promise((resolve, reject) => {
            this.db.all(sql, ...params, (err: any, rows: any[]) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });
    }

    private exec(sql: string, params: any[] = []): Promise<void> {
        return new Promise((resolve, reject) => {
            this.db.run(sql, ...params, (err: any) => {
                if (err) reject(err);
                else resolve();
            });
        });
    }

    async init() {
        await this.exec(`
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY,
                name VARCHAR UNIQUE,
                code VARCHAR,
                description VARCHAR,
                tags VARCHAR,
                metadata VARCHAR,
                status VARCHAR DEFAULT 'active',
                test_cases VARCHAR,
                call_count INTEGER DEFAULT 0,
                last_called_at VARCHAR,
                created_at VARCHAR,
                updated_at VARCHAR
            )
        `);
    }

    async listFunctions(query?: string, tag?: string, limit = 20, includeArchived = false) {
        let sql = "SELECT name, description, tags, status, call_count FROM functions";
        const where: string[] = [];
        const params: any[] = [];

        if (!includeArchived) where.push("status != 'archived'");
        if (tag) {
            where.push("tags LIKE ?");
            params.push(`%"${tag}"%`);
        }
        if (query) {
            where.push("(name ILIKE ? OR description ILIKE ?)");
            params.push(`%${query}%`, `%${query}%`);
        }

        if (where.length > 0) sql += " WHERE " + where.join(" AND ");
        sql += " ORDER BY updated_at DESC LIMIT ?";
        params.push(limit);

        return await this.query(sql, params);
    }

    async getFunctionDetails(name: string) {
        const rows = await this.query("SELECT * FROM functions WHERE name = ?", [name]);
        if (rows.length === 0) return null;
        const row = rows[0];
        return {
            ...row,
            tags: JSON.parse(row.tags || "[]"),
            metadata: JSON.parse(row.metadata || "{}"),
            test_cases: JSON.parse(row.test_cases || "[]")
        };
    }

    async saveFunction(data: any) {
        const now = new Date().toISOString();
        const existing = await this.getFunctionDetails(data.name);

        if (existing) {
            await this.exec(
                "UPDATE functions SET code=?, description=?, tags=?, metadata=?, test_cases=?, status=?, updated_at=? WHERE name=?",
                [
                    data.code,
                    data.description || existing.description,
                    JSON.stringify(data.tags || existing.tags),
                    JSON.stringify(data.metadata || existing.metadata),
                    JSON.stringify(data.test_cases || existing.test_cases),
                    data.status || existing.status,
                    now,
                    data.name
                ]
            );
        } else {
            await this.exec(
                "INSERT INTO functions (name, code, description, tags, metadata, test_cases, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    data.name,
                    data.code,
                    data.description || "",
                    JSON.stringify(data.tags || []),
                    JSON.stringify(data.metadata || {}),
                    JSON.stringify(data.test_cases || []),
                    data.status || "active",
                    now,
                    now
                ]
            );
        }
    }
}

const localDb = new LocalDB(DB_PATH);

const server = new Server(
    {
        name: "function-store-proxy",
        version: "3.0.0", // Hybrid Edition
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
                        include_archived: { type: "boolean" },
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
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case "list_functions": {
                const results = await localDb.listFunctions(
                    args?.query as string,
                    args?.tag as string,
                    args?.limit as number,
                    args?.include_archived as boolean
                );
                return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
            }

            case "get_function_details": {
                const detail = await localDb.getFunctionDetails(args?.name as string);
                return { content: [{ type: "text", text: detail ? JSON.stringify(detail, null, 2) : "Not found." }] };
            }

            case "save_function": {
                // 1. Initial Local Save (Pending)
                await localDb.saveFunction({ ...args, status: "pending" });

                // 2. Cloud Intelligence (Verification, Quality, Dependency Analysis)
                try {
                    const response = await fetch(`${HUB_URL}/api/v1/intelligence/verify`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(args)
                    });
                    if (response.ok) {
                        const intellectResult = await response.json();
                        // 3. Update Local DB with Intelligence results
                        await localDb.saveFunction({
                            name: args?.name,
                            ...intellectResult,
                            status: intellectResult.status || "verified"
                        });
                        return { content: [{ type: "text", text: `SUCCESS: Function '${args?.name}' saved and verified via Cloud.` }] };
                    }
                } catch (e) {
                    return { content: [{ type: "text", text: `WARNING: Saved locally as 'pending', but Cloud verification failed: ${e}` }] };
                }
                return { content: [{ type: "text", text: `SUCCESS: Saved locally as 'pending'.` }] };
            }

            case "smart_search_and_get": {
                // 1. Local Broad Search
                const candidates = await localDb.listFunctions(args?.query as string, undefined, 10);
                if (candidates.length === 0) {
                    return { content: [{ type: "text", text: "No matching functions found locally." }] };
                }

                // 2. Cloud Intelligence (Semantic Reranking)
                const cloudRes = await fetch(`${HUB_URL}/api/v1/intelligence/rerank`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: args?.query, candidates })
                });

                if (!cloudRes.ok) throw new Error("Cloud Reranking failed.");
                const { selected_name } = await cloudRes.json();

                // 3. Local Retrieval & Injection
                const details = await localDb.getFunctionDetails(selected_name);
                if (!details) throw new Error("Selected function disappeared from Local DB.");

                // Fake injection for now (simulating do_inject_impl)
                const targetDir = (args?.target_dir as string) || "./";
                const pkgDir = path.join(process.cwd(), targetDir, "local_pkg");
                if (!fs.existsSync(pkgDir)) fs.mkdirSync(pkgDir, { recursive: true });
                fs.writeFileSync(path.join(pkgDir, `${selected_name}.py`), details.code);

                return {
                    content: [{
                        type: "text",
                        text: `SUCCESS: Selected '${selected_name}' via Cloud Intelligence.\nInjected into ${targetDir}/local_pkg/`
                    }]
                };
            }

            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    } catch (error) {
        return {
            isError: true,
            content: [{ type: "text", text: `Hybrid Proxy Error: ${error instanceof Error ? error.message : String(error)}` }],
        };
    }
});

async function main() {
    await localDb.init();
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error(`Function Store Hybrid Proxy running. Hub: ${HUB_URL}`);
}

main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});
