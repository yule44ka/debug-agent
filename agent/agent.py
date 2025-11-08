from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

from langchain_ollama import ChatOllama

# qwen2.5 - 14b (#30 on BFCL leaderboard)
local_llm = "qwen2.5:0.5b"
model = ChatOllama(model=local_llm)

agent = create_agent(
    model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant. Be concise and accurate.",
)

# Run the agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)
print(result)