# PROCESS LOG — CSCI 599 Assignment 1

## 1. Project Overview

**Project:** LangGraph Agent with MCP Tool Integration  
**Frameworks:** LangGraph, LangChain, FastAPI, MCP  
**LLM:** OpenAI GPT-5  
**Deployment target:** Google Cloud Run

### Objective

Develop an AI agent that integrates multiple external tools through the Model Context Protocol (MCP), maintains session-based conversation memory, and exposes its functionality through a REST API.

The application integrates three MCP servers:

1. **Filesystem MCP** — File operations within a restricted workspace.
2. **Tavily MCP** — Web search and information retrieval.
3. **Weather MCP** — Weather, air quality, and time-related operations.

The application is containerized with Docker and prepared for deployment to Google Cloud Run.

---

## 2. Implementation Process

### Phase 1 — Agent and MCP Integration

Implemented the application using Python, LangGraph, and the LangChain MCP adapters.

The MCP client uses `MultiServerMCPClient` to configure and connect to three MCP servers using stdio transport.

The Filesystem and Tavily servers run through Node.js and `npx`. The Weather server runs through a Python module.

The LangGraph agent receives the tools discovered from these servers and can select tools based on the user's request.

**Design decision:** Use separate MCP servers rather than implementing the tools directly inside the agent. This provides a consistent interface for accessing external capabilities.

### Phase 2 — Language Model Configuration

Configured the agent to use OpenAI GPT-5 through `ChatOpenAI`.

API credentials are loaded from environment variables rather than hardcoded into application source files.

**Design decision:** Keep credentials separate from code to support local development, containerization, and cloud deployment.

### Phase 3 — Session-Based Conversation Memory

Integrated LangGraph's `InMemorySaver` checkpointer.

Each request includes a `session_id`, which is passed to the agent as its configurable `thread_id`.

This allows subsequent requests with the same session identifier to access previous conversation context within the same running agent instance.

**Design decision:** Use in-memory checkpointing for the assignment because it is straightforward to implement and sufficient for demonstrating session memory.

**Limitation:** The memory is not persistent across process restarts or shared between multiple container instances.

### Phase 4 — FastAPI REST Interface

Created a FastAPI application exposing:

`POST /chat`

The endpoint accepts:

```json
{
  "query": "Explain MCP in two sentences.",
  "session_id": "test123"
}
```

The endpoint invokes the LangGraph agent asynchronously and returns the generated response as JSON.

FastAPI's lifespan mechanism is used to initialize the agent during application startup.

---

## 3. Reliability Improvements

### Change 1.1 — Response Validation and Extraction

**Problem:** The final LangGraph message content may be a string or a list of structured content blocks. Returning the raw content could violate the API's expected string response format.

**Solution:**

- Added a `ChatResponse` Pydantic model.
- Implemented `extract_final_text()` to extract text from the final AI message.
- Added checks for missing messages, incorrect message types, pending tool calls, and empty responses.
- Added request length constraints and whitespace validation.

**Result:** The API consistently returns a string response for supported final AI message formats.

### Change 2.1 — Graceful Agent Initialization Failure

**Problem:** If MCP initialization fails during application startup, the service may fail to start entirely.

**Solution:**

- Updated the FastAPI lifespan function to catch initialization failures.
- Initialized `app.state.agent` to `None` before attempting startup.
- Logged initialization exceptions.
- Returned HTTP 503 when the agent was unavailable.

**Result:** The HTTP server can remain available and return a controlled error response when agent initialization fails.

**Trade-off:** Application startup success alone does not guarantee agent readiness. Startup logs must be checked to confirm successful agent initialization.

### Change 3.1 — MCP Tool Execution Interceptor

**Problem:** Tool execution can fail because of server errors, network problems, or invalid results.

**Solution:**

Implemented a custom MCP interceptor that:

- Wraps MCP tool execution.
- Logs the server name, tool name, and execution outcome.
- Catches exceptions during tool execution.
- Converts caught exceptions into MCP error results.
- Validates the expected result type.

The client also enables `handle_tool_errors=True`.

**Design consideration:** The adapter already includes built-in error handling. The custom interceptor was retained to provide centralized logging and an extension point for future server-specific normalization.

**Limitation:** Broad exception handling may hide useful distinctions between failure types. The implementation could be refined to handle specific exceptions separately.

### Change 5.1 — Weather-Specific Error Normalization

**Status:** Deferred.

The installed Weather MCP package was identified as `mcp_weather_server` version `0.6.1`.

Weather-specific normalization was not implemented because there was no confirmed evidence that the server incorrectly marked failures as successful MCP results.

**Decision:** Avoid adding error classification rules based solely on matching words in tool output.

---

## 4. Debugging and Issues Encountered

### Issue 1 — PowerShell Python Command Quoting

An inline Python command produced a syntax error because of quoting behavior in PowerShell.

**Resolution:** Used the interactive Python interpreter to test `extract_final_text()` directly.

**Lesson:** Command-line quoting differs between shells, and using an interactive interpreter can simplify debugging small Python snippets.

### Issue 2 — JSON Request Formatting in PowerShell

A `curl.exe` request containing JSON produced:

- HTTP 422 JSON decoding errors.
- `curl: (6) Could not resolve host` errors.
- An unmatched-brace parsing error.

**Cause:** PowerShell passed the quoted JSON body to `curl.exe` incorrectly.

**Resolution:** Used PowerShell's `ConvertTo-Json` and `Invoke-RestMethod` instead.

Example:

```powershell
$body = @{
    query = "Say hello in one sentence."
    session_id = "docker-test"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8080/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Result:** The containerized `/chat` endpoint returned a successful response.

### Issue 3 — MCP Error Handling Design

The initial proposal introduced custom normalization for all MCP execution exceptions.

After reviewing the adapter's existing `handle_tool_errors=True` behavior, the need for custom error handling was reconsidered.

**Decision:** Retain the custom interceptor for logging and extensibility while acknowledging the overlap with the adapter's built-in functionality.

---

## 5. Automated Testing

Used `pytest` to implement offline unit tests.

### Test Coverage

Tests include:

- Extracting plain-text AI responses.
- Extracting text from structured content blocks.
- Rejecting empty or malformed agent results.
- Rejecting pending tool calls.
- Validating request lengths and whitespace.
- Returning HTTP 503 when the agent is unavailable.
- Returning HTTP 503 when agent execution raises an exception.
- Returning HTTP 200 for successful mocked agent responses.
- Forwarding `session_id` as LangGraph `thread_id`.
- Trimming query and session ID whitespace.
- Handling successful MCP tool execution.
- Converting MCP execution exceptions into error results.
- Handling invalid MCP results.
- Preserving existing MCP error results.

### Test Command

```powershell
python -m pytest tests/ -v
```

**Result: 21 tests passed.**

The tests use mocked agent and MCP tool handlers, avoiding OpenAI and Tavily API charges.

**Limitation:** Unit tests do not replace end-to-end integration tests with live MCP servers.

---

## 6. Docker Containerization

Created a multi-stage Dockerfile.

### Builder Stage

Uses Python 3.13 to install Python dependencies into a separate installation directory.

### Runtime Stage

Includes:

- Python 3.13.
- Node.js and npm for the Filesystem and Tavily MCP servers.
- Python application dependencies.
- Application source files.
- A dedicated non-root user.
- A writable npm cache.
- FastAPI/Uvicorn listening on the port specified by Cloud Run.

### Build Command

```powershell
docker build -t csci599-agent:latest .
```

### Node.js Verification

Verified the following versions inside the built image:

```text
Node.js: v20.19.2
npm: 9.2.0
```

### Container Execution

```powershell
docker run --rm -p 8080:8080 --env-file .env --name csci599-agent csci599-agent:latest
```

### Startup Verification

Container logs confirmed:

- Weather MCP server initialized and registered eight tools.
- Filesystem MCP server started with `/app/workspace` as its allowed directory.
- Tavily MCP server started in stdio mode.
- LangGraph agent initialized successfully.
- Uvicorn started on port 8080.

### API Verification

A live request to the Dockerized `/chat` endpoint succeeded.

**Result:** The containerized application successfully initialized the MCP infrastructure and responded to an API request.

**Remaining verification:** Individual MCP tool execution and multi-turn memory behavior inside Docker have not yet been retested after the latest changes.

---

## 7. Security and Configuration

Implemented the following practices:

- API keys stored in `.env` rather than application source files.
- `.env.example` containing placeholder values only.
- `.gitignore` and `.dockerignore` configured to exclude secrets.
- Docker runtime using a non-root user.
- Filesystem MCP restricted to a designated workspace.
- Optional detailed tool-output logging disabled by default.
- Request input length validation.

Cloud Run deployment will require secure runtime injection of API credentials.

---

## 8. Current Project Status

| Component | Status |
|---|---|
| LangGraph agent | Implemented |
| OpenAI integration | Implemented |
| Filesystem MCP | Initialized successfully |
| Tavily MCP | Initialized successfully |
| Weather MCP | Initialized successfully |
| Session-based memory | Implemented |
| FastAPI endpoint | Implemented and tested |
| Error handling | Implemented and unit-tested |
| Automated tests | 21 passed |
| Docker build | Successful |
| Docker startup | Successful |
| Dockerized `/chat` request | Successful |
| Cloud Run deployment | Pending |

---

## 9. Remaining Work

1. Prepare the Google Cloud Run deployment script.
2. Configure the Google Cloud project, Artifact Registry, and required APIs.
3. Configure credentials securely for Cloud Run.
4. Deploy the Dockerized application.
5. Verify the deployed `/chat` endpoint.
6. Perform final integration tests for MCP tool calls and session behavior.
7. Update the README and process log with deployment results.

---

## 10. Key Learnings

This project provided practical experience with:

- Integrating multiple MCP servers into a single agent.
- Using LangGraph for tool selection and session-based state.
- Exposing asynchronous agent execution through FastAPI.
- Implementing API request and response validation.
- Designing error handling around external tool integrations.
- Testing agent behavior without paid API calls.
- Containerizing Python and Node.js components together.
- Preparing an AI application for cloud deployment.

The implementation demonstrates how an LLM-based agent can use standardized MCP tools while exposing a conventional REST API interface.