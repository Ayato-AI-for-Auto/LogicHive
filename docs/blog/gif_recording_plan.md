# LogicHive GIF Recording & Demo Strategy Plan

To drive GitHub Star acquisition, we need a high-impact, lightweight visual demo showing LogicHive integrated with Cursor. Since LogicHive is a headless MCP server (no custom GUI), the demo will focus on developer experience (DX) using Cursor and a side-by-side terminal.

## Side-by-Side Screen Layout

- **Left Pane**: Cursor IDE (editor showing Python function and Composer/Chat open).
- **Right Pane**: Console terminal showing `LogicHive-MCP.exe` running.

## Demo Scenario (15-20 Seconds)

| Timestamp | Screen | Action | Visual / Log Output |
| :--- | :--- | :--- | :--- |
| **0s - 5s** | Left | User opens a Python function with tests in Cursor. Asks: *"Please save this function to LogicHive."* | Chat prompt submitted. |
| **5s - 10s** | Right | LogicHive server receives tool call `save_function` and starts verification. | Log output: `[Fact Gate] Scanning AST... OK`, `[Static Gate] Running Ruff... OK`, `[Execution Gate] Running pytest... Passed`. |
| **10s - 13s** | Left | Cursor confirms storage and returns quality metrics. | Chat returns: *"Logic 'intrinsic_value' saved. Score: 85 (Verified)."* |
| **13s - 20s** | Left | User opens a blank file and requests: *"Retrieve calculate_intrinsic_value from LogicHive and adapt it."* | Code is instantly pulled and inserted into the editor. |

## Complete Local-First Setup (Marketing Highlight)

To appeal to developers who prioritize data privacy, highlight the **100% Local Deployment** feature:
- **LLM Engine**: Ollama (e.g., `llama3` or `qwen2.5-coder`).
- **Embeddings**: FastEmbed (local CPU-bound vectorization).
- This combination requires no external network calls or cloud API keys.
