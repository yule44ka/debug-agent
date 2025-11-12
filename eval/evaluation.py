import pandas as pd
import sys
from pathlib import Path
import signal


class TimeoutError(Exception):
    """Custom timeout exception"""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal"""
    raise TimeoutError("Test execution timed out")


def run_code_with_timeout(code: str, timeout_seconds: int = 5):
    """
    Execute code with a timeout.
    
    Args:
        code: Python code to execute
        timeout_seconds: Maximum execution time in seconds
        
    Raises:
        TimeoutError: If execution exceeds timeout
    """
    # Set up the timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        namespace = {}
        exec(code, namespace)
    finally:
        # Disable the alarm
        signal.alarm(0)


def run_tests(csv_path: str, version: str, timeout: int = 5):
    """
    Loads CSV file, combines canonical_code with tests and runs the check function.
    
    Args:
        csv_path: Path to CSV file with data
        version: Column name to use for code ('canonical_code' or 'buggy_code')
        timeout: Maximum execution time per test in seconds (default: 5)
    """
    # Load CSV
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} tasks from dataset")
    print("-" * 80)
    
    results = {
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'timeout': 0
    }

    failed_tasks = []
    error_tasks = []
    timeout_tasks = []
    
    # Iterate through each row in the dataset
    for idx, row in df.iterrows():
        task_id = row['task_id']
        bug_type = row['bug_type']
        column = version
        code = row[column]
        if code == "" or type(code) != str:
            continue
        # Combine code and test
        full_code = code + row['test']
        
        print(f"[{idx + 1}/{len(df)}] Running tests for task {task_id}, bug type: {bug_type}...", end=" ")
        
        try:
            # Execute code with timeout
            run_code_with_timeout(full_code, timeout)
            
            # If we got here without exceptions, test passed
            print("✓ PASSED")
            results['passed'] += 1
            
        except TimeoutError:
            print(f"⏱ TIMEOUT")
            results['timeout'] += 1
            timeout_tasks.append({
                'task_id': task_id,
                'error': f"Execution exceeded {timeout} seconds",
                'bug_type': bug_type
            })
            
        except AssertionError as e:
            print(f"✗ FAILED")
            results['failed'] += 1
            failed_tasks.append({
                'task_id': task_id,
                'error': str(e),
                'bug_type': bug_type,
            })
            
        except Exception as e:
            print(f"✗ ERROR: {type(e).__name__}")
            results['errors'] += 1
            error_tasks.append({
                'task_id': task_id,
                'error': f"{type(e).__name__}: {str(e)}",
                'bug_type': bug_type,
            })
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Total tasks: {len(df)}")
    print(f"✓ Tests passed: {results['passed']} ({results['passed']/len(df)*100:.1f}%)")
    print(f"✗ Tests failed: {results['failed']} ({results['failed']/len(df)*100:.1f}%)")
    print(f"⏱ Timeouts: {results['timeout']} ({results['timeout']/len(df)*100:.1f}%)")
    print(f"✗ Execution errors: {results['errors']} ({results['errors']/len(df)*100:.1f}%)")
    
    # Show failure details if any
    if failed_tasks:
        print("\n" + "-" * 80)
        print("FAILED TESTS:")
        print("-" * 80)
        for task in failed_tasks[:10]:  # Show first 10
            print(f"  • {task['task_id']}, bug type: {task["bug_type"]}, {task['error']}")
        if len(failed_tasks) > 10:
            print(f"  ... and {len(failed_tasks) - 10} more failures")
    
    # Show timeout details if any
    if timeout_tasks:
        print("\n" + "-" * 80)
        print("TIMEOUT TASKS:")
        print("-" * 80)
        for task in timeout_tasks[:10]:  # Show first 10
            print(f"  • {task['task_id']}, bug type: {task["bug_type"]}, {task['error']}")
        if len(timeout_tasks) > 10:
            print(f"  ... and {len(timeout_tasks) - 10} more timeouts")
    
    # Show error details if any
    if error_tasks:
        print("\n" + "-" * 80)
        print("EXECUTION ERRORS:")
        print("-" * 80)
        for task in error_tasks[:10]:  # Show first 10
            print(f"  • {task['task_id']}, bug type: {task["bug_type"]}, {task['error']}")
        if len(error_tasks) > 10:
            print(f"  ... and {len(error_tasks) - 10} more errors")
    
    return results


def main():
    # Define path to CSV file
    project_root = Path(__file__).parent.parent

    # Get version from command line argument or use default
    version = input("Enter version (v1 is default): ") or "v1"
    dataset = input("Enter dataset (tiny is default): ") or "tiny"

    csv_path = project_root / "results" / f"results_{dataset}_{version}.csv"
    if not csv_path.exists():
        print(f"Error: File {csv_path} not found!")
        sys.exit(1)
    
    # Run tests
    timeout = 5  # seconds
    results = run_tests(str(csv_path), version, timeout)
    
    # Return exit code based on results
    if results['failed'] > 0 or results['errors'] > 0 or results['timeout'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
