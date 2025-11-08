"""Loader for HumanEvalFix dataset from BigCode."""

from datasets import load_dataset
from typing import List, Dict, Any
import os
import csv


class HumanEvalFixLoader:
    """Load and process HumanEvalFix dataset."""
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize the loader.
        
        Args:
            cache_dir: Optional directory to cache the dataset
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/humanevalfix")
        self.dataset = None
        
    def load(self) -> List[Dict[str, Any]]:
        """
        Load the HumanEvalFix Python dataset.
        
        Returns:
            List of task dictionaries with keys:
            - task_id: Unique task identifier
            - buggy_code: The buggy Python code
            - fixed_code: The correct implementation (ground truth)
            - docstring: Function specification
            - tests: Test cases
        """
        print("Loading HumanEvalFix dataset...")
        
        try:
            # Load from HuggingFace datasets
            dataset = load_dataset(
                "bigcode/humanevalpack",
                "python",
                split="test",
                cache_dir=self.cache_dir
            )
            
            self.dataset = dataset
            
            # Process and format tasks
            tasks = []
            for idx, item in enumerate(dataset):
                task = self._process_item(item, idx)
                if task:
                    tasks.append(task)
            
            print(f"Loaded {len(tasks)} tasks from HumanEvalFix.")
            return tasks
            
        except Exception as e:
            print(f"Error loading dataset: {e}")
            print("Falling back to mock data for testing...")
            return self._get_mock_data()
    
    def _process_item(self, item: Dict[str, Any], idx: int) -> Dict[str, Any]:
        """
        Process a single dataset item.
        
        Args:
            item: Raw dataset item
            idx: Item index
            
        Returns:
            Processed task dictionary
        """
        try:
            # Extract fields (adjust based on actual dataset structure)
            task_id = item.get("task_id", str(idx))
            
            # HumanEvalFix typically has prompt (with docstring) and canonical_solution
            prompt = item.get("prompt", "")
            buggy_solution = item.get("buggy_solution", "")
            canonical_solution = item.get("canonical_solution", "")
            test = item.get("test", "")
            
            # Combine prompt and buggy solution
            buggy_code = prompt + buggy_solution if buggy_solution else prompt
            fixed_code = prompt + canonical_solution if canonical_solution else prompt
            
            return {
                "task_id": task_id,
                "buggy_code": buggy_code,
                "fixed_code": fixed_code,
                "docstring": prompt,
                "tests": test
            }
            
        except Exception as e:
            print(f"Error processing item {idx}: {e}")
            return None
    
    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """
        Generate mock data for testing when dataset is unavailable.
        
        Returns:
            List of mock task dictionaries
        """
        return [
            {
                "task_id": "0",
                "docstring": "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    ",
                "buggy_code": "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a - b",
                "fixed_code": "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a + b",
                "tests": "assert add(2, 3) == 5\nassert add(-1, 1) == 0\nassert add(0, 0) == 0"
            },
            {
                "task_id": "1",
                "docstring": "def multiply(a, b):\n    \"\"\"Multiply two numbers.\"\"\"\n    ",
                "buggy_code": "def multiply(a, b):\n    \"\"\"Multiply two numbers.\"\"\"\n    return a + b",
                "fixed_code": "def multiply(a, b):\n    \"\"\"Multiply two numbers.\"\"\"\n    return a * b",
                "tests": "assert multiply(2, 3) == 6\nassert multiply(-1, 5) == -5\nassert multiply(0, 10) == 0"
            },
            {
                "task_id": "2",
                "docstring": "def is_even(n):\n    \"\"\"Check if number is even.\"\"\"\n    ",
                "buggy_code": "def is_even(n):\n    \"\"\"Check if number is even.\"\"\"\n    return n % 2 == 1",
                "fixed_code": "def is_even(n):\n    \"\"\"Check if number is even.\"\"\"\n    return n % 2 == 0",
                "tests": "assert is_even(2) == True\nassert is_even(3) == False\nassert is_even(0) == True"
            }
        ]
    
    def get_task_by_id(self, task_id: str) -> Dict[str, Any]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task dictionary
        """
        tasks = self.load()
        for task in tasks:
            if task["task_id"] == task_id:
                return task
        return None
    
    def save_to_csv(self, tasks: List[Dict[str, Any]], output_path: str = "humanevalfix_dataset.csv") -> None:
        """
        Save the dataset to a CSV file.
        
        Args:
            tasks: List of task dictionaries to save
            output_path: Path to output CSV file
        """
        if not tasks:
            print("No tasks to save.")
            return
        
        # Define CSV columns
        fieldnames = ["task_id", "docstring", "buggy_code", "fixed_code", "tests"]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write rows
                for task in tasks:
                    writer.writerow({
                        "task_id": task.get("task_id", "").strip(),
                        "docstring": task.get("docstring", "").strip(),
                        "buggy_code": task.get("buggy_code", "").strip(),
                        "fixed_code": task.get("fixed_code", "").strip(),
                        "tests": task.get("tests", "").strip()
                    })
            
            print(f"Successfully saved {len(tasks)} tasks to {output_path}")
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")


if __name__ == "__main__":
    # Test the loader
    loader = HumanEvalFixLoader()
    tasks = loader.load()
    
    print(f"\nLoaded {len(tasks)} tasks")
    if tasks:
        print("\nFirst task:")
        print(f"Task ID: {tasks[0]['task_id']}")
        print(f"Buggy code:\n{tasks[0]['buggy_code']}")
        print(f"Tests:\n{tasks[0]['tests']}")
        
        # Save to CSV
        print("\nSaving dataset to CSV...")
        loader.save_to_csv(tasks, "humanevalfix_dataset.csv")

