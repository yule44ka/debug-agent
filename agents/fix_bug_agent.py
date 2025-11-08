"""LangGraph ReAct agent for fixing buggy Python code."""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import re
from agents.tools import create_code_execution_tool


class AgentState(TypedDict):
    """State for the bug-fixing agent."""
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    buggy_code: str
    docstring: str
    tests: str
    fixed_code: str
    iteration: int
    max_iterations: int


class BugFixAgent:
    """ReAct agent for fixing buggy Python code."""
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-0.5B-Instruct", max_iterations: int = 5):
        """
        Initialize the bug-fixing agent.
        
        Args:
            model_name: HuggingFace model name
            max_iterations: Maximum number of ReAct iterations
        """
        self.max_iterations = max_iterations
        self.model_name = model_name
        
        # Initialize LLM
        print(f"Loading model: {model_name}...")
        self.llm = self._load_llm(model_name)
        
        # Initialize tools
        self.tools = [create_code_execution_tool()]
        self.tool_node = ToolNode(self.tools)
        
        # Build graph
        self.graph = self._build_graph()
        
    def _load_llm(self, model_name: str):
        """Load the HuggingFace LLM."""
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                low_cpu_mem_usage=True,
            )
            
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
            )
            
            llm = HuggingFacePipeline(pipeline=pipe)
            return llm
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to a mock LLM for testing...")
            return None
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph ReAct workflow."""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("extract_code", self._extract_code_node)
        
        # Define edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "extract": "extract_code",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        workflow.add_edge("extract_code", END)
        
        return workflow.compile()
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent reasoning node."""
        messages = state["messages"]
        iteration = state.get("iteration", 0)
        
        # Create prompt
        if iteration == 0:
            # Initial prompt
            prompt = f"""You are a Python debugging expert. Your task is to fix the buggy code below.

Docstring (specification):
{state['docstring']}

Buggy code:
```python
{state['buggy_code']}
```

Tests that must pass:
```python
{state['tests']}
```

Use the execute_python_code tool to test your fixes. Follow these steps:
1. Analyze the bug in the code
2. Propose a fix
3. Test the fix using the tool
4. If tests fail, analyze the error and try again
5. When all tests pass, provide the final fixed code wrapped in ```python ``` tags

Start by analyzing the bug and testing the current code."""

            messages.append(HumanMessage(content=prompt))
        
        # Get LLM response
        if self.llm is None:
            # Mock response for testing
            response = self._mock_agent_response(state)
        else:
            response = self._get_llm_response(messages)
        
        messages.append(AIMessage(content=response))
        
        return {
            **state,
            "messages": messages,
            "iteration": iteration + 1
        }
    
    def _mock_agent_response(self, state: AgentState) -> str:
        """Mock agent response for testing without LLM."""
        iteration = state.get("iteration", 0)
        
        if iteration == 0:
            return f"""Let me test the buggy code first.

Action: execute_python_code
CODE:
{state['buggy_code']}
TESTS:
{state['tests']}
"""
        else:
            # Return the fixed code
            return f"""Based on the test results, here is the fixed code:

```python
{state['buggy_code']}
```

The fix addresses the issue identified in the tests."""
    
    def _get_llm_response(self, messages: Sequence[BaseMessage]) -> str:
        """Get response from LLM."""
        # Format messages for the LLM
        formatted_prompt = "\n\n".join([
            f"{'Human' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
            for m in messages
        ])
        
        try:
            response = self.llm(formatted_prompt)
            return response
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "Error generating response."
    
    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to continue, extract code, or end."""
        messages = state["messages"]
        last_message = messages[-1]
        iteration = state.get("iteration", 0)
        
        # Check if max iterations reached
        if iteration >= state["max_iterations"]:
            return "extract"
        
        # Check if agent wants to use a tool
        if isinstance(last_message, AIMessage) and "execute_python_code" in last_message.content:
            return "continue"
        
        # Check if code is present (wrapped in ```)
        if isinstance(last_message, AIMessage) and "```python" in last_message.content:
            return "extract"
        
        # Check if previous tool execution was successful
        if len(messages) >= 2 and isinstance(messages[-2], ToolMessage):
            if "✓ Success" in messages[-2].content:
                return "extract"
        
        # Continue by default if under max iterations
        if iteration < state["max_iterations"]:
            return "continue"
        
        return "end"
    
    def _extract_code_node(self, state: AgentState) -> AgentState:
        """Extract the fixed code from the agent's response."""
        messages = state["messages"]
        
        # Look for code in the last few messages
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                # Extract code between ```python and ```
                match = re.search(r'```python\s*(.*?)\s*```', message.content, re.DOTALL)
                if match:
                    fixed_code = match.group(1).strip()
                    return {**state, "fixed_code": fixed_code}
        
        # Fallback: use buggy code if no fix found
        return {**state, "fixed_code": state["buggy_code"]}
    
    def fix_bug(self, buggy_code: str, docstring: str, tests: str) -> str:
        """
        Fix a buggy Python function.
        
        Args:
            buggy_code: The buggy Python code
            docstring: The function specification
            tests: Test cases that should pass
            
        Returns:
            Fixed Python code
        """
        initial_state = {
            "messages": [],
            "buggy_code": buggy_code,
            "docstring": docstring,
            "tests": tests,
            "fixed_code": "",
            "iteration": 0,
            "max_iterations": self.max_iterations
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state.get("fixed_code", buggy_code)


if __name__ == "__main__":
    # Test the agent
    agent = BugFixAgent(max_iterations=3)
    
    buggy_code = """def add(a, b):
    return a - b  # Bug: should be + not -
"""
    
    docstring = "Add two numbers and return the result."
    
    tests = """
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(0, 0) == 0
"""
    
    fixed = agent.fix_bug(buggy_code, docstring, tests)
    print("Fixed code:")
    print(fixed)

