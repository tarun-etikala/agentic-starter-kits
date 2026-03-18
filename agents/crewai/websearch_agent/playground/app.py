"""
Playground UI for the CrewAI Web Search Agent.

A simple Flask chat interface that proxies requests to the agent's
/chat/completions endpoint with streaming support.

Usage:
    # Make sure the agent is running first (default: http://localhost:8000)
    cd agents/crewai/websearch_agent
    flask --app playground/app run --port 5001

    # Or with a custom agent URL:
    AGENT_URL=http://localhost:8000 flask --app playground/app run --port 5001
"""

import json
import logging
import os

import requests as http_requests
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8000")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Check if the agent is reachable."""
    try:
        resp = http_requests.get(f"{AGENT_URL}/health", timeout=5)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"status": "unreachable", "error": str(e)}), 503


@app.route("/api/chat", methods=["POST"])
def chat():
    """Proxy chat requests to the agent with streaming."""
    data = request.get_json()
    messages = data.get("messages", [])

    payload = {
        "messages": messages,
        "stream": True,
    }

    logger.info(f"Sending request to {AGENT_URL}/chat/completions")
    logger.info(f"Payload: {json.dumps(payload)}")

    def generate():
        try:
            with http_requests.post(
                f"{AGENT_URL}/chat/completions",
                json=payload,
                stream=True,
                timeout=(10, 300),
            ) as resp:
                logger.info(f"Agent response status: {resp.status_code}")

                if resp.status_code != 200:
                    error_msg = resp.text[:500]
                    logger.error(f"Agent error: {error_msg}")
                    error = json.dumps({"error": {"message": f"Agent returned {resp.status_code}: {error_msg}"}})
                    yield f"data: {error}\n\n"
                    return

                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        logger.debug(f"Chunk: {chunk[:200]}")
                        yield chunk

        except http_requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to agent at {AGENT_URL}")
            error = json.dumps({"error": {"message": f"Cannot connect to agent at {AGENT_URL}. Is it running?"}})
            yield f"data: {error}\n\n"
        except http_requests.exceptions.ReadTimeout:
            logger.error("Agent request timed out")
            error = json.dumps({"error": {"message": "Agent request timed out (300s)"}})
            yield f"data: {error}\n\n"
        except Exception as e:
            logger.exception("Unexpected error in proxy")
            error = json.dumps({"error": {"message": str(e)}})
            yield f"data: {error}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
