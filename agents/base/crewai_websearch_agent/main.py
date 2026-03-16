import asyncio
import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from os import getenv

from crewai import LLM
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from crewai_web_search.crew import AssistanceAgents

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


# Global LLM instance
llm = None

# Patterns that indicate CrewAI internal scaffolding in the output
_REACT_NOISE = re.compile(
    r"(^|\n)\s*(Thought:\s*|Action:\s*|Action Input:\s*|Observation:\s*|Final Answer:\s*).*",
    re.DOTALL,
)
_CREWAI_PROMPT_MARKER = "\n\n\nYou ONLY have access to"


def _clean_content(text: str) -> str:
    """Strip CrewAI internal ReAct scaffolding and prompt noise from output."""
    # Strip appended retry instructions
    idx = text.find(_CREWAI_PROMPT_MARKER)
    if idx != -1:
        text = text[:idx]

    # Strip ReAct format artifacts (Thought:/Action:/Final Answer: prefixes)
    text = _REACT_NOISE.sub("", text)

    return text.strip()


def _build_user_message(messages: list[ChatMessage]) -> str:
    """Extract the last user message from the OpenAI-format messages list."""
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    raise ValueError("No user message found in messages list")


def _make_completion_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:12]}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the CrewAI LLM on startup."""
    global llm

    base_url = getenv("BASE_URL")
    model_id = getenv("MODEL_ID")
    api_key = getenv("API_KEY", "no-key")

    if base_url and not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    llm = LLM(
        model=f"openai/{model_id}",
        base_url=base_url,
        api_key=api_key,
        temperature=0.7,
    )

    yield

    llm = None


app = FastAPI(
    title="CrewAI Web Search Agent API",
    description="FastAPI service for CrewAI Web Search Agent",
    lifespan=lifespan,
)


@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    When stream=false, returns a full chat.completion response.
    When stream=true, returns SSE chat.completion.chunk events.
    """
    global llm

    if llm is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    user_message = _build_user_message(request.messages)
    model_id = request.model or getenv("MODEL_ID", "model")

    if request.stream:
        return await _handle_stream(user_message, model_id)
    else:
        return await _handle_chat(user_message, model_id)


async def _handle_chat(user_message: str, model_id: str):
    """Handle non-streaming chat completion."""
    global llm

    try:
        inputs = {
            "user_prompt": user_message,
            "custom_instruction": "",
        }

        crew = AssistanceAgents(llm=llm).crew()
        result = await asyncio.to_thread(crew.kickoff, inputs=inputs)

        assistant_content = _clean_content(str(result))

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
            "usage": None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


async def _handle_stream(user_message: str, model_id: str):
    """Handle streaming chat completion with OpenAI-compatible SSE chunks."""
    global llm

    completion_id = _make_completion_id()
    created = int(time.time())

    async def event_generator():
        try:
            inputs = {
                "user_prompt": user_message,
                "custom_instruction": "",
            }

            crew = AssistanceAgents(llm=llm, stream=True).crew()
            streaming_output = await crew.kickoff_async(inputs=inputs)

            # Buffer tokens until we see "Final Answer:" — everything before
            # that is internal ReAct reasoning (Thought/Action/Observation).
            buffer = ""
            emitting = False

            async for chunk in streaming_output:
                if chunk.chunk_type.value != "text" or not chunk.content:
                    continue

                if emitting:
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
                else:
                    buffer += chunk.content
                    marker = "Final Answer:"
                    idx = buffer.find(marker)
                    if idx != -1:
                        emitting = True
                        remainder = buffer[idx + len(marker) :]
                        if remainder.strip():
                            data = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model_id,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": remainder.lstrip()},
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(data)}\n\n"

            # If no "Final Answer:" was found, send the cleaned full buffer
            if not emitting and buffer.strip():
                cleaned = _clean_content(buffer)
                if cleaned:
                    data = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model_id,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": cleaned},
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
    """Return service health status."""
    return {"status": "healthy", "agent_initialized": llm is not None}


if __name__ == "__main__":
    import uvicorn

    port = int(getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)