from typing import (
    Annotated,
    Sequence,
    TypedDict,
)
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langchain_community.tools import ReadFileTool
from langchain_community.tools import WriteFileTool

prompt = """You are an autonomous Python debugging agent. Your task is to fix failing code by using the available tools until all tests pass.

**Available Tools:**
- `run_tests`: Execute the test suite and see which tests pass/fail
- `read_file`: Read the contents of code files to understand the current implementation
- `write_file`: Write updated code to files (always overwrites the entire file)

**Your Workflow:**
You must follow this exact sequence:

1. **Run Tests**: Call `run_tests` to see current test status
2. **Check Results**: 
   - If ALL tests pass → respond with exactly "DONE" 
   - If ANY tests fail → proceed to step 3
3. **Read Code**: Call `read_file` to examine the failing code
4. **Fix Code**: Make targeted, minimal fixes to address the specific test failures
5. **Write Code**: Call `write_file` with the complete updated file content. Always write in the same file.
6. **Repeat**: Go back to step 1

**Critical Instructions:**
- Always begin by calling `run_tests` first
- Always write code in the same file
- Only respond "DONE" when ALL tests pass
- When writing files, include the complete file content (overwrite entirely)
- Make minimal, targeted fixes - don't change unrelated code
- If you get the same test failure multiple times, try a different approach

Begin by running the tests to see the current status. Your output should consist only of tool calls or "DONE" and should not duplicate or rehash any of the analysis work you did in the thinking block.
"""

class AgentState(TypedDict):
    """The state of the agent."""

    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]

from langchain_core.tools import tool

local_llm = "qwen2.5:14b"
model = ChatOllama(model=local_llm)

from tools import *
read_file = ReadFileTool()
write_file = WriteFileTool()

tools = [read_file, write_file, run_tests]

model = model.bind_tools(tools)

import json
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

tools_by_name = {tool.name: tool for tool in tools}


# Define our tool node
def tool_node(state: AgentState):
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}


# Define the node that calls the model
def call_model(
    state: AgentState,
    config: RunnableConfig,
):
    # this is similar to customizing the create_react_agent with 'prompt' parameter, but is more flexible
    system_prompt = SystemMessage(prompt)
    response = model.invoke([system_prompt] + state["messages"], config)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define the conditional edge that determines whether to continue or not
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"

from langgraph.graph import StateGraph, END

# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "tools",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("tools", "agent")

# Now we can compile and visualize our graph
graph = workflow.compile()

from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass

# Helper function for formatting the stream nicely
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

path = "code_1.py"
test = readfile("test.py")
inputs = {"messages": [("user", "Fix bugs in the code. Code file path:"+path+". Now this tests failed:\n"+test+"")]}
print_stream(graph.stream(inputs,
                          stream_mode="values",
                          config={"max_iterations": 50}))