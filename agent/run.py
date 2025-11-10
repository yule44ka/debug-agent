import os
import pandas as pd
from pathlib import Path
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple

# Import the agent components
from agent import create_agent, print_stream


def process_single_row(args: Tuple) -> Tuple[int, str]:
    """
    Process a single row from the dataset.
    This function runs in a separate process.
    
    Args:
        args: Tuple of (idx, row_data, version, agent_dir, tmp_dir)
        
    Returns:
        Tuple of (index, fixed_code)
    """
    idx, row_data, version, agent_dir, tmp_dir = args
    
    # Extract data from row
    task_id = row_data['task_id'].split("/")[-1]
    buggy_function = row_data['buggy_function']
    test_text = row_data['test']
    
    print(f"\n[Worker {os.getpid()}] Processing Task ID: {task_id} (row {idx})")
    
    try:
        # Change to agent directory
        os.chdir(agent_dir)
        
        # Prepare the code file with process-specific naming to avoid conflicts
        code_filename = f"code_{task_id}.py"
        code_filepath = tmp_dir / "code" / code_filename
        
        # Write buggy function to the code file
        with open(code_filepath, 'w', encoding='utf-8') as f:
            f.write(buggy_function)
        
        # Save test to test subdirectory (tools.py reads from here)
        test_backup_filepath = tmp_dir / "test" / f"test_{task_id}.py"
        with open(test_backup_filepath, 'w', encoding='utf-8') as f:
            f.write(test_text)
        
        # Create agent instance for this process
        graph = create_agent()
        
        # Create relative path from agent directory to code file
        relative_code_path = f"tmp/code/{code_filename}"
        
        # Prepare inputs for the agent
        inputs = {
            "messages": [(
                "user", 
                f"Fix bugs in the code. Code file path: {relative_code_path}. "
                f"Now this tests failed:\n{test_text}"
            )]
        }
        
        print(f"[Worker {os.getpid()}] Running agent on {relative_code_path}...")
        
        # Stream the agent execution
        stream = graph.stream(
            inputs,
            stream_mode="values",
            config={"max_iterations": 50}
        )
        print_stream(stream)
        
        # Read the fixed code
        with open(code_filepath, 'r', encoding='utf-8') as f:
            fixed_code = f.read()
        
        print(f"[Worker {os.getpid()}] ✓ Successfully processed {task_id}")
        return (idx, fixed_code)
        
    except Exception as e:
        print(f"[Worker {os.getpid()}] ✗ Error processing {task_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return original buggy code if agent fails
        return (idx, buggy_function)


def run(version: str, dataset: str):
    """
    Main function to run the debugging agent on the HumanEvalFix dataset.
    
    Args:
        version: Version identifier for the agent (e.g., "v1", "v2")
    """
    # 1. Read the input CSV
    csv_path = Path(__file__).parent.parent / "data" / "humanevalfix" / f"humanevalfix_{dataset}.csv"
    print(f"Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # 2. Create tmp directory structure if it doesn't exist
    tmp_dir = Path(__file__).parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "code").mkdir(exist_ok=True)
    (tmp_dir / "test").mkdir(exist_ok=True)
    print(f"Temporary directory: {tmp_dir}")
    
    # Store original working directory
    original_dir = os.getcwd()
    agent_dir = Path(__file__).parent
    
    # Number of parallel workers
    NUM_WORKERS = 1
    
    print(f"Running with {NUM_WORKERS} parallel workers")
    
    # Define results CSV path
    results_path = Path(__file__).parent.parent / "results" / f"results_{dataset}_{version}.csv"
    
    try:
        # Check if results file already exists and load previous results
        if results_path.exists():
            print(f"Found existing results file: {results_path}")
            existing_results = pd.read_csv(results_path)
            if version in existing_results.columns:
                # Merge existing results into the current dataframe
                df[version] = existing_results[version]
                print(f"Loaded existing results for version '{version}'")
            else:
                df[version] = ""
        else:
            # Initialize results column in DataFrame with empty strings
            df[version] = ""
        
        # Count how many rows already have results
        completed_mask = df[version].notna() & (df[version] != "")
        already_completed = completed_mask.sum()
        
        if already_completed > 0:
            print(f"Found {already_completed} rows already completed, skipping them")
        
        # Prepare arguments only for rows that need processing
        row_args = []
        for idx, row in df.iterrows():
            # Skip rows that already have results
            if completed_mask.loc[idx]:
                print(f"Skipping row {idx} (already completed)")
                continue
                
            row_data = {
                'task_id': row['task_id'],
                'buggy_function': row['buggy_function'],
                'test': row['test']
            }
            row_args.append((idx, row_data, version, agent_dir, tmp_dir))
        
        # Check if there's anything to process
        if len(row_args) == 0:
            print(f"\n{'='*80}")
            print("All rows already completed! Nothing to process.")
            print(f"{'='*80}")
            return
        
        # Process rows in parallel with 8 workers
        print(f"\n{'='*80}")
        print(f"Processing {len(row_args)} rows with {NUM_WORKERS} parallel workers...")
        print(f"Already completed: {already_completed}/{len(df)}")
        print(f"{'='*80}\n")
        
        # Save initial CSV state
        df.to_csv(results_path, index=False)
        print(f"Results file: {results_path}")
        
        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
            # Submit all tasks
            future_to_idx = {executor.submit(process_single_row, arg): arg[0] 
                           for arg in row_args}
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result_idx, fixed_code = future.result()
                    
                    # Update DataFrame with the result
                    df.at[result_idx, version] = fixed_code
                    
                    # Save updated CSV immediately
                    df.to_csv(results_path, index=False)
                    
                    completed += 1
                    print(f"\n{'='*80}")
                    print(f"Progress: {completed}/{len(row_args)} tasks completed")
                    print(f"✓ CSV updated with result for row {result_idx}")
                    print(f"{'='*80}\n")
                except Exception as e:
                    print(f"✗ Task {idx} generated an exception: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Store empty string for failed tasks and save
                    df.at[idx, version] = ""
                    df.to_csv(results_path, index=False)
        
        # Final summary
        print(f"\n{'='*80}")
        print("All tasks completed!")
        print(f"{'='*80}")
        print(f"✓ Final results saved to: {results_path}")
        print(f"Total rows processed: {len(df)}")
        
    finally:
        # Restore original working directory
        os.chdir(original_dir)


if __name__ == "__main__":
    # Get version from command line argument or use default
    version = input("Enter version (v1 is default): ") or "v1"
    dataset = input("Enter dataset (tiny is default): ") or "tiny"
    
    print(f"Starting debug agent run with version: {version}")
    run(version, dataset)
    print("\n✓ All done!")

