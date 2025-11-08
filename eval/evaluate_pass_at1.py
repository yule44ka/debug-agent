"""Evaluate agent results using pass@1 metric."""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.tools import execute_python_code


def load_results(results_file: str) -> List[Dict[str, Any]]:
    """
    Load agent results from JSONL file.
    
    Args:
        results_file: Path to results file
        
    Returns:
        List of result dictionaries
    """
    results = []
    with open(results_file, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def evaluate_solution(fixed_code: str, tests: str, timeout: int = 5) -> bool:
    """
    Evaluate a single solution by running tests.
    
    Args:
        fixed_code: The fixed code to test
        tests: Test cases to run
        timeout: Maximum execution time
        
    Returns:
        True if all tests pass, False otherwise
    """
    try:
        result = execute_python_code(fixed_code, tests, timeout=timeout)
        return result["success"] and result["tests_passed"]
    except Exception as e:
        print(f"Error evaluating solution: {e}")
        return False


def calculate_pass_at_1(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate pass@1 metric.
    
    Args:
        results: List of agent results
        
    Returns:
        Dictionary with evaluation metrics
    """
    total = len(results)
    passed = 0
    failed = 0
    errors = 0
    
    detailed_results = []
    
    print(f"\nEvaluating {total} solutions...")
    print("-"*60)
    
    for result in tqdm(results, desc="Testing solutions"):
        task_id = result["task_id"]
        fixed_code = result.get("fixed_code", "")
        tests = result.get("tests", "")
        
        if not fixed_code or not tests:
            print(f"✗ Task {task_id}: Missing code or tests")
            errors += 1
            detailed_results.append({
                "task_id": task_id,
                "passed": False,
                "error": "Missing code or tests"
            })
            continue
        
        try:
            # Evaluate the solution
            success = evaluate_solution(fixed_code, tests)
            
            if success:
                passed += 1
                status = "✓ PASS"
            else:
                failed += 1
                status = "✗ FAIL"
            
            print(f"{status}: Task {task_id}")
            
            detailed_results.append({
                "task_id": task_id,
                "passed": success
            })
            
        except Exception as e:
            print(f"✗ ERROR: Task {task_id}: {e}")
            errors += 1
            failed += 1
            
            detailed_results.append({
                "task_id": task_id,
                "passed": False,
                "error": str(e)
            })
    
    # Calculate metrics
    pass_at_1 = (passed / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass@1": pass_at_1,
        "detailed_results": detailed_results
    }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate bug-fixing agent with pass@1")
    parser.add_argument(
        "--results",
        default="results/agent_solutions.jsonl",
        help="Path to agent results file"
    )
    parser.add_argument(
        "--output",
        default="results/evaluation.json",
        help="Path to save evaluation results"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout for code execution (seconds)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Evaluating Bug-Fixing Agent (pass@1)")
    print("="*60)
    
    # Load results
    print(f"\nLoading results from: {args.results}")
    try:
        results = load_results(args.results)
    except FileNotFoundError:
        print(f"Error: Results file not found: {args.results}")
        print("Please run 'python eval/run_agent_on_tasks.py' first.")
        sys.exit(1)
    
    # Evaluate
    evaluation = calculate_pass_at_1(results)
    
    # Save evaluation results
    print(f"\nSaving evaluation to: {args.output}")
    with open(args.output, 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"Total tasks:     {evaluation['total']}")
    print(f"Passed:          {evaluation['passed']}")
    print(f"Failed:          {evaluation['failed']}")
    print(f"Errors:          {evaluation['errors']}")
    print(f"\npass@1:          {evaluation['pass@1']:.2f}%")
    print("="*60)
    
    # Show some examples of failures if any
    if evaluation['failed'] > 0:
        print("\nFailed tasks (showing first 5):")
        failed_tasks = [r for r in evaluation['detailed_results'] if not r['passed']][:5]
        for task in failed_tasks:
            print(f"  - Task {task['task_id']}")
            if 'error' in task:
                print(f"    Error: {task['error']}")


if __name__ == "__main__":
    main()

