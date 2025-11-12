# Python Bug-Fixing LLM Agent

A local LLM-based agent that fixes buggy Python code using a **ReAct-style workflow** with LangGraph. The agent is evaluated on the **HumanEvalFix (Python)** benchmark using the **pass@1** metric.

# Features

- ReAct-style workflow
- LangGraph
- HumanEvalFix dataset (Python)
- Local model
- Tools: read_file, write_file, run_tests

# Usage

Create environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  
```

Upload requirements.txt:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Load model (prefer `qwen2.5:14b`):
```bash
ollama pull <model-name>
```

Run agent using HumanEvalFix datasets:
```bash
python run.py
```

# Flow
For giving context to the agent, it reads the code from the file and runs the tests initially and then goes to loop. 

Agent needs this context anyway, so it reduces unnecessary calls to the model to call these tools and saves time.
```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
    __start__([<p>__start__</p>]):::first
    read_code(read_code)
    run_tests_initial(run_tests_initial)
    agent(agent)
    tools(tools)
    __end__([<p>__end__</p>]):::last
    __start__ --> read_code;
    agent -. &nbsp;end&nbsp; .-> __end__;
    agent -. &nbsp;continue&nbsp; .-> tools;
    read_code --> run_tests_initial;
    run_tests_initial --> agent;
    tools --> agent;
    classDef default fill:#f2fff,line-height:1.2
    classDef first fill-opacity:0
    classDef last fill:#bfb6fc
```

# Datasets 
- Large: full HumanEvalFix dataset (164 examples)
- Tiny: one random example per each bug_type from HumanEalFix (6 examples)

# Evaluation
pass@1 metric 

Run generated code with predefined tests and check if it passes all tests or some error occurred.

# Experiments
I tried different local models from [BFCL](https://huggingface.co/spaces/gorilla-llm/berkeley-function-calling-leaderboard). Started with Qwen models on Ollama.

Using models with small corpus size (<10B) led to such problems:
- Eager invocation: Tools for reading and testing were being called again despite the fact that they were already called before.
- Invalid arguments: Parameters are missed or malformed.
- Ignored responses: The model often failed to respond to tool output, leading to awkward or incomplete conversations.
- Early stopping: The model stopped responding to the user after a few calls not getting passed all tests.

Inference time is big (I run on M4 GPU):

Qwen3:
```
qwen3:4b: avg 127s per llm call
qwen3:8b: avg 102s per llm call
```

Qwen2.5:
```
qwen2.5:7b-instruct: avg 4s per llm call
qwen2.5:14b: avg 42s per llm call
```

Why such a difference? Less corpus size, but more time.
- Thinking mode – Qwen3 performs internal reasoning before output, making it slower. 
- 262K tokens context in Qwen3, 32K tokens in Qwen2.5. Ollama allocates KV-cache for the full window even if you use only a few thousand tokens → heavy memory load.

Due to high inference time large dataset is not suitable for iterative improvements, so try on tiny.

Evaluation on tiny dataset.
Versions:
- v1
    Total tasks: 6
    ✓ Tests passed: 3 (50.0%)
    ✗ Tests failed: 1 (16.7%)
    ⏱ Timeouts: 0 (0.0%)
    ✗ Execution errors: 2 (33.3%)
    --------------------------------------------------------------------------------
    FAILED TESTS:
    --------------------------------------------------------------------------------
      • Python/158, bug type: missing logic, t1
    --------------------------------------------------------------------------------
    EXECUTION ERRORS:
    --------------------------------------------------------------------------------
      • Python/150, bug type: excess logic, SyntaxError: invalid syntax (<string>, line 10)
      • Python/123, bug type: value misuse, SyntaxError: invalid syntax (<string>, line 16)

- v2 
    Total tasks: 6
    ✓ Tests passed: 3 (50.0%)
    ✗ Tests failed: 2 (33.3%)
    ⏱ Timeouts: 0 (0.0%)
    ✗ Execution errors: 1 (16.7%)
    --------------------------------------------------------------------------------
    FAILED TESTS:
    --------------------------------------------------------------------------------
      • Python/158, bug type: missing logic, t2
      • Python/150, bug type: excess logic, 
    
    --------------------------------------------------------------------------------
    EXECUTION ERRORS:
    --------------------------------------------------------------------------------
      • Python/87, bug type: variable misuse, SyntaxError: invalid syntax (<string>, line 3)

# Summary 
Experiments show that:

- Small local models (<10B) struggle with reliable tool use:
  - repeated tool calls,
  - malformed arguments,
  - ignoring tool outputs,
  - early stopping.
- Qwen3 models are significantly slower due to:
  - internal "thinking mode",
  - large 262K context window → heavy KV-cache allocation in Ollama.
- Qwen2.5 models (7B/14B) are faster and more stable with tools but still produce syntax errors or incomplete fixes.

On the tiny HumanEvalFix subset (6 tasks), both model versions achieved **~50% pass@1**, with several syntax errors and failed test cases.

Overall, reliable local debugging agents remain challenging with small models, and performance strongly depends on:
- model's tool-handling capability,
- prompt design and tools themselves (but it is still hard to enhance iteratively with such a long inference time).
