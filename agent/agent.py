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
from prompt import get_prompt

prompt = get_prompt()

class AgentState(TypedDict):
    """The state of the agent."""

    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]

from langchain_core.tools import tool

# local_llm = "qwen2.5:14b" # v1
# local_llm = "qwen2.5:7b-instruct" # v2
local_llm = "qwen2.5:7b-instruct"
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


# Define the node that reads code
def read_code_node(state: AgentState):
    """Reads the code file and adds it to messages."""
    # Extract the file path from the initial user message
    messages = state["messages"]
    user_message = str(messages[0].content) if messages else ""
    
    # Extract path from the message
    path = user_message.split("Code file path:")[1].split(".")[0] + ".py"
    path = path.strip()

    
    # Read the code file
    try:
        code_content = read_file.invoke({"file_path": path})
        message = ToolMessage(
            content=f"Code file content ({path}):\n{code_content}",
            name="read_code",
            tool_call_id="read_code_initial",
        )
    except Exception as e:
        message = ToolMessage(
            content=f"Error reading code file: {str(e)}",
            name="read_code",
            tool_call_id="read_code_initial",
        )
    
    return {"messages": [message]}


# Define the node that runs tests
def run_tests_node(state: AgentState):
    """Runs tests and adds results to messages."""
    # Extract the file path from the initial user message
    messages = state["messages"]
    user_message = str(messages[0].content) if messages else ""
    
    # Extract path from the message
    path = user_message.split("Code file path:")[1].split(".")[0] + ".py"
    path = path.strip()

    try:
        test_results = run_tests.invoke({"code_path": path})
        message = ToolMessage(
            content=f"Test results:\n{json.dumps(test_results)}",
            name="run_tests",
            tool_call_id="run_tests_initial",
        )
    except Exception as e:
        message = ToolMessage(
            content=f"Error running tests: {str(e)}",
            name="run_tests",
            tool_call_id="run_tests_initial",
        )
    
    return {"messages": [message]}


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

# Add all nodes to the workflow
workflow.add_node("read_code", read_code_node)
workflow.add_node("run_tests_initial", run_tests_node)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entrypoint as `read_code`
# This means that this node is the first one called
workflow.set_entry_point("read_code")

# Chain the initial nodes: read_code -> run_tests_initial -> agent
workflow.add_edge("read_code", "run_tests_initial")
workflow.add_edge("run_tests_initial", "agent")

# We now add a conditional edge from agent
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

# Function to create an agent instance
def create_agent():
    """
    Creates and returns a compiled agent graph instance.
    
    Returns:
        A compiled LangGraph agent ready to process debugging tasks.
    """
    return workflow.compile()


# Helper function for formatting the stream nicely
def print_stream(stream):
    """
    Pretty prints the stream of messages from the agent execution.
    
    Args:
        stream: The stream of state updates from graph.stream()
    """
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


# Example usage (for DEBUG)
# if __name__ == "__main__":
#     from IPython.display import Image, display
#     graph = create_agent()
#     
#     try:
#         display(Image(graph.get_graph().draw_mermaid_png()))
#     except Exception:
#         # This requires some extra dependencies and is optional
#         pass
#     
#     path = "code_1.py"
#     test = readfile("test.py")
#     inputs = {"messages": [("user", "Fix bugs in the code. Code file path:"+path+". Now this tests failed:\n"+test+"")]}
#     print_stream(graph.stream(inputs,
#                               stream_mode="values",
#                               config={"max_iterations": 50}))
