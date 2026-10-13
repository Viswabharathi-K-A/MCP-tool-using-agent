
import pytest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from main import app, extract_final_text


def test_startup_connection_failure_is_graceful(monkeypatch):
    monkeypatch.setattr("main.create_mcp_agent", AsyncMock(side_effect=ConnectionError("MCP unavailable")))
    with TestClient(app) as client:
        response = client.post("/chat", json={"query": "Hello", "session_id": "startup"})
        assert response.status_code == 503
    assert app.state.agent is None


@pytest.mark.parametrize("result", [None, {}, {"messages": []}])
def test_chat_malformed_agent_result(monkeypatch, result):
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = result
    monkeypatch.setattr(app.state, "agent", mock_agent, raising=False)
    response = TestClient(app).post("/chat", json={"query": "Hello", "session_id": "malformed"})
    assert response.status_code == 503


# ----------------------------------------
# Response extraction tests
# ----------------------------------------

def test_plain_text_response():
    result = {
        "messages": [AIMessage(content="Hello from LangGraph")]
    }

    assert extract_final_text(result) == "Hello from LangGraph"


def test_list_based_response():
    result = {
        "messages": [
            AIMessage(content=[
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": "World"}
            ])
        ]
    }

    assert extract_final_text(result) == "Hello\nWorld"


def test_empty_messages():
    with pytest.raises(ValueError):
        extract_final_text({"messages": []})


def test_final_message_is_not_ai():
    result = {
        "messages": [HumanMessage(content="Hello")]
    }

    with pytest.raises(ValueError):
        extract_final_text(result)


def test_extract_final_text_rejects_pending_tool_calls():
    message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "test_tool",
                "args": {},
                "id": "call_123"
            }
        ]
    )

    with pytest.raises(ValueError):
        extract_final_text({"messages": [message]})


def test_extract_final_text_rejects_empty_content():
    with pytest.raises(ValueError):
        extract_final_text({
            "messages": [AIMessage(content="   ")]
        })


def test_extract_final_text_rejects_invalid_result():
    with pytest.raises(ValueError):
        extract_final_text(None)


# ----------------------------------------
# FastAPI request validation tests
# ----------------------------------------

@pytest.mark.parametrize(
    "query, session_id",
    [
        ("", "test123"),
        ("   ", "test123"),
        ("Hello", ""),
        ("Hello", "   "),
        ("a" * 5001, "test123"),
        ("Hello", "a" * 129),
    ]
)
def test_invalid_chat_requests(query, session_id):
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "query": query,
            "session_id": session_id
        }
    )

    assert response.status_code == 422


# ----------------------------------------
# FastAPI endpoint tests
# ----------------------------------------

def test_chat_when_agent_unavailable():
    original_agent = getattr(app.state, "agent", None)
    app.state.agent = None

    try:
        client = TestClient(app)

        response = client.post(
            "/chat",
            json={
                "query": "Hello",
                "session_id": "test123"
            }
        )

        assert response.status_code == 503
        assert response.json()["detail"] == (
            "The agent is temporarily unavailable. Please try again."
        )

    finally:
        app.state.agent = original_agent


def test_chat_success():
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = {
        "messages": [
            AIMessage(content="Hello from the agent!")
        ]
    }

    original_agent = getattr(app.state, "agent", None)
    app.state.agent = mock_agent

    try:
        client = TestClient(app)

        response = client.post(
            "/chat",
            json={
                "query": "Hello",
                "session_id": "test123"
            }
        )

        assert response.status_code == 200
        assert response.json() == {
            "response": "Hello from the agent!"
        }

        mock_agent.ainvoke.assert_awaited_once_with(
            {"messages": [{"role": "user", "content": "Hello"}]},
            config={"configurable": {"thread_id": "test123"}}
        )

    finally:
        app.state.agent = original_agent


def test_chat_agent_execution_failure():
    mock_agent = AsyncMock()
    mock_agent.ainvoke.side_effect = RuntimeError("LLM unavailable")

    original_agent = getattr(app.state, "agent", None)
    app.state.agent = mock_agent

    try:
        client = TestClient(app)

        response = client.post(
            "/chat",
            json={
                "query": "Hello",
                "session_id": "test123"
            }
        )

        assert response.status_code == 503
        assert response.json()["detail"] == (
            "The agent is temporarily unavailable. Please try again."
        )

    finally:
        app.state.agent = original_agent


def test_chat_trims_input():
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = {
        "messages": [AIMessage(content="Hello")]
    }

    original_agent = getattr(app.state, "agent", None)
    app.state.agent = mock_agent

    try:
        client = TestClient(app)

        response = client.post(
            "/chat",
            json={
                "query": "  Hello  ",
                "session_id": "  session123  "
            }
        )

        assert response.status_code == 200

        mock_agent.ainvoke.assert_awaited_once_with(
            {"messages": [{"role": "user", "content": "Hello"}]},
            config={"configurable": {"thread_id": "session123"}}
        )

    finally:
        app.state.agent = original_agent
