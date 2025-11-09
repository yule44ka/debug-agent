# pip install -q datasets
from datasets import load_dataset
import pandas as pd

# Languages: "python", "js", "java", "go", "cpp", "rust"
ds = load_dataset("bigcode/humanevalpack", "python")["test"]

# Convert to pandas DataFrame
df = pd.DataFrame(ds)

# Add buggy_code column: declaration + buggy_solution
df['buggy_code'] = df['declaration'] + df['buggy_solution'] + df['test']
df['buggy_function'] = df['declaration'] + df['buggy_solution']

# Add canonical_code column: declaration + canonical_solution
df['canonical_code'] = df['declaration'] + df['canonical_solution'] + df['test']
df['canonical_function'] = df['declaration'] + df['canonical_solution']

# Save to CSV
output_path = "humanevalfix_dataset.csv"
df.to_csv(output_path, index=False)

print(f"Dataset saved to {output_path}")
print(f"Total records: {len(df)}")
print(f"Columns: {list(df.columns)}")


