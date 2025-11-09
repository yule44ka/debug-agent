import json

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_community.tools import ReadFileTool
from langchain_community.tools import WriteFileTool
from langgraph.prebuilt import create_react_agent

from tools import *

read_file = ReadFileTool()
write_file = WriteFileTool()

from langchain_ollama import ChatOllama

prompt = """You are a professional Python developer specializing in debugging and fixing code issues. Your task is to systematically identify and resolve bugs in Python code using the available tools.

You have access to the following tools to help you debug:
- `read_file`: Read the contents of a file
- `write_file`: Write updated code to a file  
- `lint_compile_python`: Check code for syntax errors and compilation issues
- `run_tests`: Execute the tests to verify your fixes

Your goal is to fix all bugs so that the tests pass without any errors.

Instructions:
1. Use the linter to check for any syntax errors or compilation issues.

2. Run tests to check if the tests pass.

3. Read the code file to examine the current implementation.

4. Develop a systematic debugging approach based on your analysis.

5. Make targeted fixes to address the identified issues.

6. Write the corrected code back to the file.

7. Run the tests to verify your fixes work.

8. If tests still fail, repeat the process with additional analysis and refinements.

9. Continue this cycle until all tests pass successfully.

Before you begin making changes, conduct a thorough analysis in <debugging_analysis> tags. It's OK for this section to be quite long. In your analysis:

- Break down each failed test line by line, identifying exactly what behavior is expected vs what's currently happening
- Based on the test failures, predict what types of bugs might exist in the code (e.g., logic errors, missing functionality, incorrect return types)
- Plan out the specific sequence of tool calls you'll make (e.g., "First I'll read the file, then run lint_compile_python, then...")  
- Consider potential complications you might encounter and how you'll address them
- Outline your systematic approach for making and testing fixes

After your analysis, proceed with the debugging process, clearly explaining each step you take and the reasoning behind your fixes."""

# qwen2.5 - 14b (#30 on BFCL leaderboard)
local_llm = "qwen2.5:14b"
model = ChatOllama(model=local_llm)

agent = create_react_agent(
    model,
    tools=[read_file, write_file, lint_compile_python, run_tests],
    prompt=prompt,
)

# Run the agent
path = "code_1.py"
test = readfile("test.py")
result = agent.invoke(
    {"messages": [{"role": "user", "content": f"Fix bugs in the code. Code file path:{path}. Now this tests failed:{test}"}]}
)

try:
    print(json.dumps(result, indent=2, ensure_ascii=False))
except (TypeError, ValueError):
    if hasattr(result, 'dict'):
        print(json.dumps(result.dict(), indent=2, ensure_ascii=False))
    elif hasattr(result, '__dict__'):
        print(json.dumps(result.__dict__, indent=2, ensure_ascii=False, default=str))
    else:
        from pprint import pprint
        pprint(result, indent=2, width=100)