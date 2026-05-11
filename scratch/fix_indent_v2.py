import sys

try:
    with open('src/mcp_server.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Line 151: '    if mock_imports is None:\n'
    # Line 152: '    try:\n'
    # Need to insert '        mock_imports = []\n' after line 151
    
    lines.insert(152, '        mock_imports = []\n')
    
    with open('src/mcp_server.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Fixed.")
except Exception as e:
    print(f"Error: {e}")
