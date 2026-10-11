from langchain_core.messages import ToolMessage


def validate_tool_result(message: ToolMessage) -> bool:
    # Check whether the MCP tool reported an error
    if message.status == "error":
        return False

    content = message.content

    # Reject empty text
    if isinstance(content, str):
        return bool(content.strip())

    # MCP adapters may return a list of content blocks
    if isinstance(content, list):
        if not content:
            return False

        for block in content:
            if isinstance(block, str) and block.strip():
                return True

            if isinstance(block, dict):
                if block.get("type") == "text":
                    text = block.get("text")
                    if isinstance(text, str) and text.strip():
                        return True

        return False

    return False