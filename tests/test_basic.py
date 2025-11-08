"""Basic tests for the bug-fixing agent components."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.tools import execute_python_code, create_code_execution_tool
from data.humanevalfix.loader import HumanEvalFixLoader


def test_code_execution_success():
    """Test successful code execution."""
    code = """
def add(a, b):
    return a + b
"""
    tests = """
assert add(2, 3) == 5
assert add(-1, 1) == 0
"""
    
    result = execute_python_code(code, tests)
    assert result["success"] == True
    assert result["tests_passed"] == True
    print("✓ test_code_execution_success passed")


def test_code_execution_failure():
    """Test code execution with failing tests."""
    code = """
def add(a, b):
    return a - b  # Wrong operation
"""
    tests = """
assert add(2, 3) == 5
"""
    
    result = execute_python_code(code, tests)
    assert result["success"] == False or result["tests_passed"] == False
    assert "AssertionError" in result["error"] or "Test failed" in result["error"]
    print("✓ test_code_execution_failure passed")


def test_code_execution_syntax_error():
    """Test code execution with syntax error."""
    code = """
def add(a, b)
    return a + b  # Missing colon
"""
    tests = "assert add(2, 3) == 5"
    
    result = execute_python_code(code, tests)
    assert result["success"] == False
    assert "SyntaxError" in result["error"]
    print("✓ test_code_execution_syntax_error passed")


def test_code_execution_tool():
    """Test the LangChain tool wrapper."""
    tool = create_code_execution_tool()
    
    input_str = """CODE:
def multiply(a, b):
    return a * b

TESTS:
assert multiply(2, 3) == 6
assert multiply(-1, 5) == -5
"""
    
    result = tool.run(input_str)
    assert "✓ Success" in result or "passed" in result.lower()
    print("✓ test_code_execution_tool passed")


def test_dataset_loader():
    """Test the HumanEvalFix dataset loader."""
    loader = HumanEvalFixLoader()
    tasks = loader.load()
    
    assert len(tasks) > 0
    assert "task_id" in tasks[0]
    assert "buggy_code" in tasks[0]
    assert "tests" in tasks[0]
    print("✓ test_dataset_loader passed")
    print(f"  Loaded {len(tasks)} tasks")


def test_agent_import():
    """Test that agent can be imported."""
    try:
        from agents.fix_bug_agent import BugFixAgent
        print("✓ test_agent_import passed")
        return True
    except Exception as e:
        print(f"✗ test_agent_import failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Running Basic Tests")
    print("="*60)
    
    tests = [
        test_code_execution_success,
        test_code_execution_failure,
        test_code_execution_syntax_error,
        test_code_execution_tool,
        test_dataset_loader,
        test_agent_import,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

