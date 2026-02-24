import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROXY_JS = path.join(__dirname, "dist/index.js");

async function test() {
    console.log("Starting E2E Integration Test...");

    const proxy = spawn("node", [PROXY_JS], {
        stdio: ["pipe", "pipe", "inherit"],
    });

    const sendRequest = (method, params = {}) => {
        const req = {
            jsonrpc: "2.0",
            id: 1,
            method,
            params
        };
        proxy.stdin.write(JSON.stringify(req) + "\n");
    };

    proxy.stdout.on("data", (data) => {
        const response = JSON.parse(data.toString());
        console.log("\n[PROXY RESPONSE]:", JSON.stringify(response, null, 2));

        if (response.id === 1) {
            console.log("\n[SUCCESS] Received expected response from TS Proxy!");
            proxy.kill();
            process.exit(0);
        }
    });

    // Step 1: List Tools (Verify Proxy itself is healthy)
    console.log("Step 1: Listing Tools...");
    setTimeout(() => sendRequest("notifications/initialized"), 500); // Send dummy init
    setTimeout(() => sendRequest("tools/list"), 1000);

    // Step 2: Call Tool (Verify Hub Auto-Start & REST Proxy)
    // Note: ensureBackendRunning is only called on CALL_TOOL in current implementation.
    // Let's call list_functions (which is mapped to GET /api/v1/functions)
    setTimeout(() => {
        console.log("\nStep 2: Calling 'list_functions' (This triggers Hub Auto-Start)...");
        sendRequest("tools/call", {
            name: "list_functions",
            arguments: { limit: 1 }
        });
    }, 2000);

    setTimeout(() => {
        console.log("\n[FAIL] Timeout waiting for response.");
        proxy.kill();
        process.exit(1);
    }, 45000); // 45s since Hub setup + start can be slow
}

test().catch(console.error);
