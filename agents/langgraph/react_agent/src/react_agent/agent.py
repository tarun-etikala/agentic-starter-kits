import os
from os import getenv
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from react_agent.tools import dummy_web_search

MAX_RETRIES = 3


def get_graph_closure(
    model_id: str = None,
    base_url: str = None,
    api_key: str = None,
) -> Any:
    """Build and return a LangGraph ReAct agent with the configured LLM and tools."""

    if not api_key:
        api_key = getenv("API_KEY")
    if not base_url:
        base_url = getenv("BASE_URL")
    if not model_id:
        model_id = getenv("MODEL_ID")

    is_local = any(host in base_url for host in ["localhost", "127.0.0.1"])

    if not is_local and not api_key:
        raise ValueError("API_KEY is required for non-local environments.")

    tools = [dummy_web_search]

    chat = ChatOpenAI(
        model=model_id,
        temperature=0.01,
        api_key=api_key,
        base_url=base_url,
    )

    system_prompt = """You are a helpful assistant. When you receive a result from a tool,
        use that information to provide a FINAL answer to the user immediately.
        Do NOT call tools repeatedly for the same question."""
    agent = create_agent(model=chat, tools=tools, system_prompt=system_prompt)

    return agent


def log_agent_run(user_input: str, result: dict) -> None:
    log_path = os.path.join("/tmp", "agent_logs.txt")
    with open(log_path, "a") as f:
        f.write(f"Input: {user_input}\nResult: {result}\n\n")
