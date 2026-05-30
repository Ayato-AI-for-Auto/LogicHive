try:
    with open("src/mcp_server.py", encoding="utf-8") as f:
        lines = f.readlines()

    # 150: '    if mock_imports is None:\n'
    # 151: '    if mock_imports is None:\n'
    # 152: '    try:\n'

    # Needs to be:
    #     if mock_imports is None:
    #         mock_imports = []
    #     try:

    lines[150] = "    if mock_imports is None:\n"
    lines[151] = "        mock_imports = []\n"
    del lines[152]  # redundant if

    with open("src/mcp_server.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Fixed.")
except Exception as e:
    print(f"Error: {e}")
