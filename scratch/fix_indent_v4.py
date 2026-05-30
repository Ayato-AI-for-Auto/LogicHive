try:
    with open("src/mcp_server.py", encoding="utf-8") as f:
        lines = f.readlines()

    # 150: '    if mock_imports is None:\n'
    # 151: '        mock_imports = []\n'
    # 152: '    if mock_imports is None:\n'
    # 153: '    try:\n'

    del lines[152:153]  # Remove the redundant 'if'

    with open("src/mcp_server.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Fixed.")
except Exception as e:
    print(f"Error: {e}")
