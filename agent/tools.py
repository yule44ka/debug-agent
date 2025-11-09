import json

from langchain_core.tools import tool
import ast
import py_compile
import tempfile
import os
import sys
import traceback
from io import StringIO
from typing import Dict, Any


def readfile(path: str) -> str:
    """Read and return the content of a file as string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def lint_compile_python(code_path: str) -> Dict[str, Any]:
    """Check that Python code is valid and compiles without executing it.
    
    Args:
        code: The Python code to validate as a string
        
    Returns:
        A dictionary with 'success' boolean and 'errors' list if any compilation/syntax errors found
    """
    code = readfile(code_path)
    errors = []
    
    # Step 1: Try parsing with ast
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append({
            "type": "SyntaxError",
            "message": str(e),
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text
        })
        return {
            "success": False,
            "errors": errors,
            "message": f"Syntax error at line {e.lineno}: {e.msg}"
        }
    except Exception as e:
        errors.append({
            "type": type(e).__name__,
            "message": str(e)
        })
        return {
            "success": False,
            "errors": errors,
            "message": f"Parse error: {str(e)}"
        }
    
    # Step 2: Try compiling with py_compile
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            py_compile.compile(temp_file, doraise=True)
        finally:
            os.unlink(temp_file)
            # Also remove the compiled .pyc file if it was created
            pyc_file = temp_file + 'c'
            if os.path.exists(pyc_file):
                os.unlink(pyc_file)
                
    except py_compile.PyCompileError as e:
        errors.append({
            "type": "CompileError",
            "message": str(e)
        })
        return {
            "success": False,
            "errors": errors,
            "message": f"Compilation error: {str(e)}"
        }
    except Exception as e:
        errors.append({
            "type": type(e).__name__,
            "message": str(e)
        })
        return {
            "success": False,
            "errors": errors,
            "message": f"Unexpected error during compilation: {str(e)}"
        }
    
    return {
        "success": True,
        "errors": [],
        "message": "Code is syntactically valid and compiles successfully"
    }


def run_tests(function_code_path: str, test_code_path: str, function_name: str = None) -> Dict[str, Any]:
    """Execute test suite against the provided function and collect results.
    
    Args:
        function_code: The function implementation to test
        test_code: The test code to run (can include multiple test cases)
        function_name: Optional name of the function being tested
        
    Returns:
        A dictionary with test results including pass/fail status and tracebacks for failures
    """
    function_code = readfile("code.py")
    test_code = readfile("test.py")
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "test_results": [],
        "success": False
    }
    
    # Create a namespace for execution
    namespace = {}
    
    # Step 1: Execute the function code to define it
    try:
        exec(function_code, namespace)
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to load function code",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    
    # Step 2: Execute test code
    try:
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            exec(test_code, namespace)
            
            # Look for test results or assertions
            # If we get here without exceptions, tests passed
            results["total_tests"] = 1
            results["passed"] = 1
            results["success"] = True
            results["test_results"].append({
                "status": "passed",
                "message": "All tests executed successfully"
            })
            
        finally:
            stdout_output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            if stdout_output:
                results["stdout"] = stdout_output
            if stderr_output:
                results["stderr"] = stderr_output
                
    except AssertionError as e:
        results["total_tests"] = 1
        results["failed"] = 1
        results["success"] = False
        results["test_results"].append({
            "status": "failed",
            "error": "AssertionError",
            "message": str(e) if str(e) else "Assertion failed",
            "traceback": traceback.format_exc()
        })
    except Exception as e:
        results["total_tests"] = 1
        results["failed"] = 1
        results["success"] = False
        results["test_results"].append({
            "status": "failed",
            "error": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        })
    
    return results

code_path = "code.py"
test_path = "test.py"
result = run_tests(code_path, test_path)
print(result)