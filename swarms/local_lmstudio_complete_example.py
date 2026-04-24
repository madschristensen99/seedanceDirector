"""
Complete example of using LM Studio with Swarms

This example demonstrates:
1. Using LiteLLM wrapper directly
2. Using Agent with custom LLM
3. Available models on your LM Studio server

Your LM Studio server is running at: http://localhost:1234
Available models:
- kyle-jr-v2
- monero-bro-v1
- gemma-4-e4b-it-uncensored
- gemma-4-e4b-uncensored-hauhaucs-aggressive
- text-embedding-nomic-embed-text-v1.5
"""

from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM

print("=" * 80)
print("Example 1: Using LiteLLM wrapper directly")
print("=" * 80)

llm = LiteLLM(
    model_name="openai/kyle-jr-v2",
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    temperature=0.7,
    max_tokens=200,
    stream=False,
)

response = llm.run("Explain what a neural network is in one sentence.")
print(f"\nResponse: {response}\n")

print("=" * 80)
print("Example 2: Using Agent with custom LLM")
print("=" * 80)

llm_agent = LiteLLM(
    model_name="openai/kyle-jr-v2",
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    temperature=0.7,
    max_tokens=300,
    stream=False,
)

agent = Agent(
    agent_name="Local-LMStudio-Agent",
    agent_description="Agent using local LM Studio model",
    llm=llm_agent,
    max_loops=1,
)

out = agent.run(
    task="Write a haiku about artificial intelligence.",
)

print(f"\nAgent Response:\n{out}\n")

print("=" * 80)
print("Example 3: Using a different model (gemma)")
print("=" * 80)

llm_gemma = LiteLLM(
    model_name="openai/gemma-4-e4b-it-uncensored",
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    temperature=0.5,
    max_tokens=150,
    stream=False,
)

response_gemma = llm_gemma.run("What is the capital of France?")
print(f"\nResponse: {response_gemma}\n")

print("=" * 80)
print("All examples completed successfully!")
print("=" * 80)
