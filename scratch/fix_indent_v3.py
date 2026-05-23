
try:
    with open('src/mcp_server.py', encoding='utf-8') as f:
        lines = f.readlines()

    # 151: '        mock_imports = []\n'
    # 152: '    if mock_imports is None:\n'
    # Swap them

    line151 = lines[151]
    line152 = lines[152]

    lines[151] = '    if mock_imports is None:\n'
    lines[152] = '        mock_imports = []\n'

    with open('src/mcp_server.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Fixed.")
except Exception as e:
    print(f"Error: {e}")
