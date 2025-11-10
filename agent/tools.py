import json

from langchain_core.tools import tool
import ast
import py_compile
import tempfile
import os
import sys
import traceback
import signal
from io import StringIO
from typing import Dict, Any

class TimeoutError(Exception):
    """Custom timeout exception for test execution"""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal"""
    raise TimeoutError("Test execution timed out")


def readfile(path: str) -> str:
    """Read and return the content of a file as string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@tool
def lint_compile_python(code_path: str) -> Dict[str, Any]:
    """Check that Python code is valid and compiles without executing it.
    
    Args:
        code_path: The Python code path to validate as a string
        
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

@tool
def run_tests(code_path: str) -> Dict[str, Any]:
    """Execute test suite against the provided function.
    
    Args:
        code_path: The path of the code to test with predefined tests

    Returns:
        A dictionary with test results including:
        - status: 'passed', 'failed', 'timeout', or 'error'
        - success: boolean indicating if test passed
        - message: description of the result
        - traceback: detailed error information if applicable
        - error_line: the line number where error occurred
        - error_code: the actual line of code where error occurred
    """
    timeout_seconds = 5

    function_code = readfile(code_path)
    task_id = code_path.split("_")[-1].split(".")[0]
    test_code = readfile(f"tmp/test/test_{task_id}.py")
    
    # Combine code and test exactly like evaluation.py does
    full_code = function_code + "\n\n" + test_code
    full_code_lines = full_code.split('\n')
    
    # Set up the timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Execute combined code with timeout
        namespace = {}
        
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            exec(full_code, namespace)
            
            # If we got here without exceptions, test passed
            stdout_output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()
            
            result = {
                "status": "passed",
                "success": True,
                "message": "All tests executed successfully"
            }
            
            if stdout_output:
                result["stdout"] = stdout_output
            if stderr_output:
                result["stderr"] = stderr_output
                
            return result
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            # Disable the alarm
            signal.alarm(0)
    
    except TimeoutError as e:
        # Test execution timed out
        signal.alarm(0)  # Disable the alarm
        return {
            "status": "timeout",
            "success": False,
            "message": f"Test execution timed out (exceeded {timeout_seconds} seconds)",
            "error": "TimeoutError",
            "traceback": traceback.format_exc()
        }
    
    except AssertionError as e:
        # Test failed (assertion error)
        signal.alarm(0)  # Disable the alarm
        
        # Extract line number and code from traceback
        tb = traceback.extract_tb(sys.exc_info()[2])
        error_line_num = None
        error_code = None
        
        # Find the last frame that's in our executed code (not in <string>)
        for frame in reversed(tb):
            if frame.filename == '<string>':
                error_line_num = frame.lineno
                # Get the actual line of code (1-indexed to 0-indexed)
                if 0 < error_line_num <= len(full_code_lines):
                    error_code = full_code_lines[error_line_num - 1].strip()
                break
        
        result = {
            "status": "failed",
            "success": False,
            "message": f"✗Test failed: {str(e) if str(e) else 'Assertion failed'}",
            "error": "AssertionError",
        }
        
        if error_line_num:
            result["error_line"] = error_line_num
        if error_code:
            result["error_code"] = error_code
            result["message"] += f"\n  Line {error_line_num}: {error_code}"
        
        return result
    
    except Exception as e:
        # Execution error (other exceptions)
        signal.alarm(0)  # Disable the alarm
        
        # Extract line number and code from traceback
        tb = traceback.extract_tb(sys.exc_info()[2])
        error_line_num = None
        error_code = None
        
        # Find the last frame that's in our executed code
        for frame in reversed(tb):
            if frame.filename == '<string>':
                error_line_num = frame.lineno
                # Get the actual line of code (1-indexed to 0-indexed)
                if 0 < error_line_num <= len(full_code_lines):
                    error_code = full_code_lines[error_line_num - 1].strip()
                break
        
        result = {
            "status": "error",
            "success": False,
            "message": f"✗ Execution error: {type(e).__name__}: {str(e)}",
            "error": type(e).__name__,
        }
        
        if error_line_num:
            result["error_line"] = error_line_num
        if error_code:
            result["error_code"] = error_code
            result["message"] += f"\n  Line {error_line_num}: {error_code}"
        
        return result
    
    finally:
        # Ensure alarm is always disabled
        signal.alarm(0)

# code_path = "code_1.py"
# result = run_tests(code_path)
# print(result)