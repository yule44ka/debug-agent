"""Run the bug-fixing agent on all HumanEvalFix tasks."""

import json
import os
import sys
from tqdm import tqdm
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.humanevalfix.loader import HumanEvalFixLoader
from agents.fix_bug_agent import BugFixAgent


def run_agent_on_all_tasks(
    output_file: str = "results/agent_solutions.jsonl",
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
    max_iterations: int = 5,
    limit: int = None
):
    """
    Run the agent on all HumanEvalFix tasks.
    
    Args:
        output_file: Path to save results
        model_name: HuggingFace model name
        max_iterations: Maximum iterations per task
        limit: Optional limit on number of tasks to process
    """
    print("="*60)
    print("Running Bug-Fixing Agent on HumanEvalFix")
    print("="*60)
    
    # Create output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Load dataset
    loader = HumanEvalFixLoader()
    tasks = loader.load()
    
    if limit:
        tasks = tasks[:limit]
        print(f"Limited to {limit} tasks for testing")
    
    # Initialize agent
    print(f"\nInitializing agent with model: {model_name}")
    agent = BugFixAgent(model_name=model_name, max_iterations=max_iterations)
    
    # Process tasks
    results = []
    successful = 0
    failed = 0
    
    print(f"\nProcessing {len(tasks)} tasks...")
    print("-"*60)
    
    for task in tqdm(tasks, desc="Fixing bugs"):
        try:
            task_id = task["task_id"]
            buggy_code = task["buggy_code"]
            docstring = task["docstring"]
            tests = task["tests"]
            
            print(f"\nTask {task_id}: Attempting to fix bug...")
            
            # Run agent
            fixed_code = agent.fix_bug(
                buggy_code=buggy_code,
                docstring=docstring,
                tests=tests
            )
            
            # Save result
            result = {
                "task_id": task_id,
                "buggy_code": buggy_code,
                "fixed_code": fixed_code,
                "docstring": docstring,
                "tests": tests
            }
            results.append(result)
            successful += 1
            
            print(f"✓ Task {task_id} completed")
            
        except Exception as e:
            print(f"✗ Error on task {task_id}: {e}")
            failed += 1
            
            # Save partial result
            result = {
                "task_id": task_id,
                "buggy_code": buggy_code,
                "fixed_code": buggy_code,  # Fallback to buggy code
                "error": str(e)
            }
            results.append(result)
    
    # Save all results
    print(f"\n{'='*60}")
    print(f"Saving results to {output_file}")
    
    with open(output_file, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    print(f"{'='*60}")
    print(f"Summary:")
    print(f"  Total tasks: {len(tasks)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Results saved to: {output_file}")
    print(f"{'='*60}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run bug-fixing agent on HumanEvalFix")
    parser.add_argument(
        "--output", 
        default="results/agent_solutions.jsonl",
        help="Output file path"
    )
    parser.add_argument(
        "--model",
        default="Qwen/Qwen2.5-0.5B-Instruct",
        help="HuggingFace model name"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum iterations per task"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of tasks (for testing)"
    )
    
    args = parser.parse_args()
    
    run_agent_on_all_tasks(
        output_file=args.output,
        model_name=args.model,
        max_iterations=args.max_iterations,
        limit=args.limit
    )


if __name__ == "__main__":
    main()

