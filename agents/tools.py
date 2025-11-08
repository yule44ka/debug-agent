"""Code execution tool for testing Python code."""

import sys
import io
import traceback
from typing import Dict, Any
import contextlib
import signal
from langchain.tools import Tool


class TimeoutError(Exception):
    """Raised when code execution times out."""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal."""
    raise TimeoutError("Code execution timed out")


def execute_python_code(code: str, test_code: str = "", timeout: int = 5) -> Dict[str, Any]:
    """
    Execute Python code with optional test cases in a sandboxed environment.
    
    Args:
        code: The Python code to execute
        test_code: Optional test code to run after the main code
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary with execution results:
        - success: Boolean indicating if execution succeeded
        - output: stdout output from execution
        - error: error message if execution failed
        - tests_passed: Boolean indicating if tests passed (if test_code provided)
    """
    result = {
        "success": False,
        "output": "",
        "error": "",
        "tests_passed": False
    }
    
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    # Create isolated namespace for execution
    exec_namespace = {
        "__builtins__": __builtins__,
        "print": print,
    }
    
    try:
        # Set timeout
        if sys.platform != 'win32':
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            # Execute the main code
            exec(code, exec_namespace)
            
            # Execute test code if provided
            if test_code:
                exec(test_code, exec_namespace)
        
        # Cancel timeout
        if sys.platform != 'win32':
            signal.alarm(0)
        
        result["success"] = True
        result["output"] = stdout_capture.getvalue()
        result["tests_passed"] = True
        
    except TimeoutError as e:
        if sys.platform != 'win32':
            signal.alarm(0)
        result["error"] = f"Timeout: {str(e)}"
        result["output"] = stdout_capture.getvalue()
        
    except AssertionError as e:
        if sys.platform != 'win32':
            signal.alarm(0)
        result["error"] = f"Test failed: {str(e)}\n{traceback.format_exc()}"
        result["output"] = stdout_capture.getvalue()
        result["tests_passed"] = False
        
    except Exception as e:
        if sys.platform != 'win32':
            signal.alarm(0)
        result["error"] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        result["output"] = stdout_capture.getvalue()
    
    return result


def create_code_execution_tool() -> Tool:
    """
    Create a LangChain tool for code execution.
    
    Returns:
        Tool object that can be used with LangChain agents
    """
    
    def run_code(code_and_tests: str) -> str:
        """
        Run Python code with tests.
        
        Expected input format:
        CODE:
        <python code here>
        TESTS:
        <test code here>
        """
        try:
            # Parse input to separate code and tests
            if "TESTS:" in code_and_tests:
                parts = code_and_tests.split("TESTS:")
                code = parts[0].replace("CODE:", "").strip()
                tests = parts[1].strip()
            else:
                code = code_and_tests.replace("CODE:", "").strip()
                tests = ""
            
            # Execute code
            result = execute_python_code(code, tests)
            
            # Format output
            if result["success"] and result["tests_passed"]:
                return f"✓ Success! All tests passed.\nOutput:\n{result['output']}"
            elif result["success"] and not tests:
                return f"✓ Code executed successfully.\nOutput:\n{result['output']}"
            else:
                error_msg = f"✗ Execution failed.\n"
                if result["error"]:
                    error_msg += f"Error:\n{result['error']}\n"
                if result["output"]:
                    error_msg += f"Output:\n{result['output']}"
                return error_msg
                
        except Exception as e:
            return f"✗ Tool error: {str(e)}\n{traceback.format_exc()}"
    
    return Tool(
        name="execute_python_code",
        func=run_code,
        description=(
            "Execute Python code with optional tests. "
            "Input format: 'CODE:\\n<code>\\nTESTS:\\n<test_code>'. "
            "Returns execution results and test status."
        )
    )


if __name__ == "__main__":
    # Test the tool
    tool = create_code_execution_tool()
    
    test_input = """CODE:
def add(a, b):
    return a + b

TESTS:
assert add(2, 3) == 5
assert add(-1, 1) == 0
"""
    
    print(tool.run(test_input))

