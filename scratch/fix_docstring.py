import sys

try:
    with open('src/mcp_server.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Lines 453-456 in my check were:
    # 453: """
    # 454: Forcefully rebuilds...
    # 455: Use this if...
    # 456: """
    
    lines[453] = '    """\n'
    lines[454] = '    Forcefully rebuilds the FAISS vector index from all embeddings stored in the database.\n'
    lines[455] = '    Use this if \'check_integrity\' reports a desync between DB and Vector Store.\n'
    lines[456] = '    """\n'
    
    with open('src/mcp_server.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Fixed.")
except Exception as e:
    print(f"Error: {e}")
