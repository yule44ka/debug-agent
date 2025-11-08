"""Example usage of the bug-fixing agent."""

import sys
from agents.fix_bug_agent import BugFixAgent
from agents.tools import execute_python_code


def example_1_simple_bug():
    """Example 1: Fix a simple arithmetic bug."""
    print("="*60)
    print("Example 1: Simple Arithmetic Bug")
    print("="*60)
    
    buggy_code = """
def add(a, b):
    '''Add two numbers and return the sum.'''
    return a - b  # BUG: Should be + not -
"""
    
    docstring = "Add two numbers and return the sum."
    
    tests = """
assert add(2, 3) == 5, "2 + 3 should equal 5"
assert add(-1, 1) == 0, "-1 + 1 should equal 0"
assert add(0, 0) == 0, "0 + 0 should equal 0"
assert add(10, -5) == 5, "10 + (-5) should equal 5"
"""
    
    print("\nBuggy code:")
    print(buggy_code)
    
    print("\nTesting buggy code...")
    result = execute_python_code(buggy_code, tests)
    if not result["tests_passed"]:
        print(f"✗ Tests failed (as expected):\n{result['error'][:200]}...")
    
    print("\nInitializing agent...")
    agent = BugFixAgent(max_iterations=3)
    
    print("\nAgent is fixing the bug...")
    fixed_code = agent.fix_bug(buggy_code, docstring, tests)
    
    print("\nFixed code:")
    print(fixed_code)
    
    print("\nVerifying fix...")
    result = execute_python_code(fixed_code, tests)
    if result["tests_passed"]:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests still failing:\n{result['error']}")


def example_2_logic_bug():
    """Example 2: Fix a logic bug in conditional."""
    print("\n" + "="*60)
    print("Example 2: Logic Bug in Conditional")
    print("="*60)
    
    buggy_code = """
def is_even(n):
    '''Check if a number is even.'''
    return n % 2 == 1  # BUG: Should be == 0
"""
    
    docstring = "Check if a number is even. Returns True if even, False otherwise."
    
    tests = """
assert is_even(2) == True, "2 is even"
assert is_even(3) == False, "3 is odd"
assert is_even(0) == True, "0 is even"
assert is_even(-4) == True, "-4 is even"
assert is_even(-3) == False, "-3 is odd"
"""
    
    print("\nBuggy code:")
    print(buggy_code)
    
    print("\nAgent is fixing the bug...")
    agent = BugFixAgent(max_iterations=3)
    fixed_code = agent.fix_bug(buggy_code, docstring, tests)
    
    print("\nFixed code:")
    print(fixed_code)
    
    print("\nVerifying fix...")
    result = execute_python_code(fixed_code, tests)
    if result["tests_passed"]:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests still failing:\n{result['error']}")


def example_3_off_by_one():
    """Example 3: Fix an off-by-one error."""
    print("\n" + "="*60)
    print("Example 3: Off-by-One Error")
    print("="*60)
    
    buggy_code = """
def get_first_n_elements(lst, n):
    '''Get the first n elements from a list.'''
    return lst[:n-1]  # BUG: Should be lst[:n]
"""
    
    docstring = "Get the first n elements from a list."
    
    tests = """
assert get_first_n_elements([1, 2, 3, 4, 5], 3) == [1, 2, 3]
assert get_first_n_elements([1, 2, 3], 1) == [1]
assert get_first_n_elements([1, 2, 3], 0) == []
assert get_first_n_elements([], 5) == []
"""
    
    print("\nBuggy code:")
    print(buggy_code)
    
    print("\nAgent is fixing the bug...")
    agent = BugFixAgent(max_iterations=3)
    fixed_code = agent.fix_bug(buggy_code, docstring, tests)
    
    print("\nFixed code:")
    print(fixed_code)
    
    print("\nVerifying fix...")
    result = execute_python_code(fixed_code, tests)
    if result["tests_passed"]:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests still failing:\n{result['error']}")


def main():
    """Run all examples."""
    print("\n" + "🐛" * 30)
    print("Bug-Fixing Agent Examples")
    print("🐛" * 30)
    
    print("\nThese examples demonstrate the agent's ability to:")
    print("1. Identify bugs in Python code")
    print("2. Generate fixes iteratively")
    print("3. Verify fixes with test cases")
    print("4. Use ReAct reasoning (Reason → Act → Observe)")
    
    try:
        example_1_simple_bug()
    except Exception as e:
        print(f"\n✗ Example 1 failed: {e}")
    
    try:
        example_2_logic_bug()
    except Exception as e:
        print(f"\n✗ Example 2 failed: {e}")
    
    try:
        example_3_off_by_one()
    except Exception as e:
        print(f"\n✗ Example 3 failed: {e}")
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)
    print("\nNote: The agent uses a small LLM (Qwen2.5-0.5B) which may")
    print("not always fix bugs perfectly. For better results, try:")
    print("- Larger models (1.5B, 7B parameters)")
    print("- More iterations (--max-iterations 10)")
    print("- Fine-tuned code models (CodeLlama, StarCoder)")
    print("="*60)


if __name__ == "__main__":
    main()

