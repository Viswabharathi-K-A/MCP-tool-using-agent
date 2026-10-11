from langchain_core.messages import ToolMessage
from tests.tool_validation import validate_tool_result

tests = [
    ToolMessage(
        content="File read successfully",
        tool_call_id="1"
    ),
    ToolMessage(
        content="",
        tool_call_id="2"
    ),
    ToolMessage(
        content=[{
            "type": "text",
            "text": "Weather data available"
        }],
        tool_call_id="3"
    ),
    ToolMessage(
        content=[{
            "type": "text",
            "text": "File not found"
        }],
        tool_call_id="4",
        status="error"
    ),
    ToolMessage(
        content=[{
            "type": "text",
            "text": ""
        }],
        tool_call_id="5"
    )
]

for i, result in enumerate(tests, 1):
    print(f"Test {i}: {validate_tool_result(result)}")