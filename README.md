# Python Bug-Fixing LLM Agent

A local LLM-based agent that fixes buggy Python code using a **ReAct-style workflow** with LangGraph. The agent is evaluated on the **HumanEvalFix (Python)** benchmark using the **pass@1** metric.

# Features

- ReAct-style workflow
- LangGraph
- HumanEvalFix (Python)
- Local model: qwen2.5:14b
- Tools: read_file, write_file, run_tests

# Usage

Upload requirements.txt:
```bash
pip install -r requirements.txt
```

Run agent using HumanEvalFix dataset:
```bash
python run.py
```

# Flow
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

# Evaluation
pass@1 metric
