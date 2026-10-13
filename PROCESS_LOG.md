# CSCI 599 Assignment 1 — Process Log

## AI tools used

I used ChatGPT while working on this assignment. I mainly used it to understand how LangGraph and MCP fit together, review my code, debug errors, plan tests, and check the assignment requirements. I used the suggestions to make changes in my project and tested the implementation myself using pytest, Docker, and the deployed Cloud Run endpoint.

## Development process

I started by setting up FastAPI with a `/chat` endpoint that accepts a query and a session ID. Then I connected an OpenAI GPT-5 model to a LangGraph agent. My next step was integrating the MCP servers. I initially worked with the Filesystem and Weather servers, and later added Tavily for web search. I used `MultiServerMCPClient` so the agent could discover and call the tools through MCP instead of having separate hard-coded functions for each tool.

After that, I added `InMemorySaver` and mapped `session_id` to LangGraph's `thread_id` to maintain conversation history. I also worked on error handling, extracting the final response correctly, and logging tool calls. One thing I wanted to be sure about was whether the agent was actually calling MCP tools, rather than just generating an answer that looked correct. So I checked the tool messages and logs as part of testing.

I ran the automated tests locally and got 21 passing tests. I then built the Docker image and checked that the application started and the MCP servers initialized inside the container. Next, I deployed the service to Google Cloud Run. I ran into an issue where the OpenAI API key stored in Secret Manager had an extra newline, which caused an invalid authorization header error. I corrected the secret value and tested the endpoint again.

Finally, I verified the live `/chat` endpoint, Filesystem read/write operations, Weather and Tavily tool calls, and memory across two requests with the same session ID. I also checked Cloud Run logs to confirm that the MCP tools were being invoked successfully.

## How I used ChatGPT

Some of the questions I worked through with ChatGPT were:

- How should I initialize the agent and MCP servers during FastAPI startup?
- How does `session_id` work with LangGraph's `thread_id` and `InMemorySaver`?
- How do I check whether the agent is making actual MCP tool calls?
- How should I handle tool errors and extract the final AI response?
- How can I test the project without wasting OpenAI and Tavily credits?
- How do I build and run the project in Docker and deploy it to Cloud Run?
- What caused the illegal authorization header error in Cloud Run?
- What diagrams and documentation does the assignment require?

I used ChatGPT for explanations, troubleshooting, and suggestions. I checked the behavior using actual test results and logs instead of treating AI-generated explanations as proof that something worked.

## Testing and verification

| Test | Result |
|---|---|
| Local automated tests | 21 passed |
| Docker build and application startup | Passed |
| MCP server initialization inside Docker | Passed |
| Cloud Run `/chat` request | Passed |
| Filesystem MCP: list, create, and read file | Passed |
| Weather MCP: `get_current_weather` | Passed |
| Tavily MCP: `tavily_search` | Passed |
| Memory across two requests with the same `session_id` | Passed |
| Tool invocation checked in Cloud Run logs | Passed |

The automated tests used mocked components, so I tested the deployed application separately to verify real MCP calls. The Cloud Run logs showed successful calls to `list_directory`, `get_current_weather`, and `tavily_search`.

## Issues I faced and decisions I made

**Agent initialization:** I had to fix the FastAPI application loading and set up the lifespan logic so the agent and MCP servers initialize when the application starts and clean up when it shuts down.

**Tool execution:** I wanted to confirm that the agent was really using MCP. I added logging and checked tool results, rather than assuming the final response was enough evidence.

**Deployment error:** One of the main issues I faced was the OpenAI key having a trailing newline when it was uploaded to Secret Manager from PowerShell. This caused an HTTP authorization header error. I corrected the stored value and verified the deployed application again.

**Costs and memory:** I kept the number of paid API tests low and configured Cloud Run to scale to zero with a maximum of one instance. I used `InMemorySaver` because the assignment only requires memory while the instance is running. I understand that the memory and files stored inside the container can be lost when the instance restarts.

## What I learned

Before this assignment, I had a basic idea of agents calling tools, but I didn't fully understand how MCP discovery and execution worked. Building and testing the application helped me understand the flow from the user's request to the LLM's tool decision, the MCP call, and the final response. I also learned that getting an agent to work locally is only one part of the process; Docker, Cloud Run, environment variables, logging, and debugging are equally important when deploying it.

## External MCP projects used

- Filesystem MCP server: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- Tavily MCP server: https://github.com/tavily-ai/tavily-mcp
- Weather MCP server: `mcp_weather_server` Python package

I integrated these existing MCP server implementations into my application. I did not write the server implementations myself.
