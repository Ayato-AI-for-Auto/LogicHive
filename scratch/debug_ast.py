import ast

test_code = "pytest.assume(x > 0)"
tree = ast.parse(test_code)
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            print(f"Attr: {node.func.attr}")
            print(f"Starts with assume: {node.func.attr.startswith('assume')}")
