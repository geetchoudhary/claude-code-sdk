#!/usr/bin/env python3
"""
Example MCP Server for testing the MCP Client Server
"""

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types


# Create the MCP server
server = Server("example-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="get_weather",
            description="Get weather information for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["city"]
            }
        ),
        types.Tool(
            name="calculate",
            description="Perform basic calculations",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    
    if name == "get_weather":
        city = arguments.get("city", "Unknown") if arguments else "Unknown"
        # Simulated weather data
        weather_data = {
            "New York": {"temp": "72°F", "condition": "Sunny"},
            "London": {"temp": "59°F", "condition": "Cloudy"},
            "Tokyo": {"temp": "68°F", "condition": "Clear"},
        }
        
        weather = weather_data.get(city, {"temp": "Unknown", "condition": "Unknown"})
        
        return [
            types.TextContent(
                type="text",
                text=f"Weather in {city}: {weather['temp']}, {weather['condition']}"
            )
        ]
    
    elif name == "calculate":
        expression = arguments.get("expression", "") if arguments else ""
        try:
            # Simple evaluation (be careful with eval in production!)
            # Only allow basic math operations
            allowed_names = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return [
                types.TextContent(
                    type="text",
                    text=f"{expression} = {result}"
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error evaluating expression: {str(e)}"
                )
            ]
    
    else:
        return [
            types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )
        ]


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="example://data/sample.txt",
            name="Sample Data",
            description="A sample text resource",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="example://data/config.json",
            name="Configuration",
            description="Example configuration data",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource"""
    if uri == "example://data/sample.txt":
        return "This is sample text data from the MCP server!"
    elif uri == "example://data/config.json":
        return '{"version": "1.0", "enabled": true, "settings": {"debug": false}}'
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """List available prompts"""
    return [
        types.Prompt(
            name="greeting",
            description="Generate a greeting message",
            arguments=[
                types.PromptArgument(
                    name="name",
                    description="Name of the person to greet",
                    required=True
                )
            ]
        ),
        types.Prompt(
            name="code_review",
            description="Generate a code review template",
            arguments=[
                types.PromptArgument(
                    name="language",
                    description="Programming language",
                    required=True
                ),
                types.PromptArgument(
                    name="focus_area",
                    description="Area to focus on (e.g., security, performance)",
                    required=False
                )
            ]
        )
    ]


@server.get_prompt()
async def handle_get_prompt(
    name: str,
    arguments: dict | None
) -> types.GetPromptResult:
    """Get a prompt template"""
    
    if name == "greeting":
        user_name = arguments.get("name", "User") if arguments else "User"
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Please write a friendly greeting message for {user_name}."
                    )
                )
            ]
        )
    
    elif name == "code_review":
        language = arguments.get("language", "Python") if arguments else "Python"
        focus_area = arguments.get("focus_area", "general") if arguments else "general"
        
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Please provide a code review checklist for {language} code, "
                             f"with special focus on {focus_area} aspects."
                    )
                )
            ]
        )
    
    else:
        raise ValueError(f"Unknown prompt: {name}")


async def run():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="example-server",
                server_version="0.1.0"
            )
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())