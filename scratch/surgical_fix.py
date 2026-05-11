import sys

try:
    with open('src/mcp_server.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Identify the section from line 140
    # The snippet confirms lines are messed up starting after 'if mock_imports is None: mock_imports = []'
    
    new_lines = []
    for i, line in enumerate(lines):
        if "if mock_imports is None:" in line:
            new_lines.append(line)
            new_lines.append("        mock_imports = []\n")
            new_lines.append('    """\n')
            new_lines.append('    Saves a verified, high-quality code asset to the LogicHive vault.\n')
            new_lines.append('    """\n')
            # Skip the corrupt lines until the docstring ends
            # The corrupt lines were around 155-167. 
            # I will manually jump past them
            continue
        if i >= 152 and i <= 170:
            continue
        new_lines.append(line)
    
    with open('src/mcp_server.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Fixed.")
except Exception as e:
    print(f"Error: {e}")
