# Python Bug-Fixing LLM Agent

A local LLM-based agent that fixes buggy Python code using a **ReAct-style workflow** with LangGraph. The agent is evaluated on the **HumanEvalFix (Python)** benchmark using the **pass@1** metric.

## Overview

This project implements an autonomous debugging agent that:
- Analyzes buggy Python code and test specifications
- Uses iterative ReAct reasoning (Reason → Act → Observe)
- Executes code in a sandboxed environment to verify fixes
- Automatically refines solutions based on test feedback
- Achieves measurable performance on standard benchmarks

**Recommended Model**: Qwen2.5-0.5B-Instruct (small, open-source, runs locally on Mac)

---

## Project Structure

```
debug-agent/
├── agents/
│   ├── __init__.py
│   ├── fix_bug_agent.py        # LangGraph ReAct agent implementation
│   └── tools.py                # Code execution sandbox tool
├── data/
│   ├── __init__.py
│   └── humanevalfix/
│       ├── __init__.py
│       └── loader.py           # HumanEvalFix dataset loader
├── eval/
│   ├── __init__.py
│   ├── run_agent_on_tasks.py   # Run agent on all benchmark tasks
│   └── evaluate_pass_at1.py    # Compute pass@1 metric
├── results/                     # Generated during evaluation
│   ├── agent_solutions.jsonl   # Agent's fixed code for each task
│   └── evaluation.json         # Final pass@1 results
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Main dependencies:**
- `langgraph` - Graph-based agent orchestration
- `langchain` - LLM integration framework
- `transformers` - HuggingFace model loading
- `datasets` - HumanEvalFix dataset access
- `torch` - Deep learning backend

### 3. Download Dataset (Optional)

The dataset will download automatically on first run, but you can pre-download:

```python
from datasets import load_dataset
load_dataset("bigcode/humanevalpack", "python")
```

**Note**: The project includes mock data for testing if the dataset is unavailable.

---

## Agent Architecture

### ReAct Workflow (LangGraph)

The agent uses a **ReAct loop** (Reasoning + Acting):

```
┌─────────────────────────────────────────────────┐
│  1. ANALYZE: Read buggy code + docstring        │
│  2. REASON: Identify potential bug              │
│  3. ACT: Generate fix and test with tool        │
│  4. OBSERVE: Review test results                │
│  5. REFINE: If tests fail, iterate              │
│  6. OUTPUT: Return fixed code when tests pass   │
└─────────────────────────────────────────────────┘
```

### Components

1. **LLM** (Qwen2.5-0.5B-Instruct)
   - Small, efficient model for local execution
   - Generates fixes based on error analysis
   - Runs on CPU or GPU

2. **Code Execution Tool**
   - Safely executes Python code with tests
   - Sandboxed environment with timeout
   - Returns detailed error messages for debugging

3. **LangGraph State Machine**
   - Manages ReAct iteration loop
   - Handles tool calls and responses
   - Limits iterations to prevent infinite loops

### Key Features

- **Iterative Refinement**: Agent learns from test failures
- **Safe Execution**: Sandboxed code execution with timeouts
- **Automatic Fallback**: Uses mock LLM if model fails to load
- **Limit Controls**: Max iterations prevent runaway loops (default: 5)

---

## Usage

### Quick Start

```bash
# Run agent on all tasks (or limited set for testing)
python eval/run_agent_on_tasks.py --limit 10

# Evaluate results with pass@1 metric
python eval/evaluate_pass_at1.py
```

### Full Benchmark Run

```bash
# Run on full dataset (may take several hours)
python eval/run_agent_on_tasks.py

# Evaluate
python eval/evaluate_pass_at1.py
```

### Command-Line Options

**run_agent_on_tasks.py:**
```bash
python eval/run_agent_on_tasks.py \
  --output results/solutions.jsonl \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --max-iterations 5 \
  --limit 10  # Optional: limit for testing
```

**evaluate_pass_at1.py:**
```bash
python eval/evaluate_pass_at1.py \
  --results results/agent_solutions.jsonl \
  --output results/evaluation.json \
  --timeout 5
```

---

## Evaluation Metrics

### pass@1

The primary metric is **pass@1**: the percentage of problems solved correctly on the first attempt.

**Formula:**
```
pass@1 = (number of tasks with passing tests / total tasks) × 100%
```

**HumanEvalFix Benchmark:**
- Dataset: ~164 buggy Python functions
- Each task includes: buggy code, docstring (spec), and unit tests
- Success = all unit tests pass for the fixed code

## Testing Individual Components

### Test Code Execution Tool

```bash
python agents/tools.py
```

### Test Bug-Fixing Agent

```bash
python agents/fix_bug_agent.py
```

### Test Dataset Loader

```bash
python data/humanevalfix/loader.py
```

---

## Performance Tips

### For Faster Evaluation
1. Use `--limit` to test on subset first
2. Run on GPU if available (set `CUDA_VISIBLE_DEVICES`)
3. Use smaller models (0.5B → 1.5B → 7B)

### For Better Accuracy
1. Increase `--max-iterations` (more chances to fix)
2. Use larger models (7B or 13B parameters)
3. Tune the ReAct prompt for your specific bug types

