import sys
import settings_ui

for k in sys.modules.keys():
    if "fastmcp" in k or "mcp" in k or "uvicorn" in k or "starlette" in k:
        print(f"Imported: {k}")
