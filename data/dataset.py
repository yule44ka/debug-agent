import pandas as pd
import random
from pathlib import Path

def create_tiny_dataset(seed=42):
    """
    Create a tiny dataset with one random example from each bug type.
    """
    # Set random seed for reproducibility
    random.seed(seed)
    
    # Read the full dataset
    data_dir = Path(__file__).parent
    full_dataset_path = data_dir / "humanevalfix" / "humanevalfix_large.csv"
    tiny_dataset_path = data_dir / "humanevalfix" / "humanevalfix_tiny.csv"
    
    print(f"Reading full dataset from: {full_dataset_path}")
    df = pd.read_csv(full_dataset_path)
    
    print(f"Full dataset size: {len(df)} examples")
    
    # Get unique bug types
    bug_types = df['bug_type'].unique()
    print(f"\nBug types found: {list(bug_types)}")
    
    # Sample one random example from each bug type
    tiny_samples = []
    for bug_type in bug_types:
        bug_df = df[df['bug_type'] == bug_type]
        sample = bug_df.sample(n=1, random_state=seed)
        tiny_samples.append(sample)
        print(f"  - {bug_type}: {len(bug_df)} examples available, sampled: {sample['task_id'].values[0]}")
    
    # Combine all samples
    tiny_df = pd.concat(tiny_samples, ignore_index=True)
    
    # Save the tiny dataset
    tiny_df.to_csv(tiny_dataset_path, index=False)
    
    print(f"\nTiny dataset created with {len(tiny_df)} examples (one per bug type)")
    print(f"Saved to: {tiny_dataset_path}")
    
    return tiny_df

if __name__ == "__main__":
    tiny_df = create_tiny_dataset()
    print("\nTask IDs in tiny dataset:")
    print(tiny_df['task_id'].tolist())

