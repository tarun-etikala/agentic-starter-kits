import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from pydantic import BaseModel
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from langgraph_react_with_database_memory_base.agent import get_graph_closure
from langgraph_react_with_database_memory_base.utils import (
    getenv,
    get_database_uri,
)

logger = logging.getLogger(__name__)


# OpenAI-compatible request/response models
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    messages: list[ChatMessage]
    model: str | None = None
    stream: bool = False
    thread_id: str | None = None


# Global variables
agent_graph_closure = None
DB_URI = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the ReAct agent graph on startup and clear it on shutdown."""
    global agent_graph_closure, DB_URI

    base_url = getenv("BASE_URL")
    model_id = getenv("MODEL_ID")

    if base_url and not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    DB_URI = get_database_uri()

    with PostgresSaver.from_conn_string(DB_URI) as saver:
        saver.setup()

    agent_graph_closure = get_graph_closure(model_id=model_id, base_url=base_url)

    yield

    agent_graph_closure = None
    DB_URI = None


# Create FastAPI app
app = FastAPI(
    title="LangGraph React Agent with Database Memory API",
    description="FastAPI service for LangGraph React Agent with PostgreSQL persistence",
    lifespan=lifespan,
)


def _convert_dict_to_message(msg: ChatMessage):
    """Convert ChatMessage to LangChain message object."""
    if msg.role == "system":
        return SystemMessage(content=msg.content)
    elif msg.role == "assistant":
        return AIMessage(content=msg.content)
    else:
        return HumanMessage(content=msg.content)


def _make_completion_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:12]}"


def _format_context_messages(messages) -> list[dict]:
    """Convert LangChain messages to OpenAI-compatible context dicts."""
    context = []
    for message in messages:
        if isinstance(message, HumanMessage):
            context.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            msg_data = {"role": "assistant", "content": message.content or ""}
            if message.tool_calls:
                msg_data["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"]),
                        },
                    }
                    for tc in message.tool_calls
                ]
            context.append(msg_data)
        elif isinstance(message, ToolMessage):
            context.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "name": message.name,
                    "content": message.content,
                }
            )
    return context


@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    When stream=false, returns a full chat.completion response.
    When stream=true, returns SSE chat.completion.chunk events.
    Supports thread_id for conversation persistence.
    """
    global agent_graph_closure, DB_URI

    if agent_graph_closure is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Convert messages to LangChain format
    langchain_messages = [_convert_dict_to_message(msg) for msg in request.messages]

    # Extract system prompt if present
    system_prompt = None
    if langchain_messages and isinstance(langchain_messages[0], SystemMessage):
        system_prompt = langchain_messages[0].content
        langchain_messages = langchain_messages[1:]

    model_id = request.model or getenv("MODEL_ID", "model")

    if request.stream:
        return await _handle_stream(
            langchain_messages, model_id, request.thread_id, system_prompt
        )
    else:
        return await _handle_chat(
            langchain_messages, model_id, request.thread_id, system_prompt
        )


async def _handle_chat(
    messages: list,
    model_id: str,
    thread_id: str | None,
    system_prompt: str | None,
):
    """Handle non-streaming chat completion."""
    global agent_graph_closure, DB_URI

    try:
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
            await saver.setup()

            if system_prompt:
                agent = agent_graph_closure(saver, thread_id, system_prompt)
            else:
                agent = agent_graph_closure(saver, thread_id)

            # Count existing messages before invoke so we can return only new ones
            prior_count = 0
            if thread_id:
                config = {"configurable": {"thread_id": thread_id}}
                prior = await saver.aget_tuple(config)
                if prior and prior.checkpoint:
                    prior_count = len(
                        prior.checkpoint.get("channel_values", {}).get("messages", [])
                    )
                result = await agent.ainvoke({"messages": messages}, config=config)
            else:
                result = await agent.ainvoke({"messages": messages})

        all_messages = result.get("messages", [])
        new_messages = all_messages[prior_count:]

        # Extract the final assistant content
        assistant_content = ""
        for message in reversed(new_messages):
            if isinstance(message, AIMessage) and message.content:
                assistant_content = message.content
                break

        # Build context from new messages in this turn
        context_messages = _format_context_messages(new_messages)

        return {
            "id": _make_completion_id(),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": assistant_content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "context": context_messages,
            "usage": None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


async def _handle_stream(
    messages: list,
    model_id: str,
    thread_id: str | None,
    system_prompt: str | None,
):
    """Handle streaming chat completion with OpenAI-compatible SSE chunks."""
    global agent_graph_closure, DB_URI

    completion_id = _make_completion_id()
    created = int(time.time())

    async def event_generator():
        try:
            async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
                await saver.setup()

                if system_prompt:
                    agent = agent_graph_closure(saver, thread_id, system_prompt)
                else:
                    agent = agent_graph_closure(saver, thread_id)

                config = {"configurable": {"thread_id": thread_id}} if thread_id else {}

                async for event in agent.astream_events(
                    {"messages": messages},
                    config=config,
                    version="v2",
                ):
                    kind = event["event"]

                    # LLM streaming tokens
                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            data = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model_id,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": chunk.content},
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(data)}\n\n"

                    # Tool calls (after LLM finishes generating the call)
                    elif kind == "on_chat_model_end":
                        message = event["data"]["output"]
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            tool_calls_delta = [
                                {
                                    "index": i,
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["name"],
                                        "arguments": json.dumps(tc["args"]),
                                    },
                                }
                                for i, tc in enumerate(message.tool_calls)
                            ]
                            data = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model_id,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {
                                            "role": "assistant",
                                            "tool_calls": tool_calls_delta,
                                        },
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(data)}\n\n"

                    # Tool execution results
                    elif kind == "on_tool_end":
                        output = event["data"].get("output", "")
                        if hasattr(output, "content"):
                            output = output.content
                        data = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model_id,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "tool",
                                        "content": str(output),
                                        "name": event.get("name", ""),
                                    },
                                    "finish_reason": None,
                                }
                            ],
                        }
                        yield f"data: {json.dumps(data)}\n\n"

            # Send final chunk with finish_reason
            final_data = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception:
            logger.exception("Error in stream event_generator")
            error_data = {
                "error": {
                    "message": "Internal server error",
                    "type": "server_error",
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    """Return service health and whether the agent graph has been initialized."""
    return {
        "status": "healthy",
        "agent_initialized": agent_graph_closure is not None,
        "database_connected": DB_URI is not None,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
