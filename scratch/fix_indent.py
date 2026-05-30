try:
    with open("src/mcp_server.py", encoding="utf-8") as f:
        lines = f.readlines()

    # Line 153 starts with '    """'
    # Line 158 is '        success = await do_save_async('

    # We need to ensure correct indentation
    # Remove the extra """ and fix indentation

    del lines[153:157]  # Remove the short docstring that is misplaced
    # Adjust the indentation of line 158 (was 158 now it's shifted)
    lines[153] = "    try:\n"
    lines[154] = "        success = await do_save_async(\n"

    with open("src/mcp_server.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Fixed.")
except Exception as e:
    print(f"Error: {e}")
