import ast
import re
from typing import Tuple, Set

# --- Security Patterns ---
SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z_-]{35}",  # Google API Key
    r"ghp_[a-zA-Z0-9]{36}",  # GitHub Personal Access Token
    r"sk-[a-zA-Z0-9]{48}",   # OpenAI Key (typical)
]


class ASTSecurityChecker:
    """
    Static analysis to detect potentially dangerous code.
    Policy: RESTRICTIVE - Block anything that could compromise the host or leak data.
    """

    # Modules that are completely forbidden to import
    FORBIDDEN_IMPORTS = {
        "os", "sys", "subprocess", "shutil", "pickle", "marshal", "shelve", 
        "socket", "requests", "urllib", "http", "webbrowser", "ftplib", 
        "telnetlib", "smtplib", "platform", "ctypes", "builtins", "importlib",
        "multiprocessing", "threading", "pysqlite3", "sqlite3"
    }

    # Specific dangerous calls even if they are attributes of non-forbidden modules
    FORBIDDEN_CALLS = {
        "eval", "exec", "compile", "breakpoint", "__import__",
        "system", "popen", "spawn", "fork", "kill"
    }

    # Builtin functions that should not be used in general user functions
    FORBIDDEN_BUILTINS = {
        "open", "getattr", "setattr", "delattr", "hasattr", 
        "globals", "locals", "vars", "dir", "help", "input"
    }

    @classmethod
    def check(cls, code: str) -> Tuple[bool, str]:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # 1. Check Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] in cls.FORBIDDEN_IMPORTS:
                            return False, f"Security Block: Import of '{alias.name}' is forbidden."
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in cls.FORBIDDEN_IMPORTS:
                        return False, f"Security Block: Import from '{node.module}' is forbidden."

                # 2. Check Function Calls
                elif isinstance(node, ast.Call):
                    # Direct calls: eval(), exec(), open()
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in cls.FORBIDDEN_CALLS or func_name in cls.FORBIDDEN_BUILTINS:
                            return False, f"Security Block: Direct call to '{func_name}' is forbidden."
                    
                    # Attribute calls: os.system(), subprocess.run()
                    elif isinstance(node.func, ast.Attribute):
                        method_name = node.func.attr
                        if method_name in cls.FORBIDDEN_CALLS:
                            return False, f"Security Block: Attribute call '{method_name}' is forbidden."

                # 3. Check for dunder methods/attributes access (e.g. __class__)
                elif isinstance(node, ast.Attribute):
                    if node.attr.startswith('__') and node.attr.endswith('__'):
                         # Allow common ones if necessary, but generally suspicious in this context
                         if node.attr not in {'__name__', '__init__'}:
                            return False, f"Security Block: Access to dunder attribute '{node.attr}' is forbidden."

            return True, ""
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"
        except Exception as e:
            return False, f"Analysis Error: {str(e)}"


def _contains_secrets(code: str) -> Tuple[bool, str]:
    """Scans code for potential API keys or secrets using regex."""
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            return True, matches[0]
    return False, ""
