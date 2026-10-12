# CSCI 599 Assignment 1 — LangGraph Agent with MCP Tools

A containerized AI agent built with **LangGraph, FastAPI, and Model Context Protocol (MCP)**. The agent uses OpenAI for reasoning and integrates three MCP servers for filesystem operations, web search, and weather information.

The application exposes a REST API, maintains conversation history by session, and is designed for deployment to Google Cloud Run.

## 1. Architecture

```text
Client
  |
  | POST /chat
  v
FastAPI Application (main.py)
  |
  v
LangGraph Agent (agent.py)
  |
  |-- OpenAI Chat Model (llm.py)
  |
  |-- Session Memory (InMemorySaver)
  |
  v
MultiServerMCPClient (mcp_config.py)
  |
  |-- Filesystem MCP Server
  |     |-- Read and write files within workspace/
  |
  |-- Tavily MCP Server
  |     |-- Web search
  |
  |-- Weather MCP Server
        |-- Weather and time-related tools
```

The LangGraph agent determines which MCP tools to invoke based on the user's request. The application uses `session_id` as the LangGraph `thread_id` to maintain conversation history across requests.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.13 |
| API framework | FastAPI |
| Agent framework | LangGraph / LangChain |
| Language model | OpenAI GPT-5 |
| Tool integration | Model Context Protocol (MCP) |
| Filesystem tools | `@modelcontextprotocol/server-filesystem` |
| Web search tools | `tavily-mcp` |
| Weather tools | `mcp_weather_server` |
| Session memory | LangGraph `InMemorySaver` |
| Containerization | Docker |
| Deployment target | Google Cloud Run |
| Testing | pytest |

## 3. MCP Servers

### Filesystem MCP

Provides filesystem operations restricted to the configured `workspace/` directory.

### Tavily MCP

Enables the agent to retrieve information from the web through Tavily. Requires a Tavily API key.

### Weather MCP

Provides weather-related capabilities, including current weather, date-range forecasts, air quality, and time-related utilities.

All three servers communicate with the application using the MCP stdio transport.

## 4. Project Structure

```text
.
├── main.py
├── agent.py
├── llm.py
├── mcp_config.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
├── README.md
├── tests/
│   ├── test_main.py
│   └── test_mcp_config.py
└── workspace/
```

Additional deployment scripts and documentation may be included as the project is finalized.

## 5. Environment Configuration

Create a `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your_actual_openai_api_key
TAVILY_API_KEY=your_actual_tavily_api_key
DEBUG_TOOL_OUTPUT=false
```

Use your own API keys.

The `.env.example` file provides a template without exposing credentials.

Never commit `.env` or actual API keys to version control.

## 6. Run Locally

### Prerequisites

- Python with support for the project dependencies
- Node.js and npm
- OpenAI API key
- Tavily API key

### Install dependencies

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
python -m pip install -r requirements.txt
```

The MCP client uses `npx` to launch the Filesystem and Tavily servers and Python to launch the Weather server.

### Start the API

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API is available at:

`http://localhost:8000`

FastAPI interactive documentation:

`http://localhost:8000/docs`

## 7. API Usage

### POST `/chat`

Send a user query and a session identifier.

**Request:**

```json
{
  "query": "Explain MCP in two sentences.",
  "session_id": "test123"
}
```

**Response format:**

```json
{
  "response": "The agent's generated answer appears here."
}
```

### PowerShell example

```powershell
$body = @{
    query = "Explain MCP in two sentences."
    session_id = "test123"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Use the same `session_id` for follow-up messages that should share conversation history.

Use a different `session_id` to create a separate conversation.

## 8. Session Memory

The application uses LangGraph's `InMemorySaver` checkpointer.

Each request passes its session identifier through:

```python
config={
    "configurable": {
        "thread_id": request.session_id
    }
}
```

This enables conversation history to be retained across requests within the same running agent instance.

**Limitation:** `InMemorySaver` stores state in process memory. Conversation history is lost when the process restarts and is not shared between multiple container instances.

For production use, a persistent checkpoint store would be preferable.

## 9. Error Handling

The application implements:

- Pydantic validation for request fields.
- HTTP 422 responses for invalid requests.
- HTTP 503 responses when the agent is unavailable or execution fails.
- MCP tool execution interception and logging.
- Standardized MCP error results for caught tool execution exceptions.
- Final-response extraction that supports text strings and text content blocks.

Tool output logging can be controlled through the `DEBUG_TOOL_OUTPUT` environment variable.

## 10. Automated Testing

The project includes automated tests covering:

- Response extraction and invalid agent responses.
- Input validation.
- Successful API requests.
- Agent execution failures.
- Session identifier forwarding.
- MCP tool execution success and failure.
- Invalid MCP tool results.

Run the full test suite:

```powershell
python -m pytest tests/ -v
```

**Latest local test result: 21 tests passed.**

The automated tests use mocked agent and MCP handlers, so they do not require paid API requests.

## 11. Docker

The application uses a multi-stage Dockerfile.

The builder stage installs Python dependencies. The runtime stage includes Python, Node.js, npm, application files, and a non-root application user.

### Build

```powershell
docker build -t csci599-agent:latest .
```

### Run

```powershell
docker run --rm `
    -p 8080:8080 `
    --env-file .env `
    --name csci599-agent `
    csci599-agent:latest
```

The container starts FastAPI on port 8080.

### Test the containerized API

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

### Local Docker verification

The Docker image was built and run successfully.

The container successfully initialized the LangGraph agent and discovered tools from all three MCP servers. A live `/chat` request also returned a successful response.

Individual MCP tool calls and multi-turn session behavior inside Docker require separate end-to-end verification.

## 12. Google Cloud Run Deployment

Google Cloud Run is the intended deployment platform.

The container listens on the port supplied through the `PORT` environment variable, defaulting to 8080.

Deployment requires:

- A Google Cloud project with billing enabled.
- Appropriate Google Cloud APIs and permissions.
- A container image accessible to Cloud Run.
- Secure configuration of OpenAI and Tavily credentials.

Cloud Run deployment instructions and a deployment script will be added after deployment configuration is finalized.

**Important:** Because session memory is currently stored in process memory, it is not guaranteed to persist across Cloud Run restarts or across multiple instances.

## 13. Current Verification Status

| Feature | Status |
|---|---|
| FastAPI application | Implemented |
| LangGraph agent | Implemented |
| Filesystem MCP integration | Initialized successfully |
| Tavily MCP integration | Initialized successfully |
| Weather MCP integration | Initialized successfully |
| Session memory | Implemented |
| Automated tests | 21 passed |
| Docker image | Built successfully |
| Containerized API | Verified |
| Cloud Run deployment | Pending |

## 14. Limitations and Future Improvements

Potential improvements include persistent session storage, more comprehensive end-to-end MCP integration tests, pinned dependency versions, and production-oriented monitoring.

The current implementation is intended as an academic demonstration of an MCP-enabled, stateful LangGraph agent exposed through a containerized API.