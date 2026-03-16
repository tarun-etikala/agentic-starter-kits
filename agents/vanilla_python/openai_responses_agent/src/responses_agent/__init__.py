"""
OpenAI Responses Agent Base – agent without any agentic framework.

Uses only the OpenAI Python client and pure Python (Responses API).
No LlamaStack, LangChain, LlamaIndex, etc. Compatible with OpenAI and OpenAI-compatible endpoints.
"""

from responses_agent.agent import AIAgent, get_agent_closure
from responses_agent.tools import search_reviews, search_price

__all__ = [
    "get_agent_closure",
    "AIAgent",
    "search_reviews",
    "search_price",
]
