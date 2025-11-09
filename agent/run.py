import os
import pandas as pd
from pathlib import Path
import sys

# Import the agent components
from agent import create_agent, print_stream


def run(version: str):
    """
    Main function to run the debugging agent on the HumanEvalFix dataset.
    
    Args:
        version: Version identifier for the agent (e.g., "v1", "v2")
    """
    # 1. Read the input CSV
    csv_path = Path(__file__).parent.parent / "data" / "humanevalfix" / "humanevalfix_dataset.csv"
    print(f"Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)[1:]
    
    # Prepare results column
    results = []
    
    # 2. Create tmp directory structure if it doesn't exist
    tmp_dir = Path(__file__).parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "code").mkdir(exist_ok=True)
    (tmp_dir / "test").mkdir(exist_ok=True)
    print(f"Temporary directory: {tmp_dir}")
    
    # Store original working directory
    original_dir = os.getcwd()
    agent_dir = Path(__file__).parent
    
    # Change to agent directory (since tools.py expects test.py in current directory)
    os.chdir(agent_dir)
    
    # Create agent instance
    print("Creating agent instance...")
    graph = create_agent()
    print("✓ Agent instance created")
    
    try:
        # Iterate through all rows
        for idx, row in df.iterrows():
            print(f"\n{'='*80}")
            print(f"Processing row {idx + 1}/{len(df)}")
            print(f"{'='*80}")
            
            # 3. Extract data from row
            task_id = row['task_id'].split("/")[-1]  # ID
            buggy_function = row['buggy_function']
            test_text = row['test']

            print(f"Task ID: {task_id}")
            
            # 4. Prepare the code file
            code_filename = f"code_{task_id}.py"
            code_filepath = tmp_dir / "code" / code_filename
            
            # Write buggy function to the code file
            with open(code_filepath, 'w', encoding='utf-8') as f:
                f.write(buggy_function)
            print(f"Created code file: {code_filepath}")
            
            # Also save test to test subdirectory for reference
            test_backup_filepath = tmp_dir / "test" / f"test_{task_id}.py"
            with open(test_backup_filepath, 'w', encoding='utf-8') as f:
                f.write(test_text)
            
            # Write test to test.py in agent directory (required by run_tests tool)
            test_filepath = agent_dir / "test.py"
            with open(test_filepath, 'w', encoding='utf-8') as f:
                f.write(test_text)
            print(f"Created test file: {test_filepath}")
            
            # 5. Instantiate and run the agent
            try:
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
                
                print(f"\nRunning agent on {relative_code_path}...")
                
                # Stream the agent execution using print_stream
                stream = graph.stream(
                    inputs,
                    stream_mode="values",
                    config={"max_iterations": 50}
                )
                print_stream(stream)
                print("✓ Agent completed")
                
                # 6. Collect the final code
                print(f"\nReading fixed code from: {code_filepath}")
                with open(code_filepath, 'r', encoding='utf-8') as f:
                    fixed_code = f.read()
                
                results.append(fixed_code)
                print(f"✓ Successfully processed {task_id}")
                
            except Exception as e:
                print(f"✗ Error processing {task_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                # Store original buggy code if agent fails
                results.append(buggy_function)
        
        # 7. Write results into a new results CSV
        print(f"\n{'='*80}")
        print("Saving results...")
        print(f"{'='*80}")
        
        # Add the version column with results
        df[version] = results
        
        # 8. Save results as a new CSV
        results_path = Path(__file__).parent.parent / f"results_{version}.csv"
        df.to_csv(results_path, index=False)
        print(f"✓ Results saved to: {results_path}")
        print(f"Total rows processed: {len(df)}")
        
    finally:
        # Restore original working directory
        os.chdir(original_dir)
        
        # Clean up test.py in agent directory
        test_file = agent_dir / "test.py"
        if test_file.exists():
            test_file.unlink()
            print(f"Cleaned up: {test_file}")


if __name__ == "__main__":
    # Get version from command line argument or use default
    version = input("Enter version: ") or "v1"
    
    print(f"Starting debug agent run with version: {version}")
    run(version)
    print("\n✓ All done!")

