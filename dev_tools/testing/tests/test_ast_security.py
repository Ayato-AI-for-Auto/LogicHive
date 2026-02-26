from core.security import ASTSecurityChecker


def test_ast_security_allowed_libs():
    """Verify that safe standard libraries are allowed."""
    checker = ASTSecurityChecker()
    # re.compile was previously blocked by mistake
    code = "import re\npattern = re.compile(r'hello')\nprint(pattern.match('hello'))"
    is_safe, error = checker.check(code)
    assert is_safe, f"Should allow re.compile but got: {error}"


def test_ast_security_forbidden_builtins():
    """Verify that dangerous builtins are blocked."""
    checker = ASTSecurityChecker()
    # dangerous builtin
    code = "compile('print(123)', '<string>', 'exec')"
    is_safe, error = checker.check(code)
    assert not is_safe
    assert (
        "Forbidden builtin" in error or "Attribute call 'compile' is forbidden" in error
    )


def test_ast_security_forbidden_calls():
    """Verify that dangerous calls are blocked."""
    checker = ASTSecurityChecker()
    code = "import os\nos.system('rm -rf /')"
    is_safe, error = checker.check(code)
    assert not is_safe
    assert "system" in error.lower()


def test_ast_security_eval_blocked():
    """Verify that eval is blocked."""
    checker = ASTSecurityChecker()
    code = "eval('1 + 1')"
    is_safe, error = checker.check(code)
    assert not is_safe
    assert "eval" in error.lower()
