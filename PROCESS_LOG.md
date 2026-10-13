# CSCI 599 Assignment 1 — Process Log

> **Author review required:** This is a draft based on the recorded development and testing steps. Check the chronology and first-person statements, replace any placeholders, and rewrite the reflection in your own voice before submitting.

## AI tools used

I used ChatGPT to discuss LangGraph/MCP architecture, review code and errors, interpret the assignment requirements, plan tests, and improve documentation. I used AI assistance as a development aid and verified the resulting application through local tests, Docker execution, and live Cloud Run requests. **Add any other AI tools actually used (for example, Codex) and describe their contributions; do not list tools that were not used.**

## Chronological development narrative (approximately 230 words)

I began by setting up a Python FastAPI application exposing a `POST /chat` endpoint with a query and session identifier. I integrated a LangGraph-based agent using OpenAI GPT-5, then configured `MultiServerMCPClient` to launch a Filesystem MCP server, a Weather MCP server, and a Tavily MCP server over stdio. The filesystem server was restricted to a workspace directory. I used LangGraph's `InMemorySaver` and passed the request's `session_id` as `thread_id` so the agent could maintain context across turns.

During implementation, I tested MCP discovery and examined how the agent selected tools, received `ToolMessage` results, and generated final answers. I added response extraction and error handling for agent and MCP failures, along with logging that records tool calls without requiring verbose output in production. I also wrote automated tests for API validation, response handling, and MCP execution paths; the latest local run reported 21 passing tests.

Next, I packaged the application using a multi-stage Docker build with Node.js/npm and a non-root runtime user. I verified container startup and MCP tool discovery. I deployed the image to Google Cloud Run and configured API credentials through Secret Manager. During deployment debugging, an OpenAI API key contained a trailing newline, causing an invalid HTTP authorization header. I corrected the secret formatting and retested.

Finally, I verified the deployed `/chat` endpoint, Filesystem listing and file read/write, Weather and Tavily MCP calls, and conversational memory across two requests. I used Cloud Run logs to confirm actual MCP tool invocation rather than relying only on generated answers.

## Representative AI-assisted development prompts

These are **paraphrases of the development questions discussed**, not a claim of verbatim prompt transcripts. Replace or supplement them with exact prompts from your records if required by your instructor.

- How should a FastAPI `/chat` endpoint invoke a LangGraph agent with a session-specific thread ID?
- How can a `MultiServerMCPClient` connect to Filesystem, Weather, and Tavily servers through stdio?
- How should the application handle malformed MCP results, tool errors, and empty final agent responses?
- How can I validate MCP integration while minimizing OpenAI and Tavily API costs?
- What should I check when the Cloud Run container starts but an OpenAI request fails with an illegal authorization header?
- Which architecture diagrams and submission artifacts does the assignment require?

## Verification and evidence

| Test or observation | Recorded outcome |
|---|---|
| Local automated test suite | 21 tests passed |
| Local Docker image and API | Image built; container started and responded |
| Deployed Cloud Run `/chat` | Successful GPT-5 answer |
| Filesystem MCP | Listed workspace, created file, and read its content |
| Weather MCP | `get_current_weather` invoked successfully |
| Tavily MCP | `tavily_search` invoked successfully |
| Session memory | Same `session_id` retained a fact across two requests |
| Cloud Run tool logs | Successful MCP operation and tool-result entries |

The automated tests used mocks and are distinct from live MCP verification. Live tests can incur API usage costs. The deployment uses a maximum of one Cloud Run instance and an in-memory checkpointer; memory is not durable across instance restarts.

## Debugging notes and decisions

- **FastAPI startup:** Corrected application loading and used an application lifespan to initialize and clean up the agent.
- **Tool visibility:** Checked Cloud Run logs for real `tools/call` activity instead of assuming a natural-language response proved integration.
- **Secret formatting:** Corrected an OpenAI API key value that had acquired a trailing newline during PowerShell-based secret upload. **Confirm that any key exposed in logs was rotated/revoked.**
- **Cloud costs:** Chose scale-to-zero and a single maximum instance; minimized unnecessary live paid tests.
- **Ephemeral state:** Accepted `InMemorySaver` and container-local workspace files for this academic assignment, while documenting their limitations.

## Learning reflection — revise in your own words

This assignment helped me understand the difference between an agent deciding to use a tool and the application actually executing a tool through the MCP protocol. I also learned how deployment concerns—container dependencies, runtime permissions, secret formatting, logging, and ephemeral memory—can affect an otherwise working local agent.

## External sources and attribution

The project integrates existing third-party MCP servers rather than reimplementing them:

- Filesystem MCP: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- Tavily MCP: https://github.com/tavily-ai/tavily-mcp
- Weather MCP: `mcp_weather_server` (verify and add the upstream repository URL).

LangGraph, FastAPI, and related framework documentation were consulted as needed. **If any source code was copied or substantially adapted from external tutorials or repositories, identify the specific source URL and rationale in both code comments and this log.**

## Final pre-submission checks

- [ ] Replace README Cloud Run URL placeholder with the actual service URL.
- [ ] Confirm the actual `deploy.sh` contents and add it to the source ZIP.
- [ ] Confirm final project tree, versions, and Weather MCP attribution URL.
- [ ] Verify that all first-person narrative statements reflect work actually performed.
- [ ] Review this log against the course's process-log instructions and add exact prompts or dates where needed.
- [ ] Exclude credentials, `.env`, virtual environments, and `node_modules` from the ZIP.
- [ ] Keep Cloud Run available through grading.
