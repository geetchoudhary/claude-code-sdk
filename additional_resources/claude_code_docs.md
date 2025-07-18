================================================
FILE: README.md
================================================
# Claude Code SDK for Python

Python SDK for Claude Code. See the [Claude Code SDK documentation](https://docs.anthropic.com/en/docs/claude-code/sdk) for more information.

## Installation

```bash
pip install claude-code-sdk
```

**Prerequisites:**
- Python 3.10+
- Node.js 
- Claude Code: `npm install -g @anthropic-ai/claude-code`

## Quick Start

```python
import anyio
from claude_code_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

## Usage

### Basic Query

```python
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

# Simple query
async for message in query(prompt="Hello Claude"):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)

# With options
options = ClaudeCodeOptions(
    system_prompt="You are a helpful assistant",
    max_turns=1
)

async for message in query(prompt="Tell me a joke", options=options):
    print(message)
```

### Using Tools

```python
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits'  # auto-accept file edits
)

async for message in query(
    prompt="Create a hello.py file", 
    options=options
):
    # Process tool use and results
    pass
```

### Working Directory

```python
from pathlib import Path

options = ClaudeCodeOptions(
    cwd="/path/to/project"  # or Path("/path/to/project")
)
```

## API Reference

### `query(prompt, options=None)`

Main async function for querying Claude.

**Parameters:**
- `prompt` (str): The prompt to send to Claude
- `options` (ClaudeCodeOptions): Optional configuration

**Returns:** AsyncIterator[Message] - Stream of response messages

### Types

See [src/claude_code_sdk/types.py](src/claude_code_sdk/types.py) for complete type definitions:
- `ClaudeCodeOptions` - Configuration options
- `AssistantMessage`, `UserMessage`, `SystemMessage`, `ResultMessage` - Message types
- `TextBlock`, `ToolUseBlock`, `ToolResultBlock` - Content blocks

## Error Handling

```python
from claude_code_sdk import (
    ClaudeSDKError,      # Base error
    CLINotFoundError,    # Claude Code not installed
    CLIConnectionError,  # Connection issues
    ProcessError,        # Process failed
    CLIJSONDecodeError,  # JSON parsing issues
)

try:
    async for message in query(prompt="Hello"):
        pass
except CLINotFoundError:
    print("Please install Claude Code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
```

See [src/claude_code_sdk/_errors.py](src/claude_code_sdk/_errors.py) for all error types.

## Available Tools

See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/settings#tools-available-to-claude) for a complete list of available tools.

## Examples

See [examples/quick_start.py](examples/quick_start.py) for a complete working example.

## License

MIT



================================================
FILE: LICENSE
================================================
MIT License

Copyright (c) 2025 Anthropic, PBC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


================================================
FILE: pyproject.toml
================================================
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claude-code-sdk"
version = "0.0.14"
description = "Python SDK for Claude Code"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Anthropic", email = "support@anthropic.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
keywords = ["claude", "ai", "sdk", "anthropic"]
dependencies = [
    "anyio>=4.0.0",
    "typing_extensions>=4.0.0; python_version<'3.11'",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.20.0",
    "anyio[trio]>=4.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[project.urls]
Homepage = "https://github.com/anthropics/claude-code-sdk-python"
Documentation = "https://docs.anthropic.com/en/docs/claude-code/sdk"
Issues = "https://github.com/anthropics/claude-code-sdk-python/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/claude_code_sdk"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "/README.md",
    "/LICENSE",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "--import-mode=importlib",
]

[tool.pytest-asyncio]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.ruff]
target-version = "py310"
line-length = 88

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "N",  # pep8-naming
    "UP", # pyupgrade
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "PTH", # flake8-use-pathlib
    "SIM", # flake8-simplify
]
ignore = [
    "E501", # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["claude_code_sdk"]


================================================
FILE: examples/quick_start.py
================================================
#!/usr/bin/env python3
"""Quick start example for Claude Code SDK."""

import anyio

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    query,
)


async def basic_example():
    """Basic example - simple question."""
    print("=== Basic Example ===")

    async for message in query(prompt="What is 2 + 2?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
    print()


async def with_options_example():
    """Example with custom options."""
    print("=== With Options Example ===")

    options = ClaudeCodeOptions(
        system_prompt="You are a helpful assistant that explains things simply.",
        max_turns=1,
    )

    async for message in query(
        prompt="Explain what Python is in one sentence.", options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
    print()


async def with_tools_example():
    """Example using tools."""
    print("=== With Tools Example ===")

    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write"],
        system_prompt="You are a helpful file assistant.",
    )

    async for message in query(
        prompt="Create a file called hello.txt with 'Hello, World!' in it",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
        elif isinstance(message, ResultMessage) and message.total_cost_usd > 0:
            print(f"\nCost: ${message.total_cost_usd:.4f}")
    print()


async def main():
    """Run all examples."""
    await basic_example()
    await with_options_example()
    await with_tools_example()


if __name__ == "__main__":
    anyio.run(main)



================================================
FILE: src/claude_code_sdk/__init__.py
================================================
"""Claude SDK for Python."""

import os
from collections.abc import AsyncIterator

from ._errors import (
    ClaudeSDKError,
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    ProcessError,
)
from ._internal.client import InternalClient
from .types import (
    AssistantMessage,
    ClaudeCodeOptions,
    ContentBlock,
    McpServerConfig,
    Message,
    PermissionMode,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

__version__ = "0.0.14"

__all__ = [
    # Main function
    "query",
    # Types
    "PermissionMode",
    "McpServerConfig",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "Message",
    "ClaudeCodeOptions",
    "TextBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "ContentBlock",
    # Errors
    "ClaudeSDKError",
    "CLIConnectionError",
    "CLINotFoundError",
    "ProcessError",
    "CLIJSONDecodeError",
]


async def query(
    *, prompt: str, options: ClaudeCodeOptions | None = None
) -> AsyncIterator[Message]:
    """
    Query Claude Code.

    Python SDK for interacting with Claude Code.

    Args:
        prompt: The prompt to send to Claude
        options: Optional configuration (defaults to ClaudeCodeOptions() if None).
                 Set options.permission_mode to control tool execution:
                 - 'default': CLI prompts for dangerous tools
                 - 'acceptEdits': Auto-accept file edits
                 - 'bypassPermissions': Allow all tools (use with caution)
                 Set options.cwd for working directory.

    Yields:
        Messages from the conversation


    Example:
        ```python
        # Simple usage
        async for message in query(prompt="Hello"):
            print(message)

        # With options
        async for message in query(
            prompt="Hello",
            options=ClaudeCodeOptions(
                system_prompt="You are helpful",
                cwd="/home/user"
            )
        ):
            print(message)
        ```
    """
    if options is None:
        options = ClaudeCodeOptions()

    os.environ["CLAUDE_CODE_ENTRYPOINT"] = "sdk-py"

    client = InternalClient()

    async for message in client.process_query(prompt=prompt, options=options):
        yield message



================================================
FILE: src/claude_code_sdk/_errors.py
================================================
"""Error types for Claude SDK."""


class ClaudeSDKError(Exception):
    """Base exception for all Claude SDK errors."""


class CLIConnectionError(ClaudeSDKError):
    """Raised when unable to connect to Claude Code."""


class CLINotFoundError(CLIConnectionError):
    """Raised when Claude Code is not found or not installed."""

    def __init__(
        self, message: str = "Claude Code not found", cli_path: str | None = None
    ):
        if cli_path:
            message = f"{message}: {cli_path}"
        super().__init__(message)


class ProcessError(ClaudeSDKError):
    """Raised when the CLI process fails."""

    def __init__(
        self, message: str, exit_code: int | None = None, stderr: str | None = None
    ):
        self.exit_code = exit_code
        self.stderr = stderr

        if exit_code is not None:
            message = f"{message} (exit code: {exit_code})"
        if stderr:
            message = f"{message}\nError output: {stderr}"

        super().__init__(message)


class CLIJSONDecodeError(ClaudeSDKError):
    """Raised when unable to decode JSON from CLI output."""

    def __init__(self, line: str, original_error: Exception):
        self.line = line
        self.original_error = original_error
        super().__init__(f"Failed to decode JSON: {line[:100]}...")



================================================
FILE: src/claude_code_sdk/py.typed
================================================
[Empty file]


================================================
FILE: src/claude_code_sdk/types.py
================================================
"""Type definitions for Claude SDK."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypedDict

from typing_extensions import NotRequired  # For Python < 3.11 compatibility

# Permission modes
PermissionMode = Literal["default", "acceptEdits", "bypassPermissions"]


# MCP Server config
class McpStdioServerConfig(TypedDict):
    """MCP stdio server configuration."""

    type: NotRequired[Literal["stdio"]]  # Optional for backwards compatibility
    command: str
    args: NotRequired[list[str]]
    env: NotRequired[dict[str, str]]


class McpSSEServerConfig(TypedDict):
    """MCP SSE server configuration."""

    type: Literal["sse"]
    url: str
    headers: NotRequired[dict[str, str]]


class McpHttpServerConfig(TypedDict):
    """MCP HTTP server configuration."""

    type: Literal["http"]
    url: str
    headers: NotRequired[dict[str, str]]


McpServerConfig = McpStdioServerConfig | McpSSEServerConfig | McpHttpServerConfig


# Content block types
@dataclass
class TextBlock:
    """Text content block."""

    text: str


@dataclass
class ToolUseBlock:
    """Tool use content block."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResultBlock:
    """Tool result content block."""

    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None


ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock


# Message types
@dataclass
class UserMessage:
    """User message."""

    content: str


@dataclass
class AssistantMessage:
    """Assistant message with content blocks."""

    content: list[ContentBlock]


@dataclass
class SystemMessage:
    """System message with metadata."""

    subtype: str
    data: dict[str, Any]


@dataclass
class ResultMessage:
    """Result message with cost and usage information."""

    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None


Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage


@dataclass
class ClaudeCodeOptions:
    """Query options for Claude SDK."""

    allowed_tools: list[str] = field(default_factory=list)
    max_thinking_tokens: int = 8000
    system_prompt: str | None = None
    append_system_prompt: str | None = None
    mcp_tools: list[str] = field(default_factory=list)
    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None



================================================
FILE: src/claude_code_sdk/_internal/__init__.py
================================================
"""Internal implementation details."""



================================================
FILE: src/claude_code_sdk/_internal/client.py
================================================
"""Internal client implementation."""

from collections.abc import AsyncIterator
from typing import Any

from ..types import (
    AssistantMessage,
    ClaudeCodeOptions,
    ContentBlock,
    Message,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from .transport.subprocess_cli import SubprocessCLITransport


class InternalClient:
    """Internal client implementation."""

    def __init__(self) -> None:
        """Initialize the internal client."""

    async def process_query(
        self, prompt: str, options: ClaudeCodeOptions
    ) -> AsyncIterator[Message]:
        """Process a query through transport."""

        transport = SubprocessCLITransport(prompt=prompt, options=options)

        try:
            await transport.connect()

            async for data in transport.receive_messages():
                message = self._parse_message(data)
                if message:
                    yield message

        finally:
            await transport.disconnect()

    def _parse_message(self, data: dict[str, Any]) -> Message | None:
        """Parse message from CLI output, trusting the structure."""

        match data["type"]:
            case "user":
                return UserMessage(content=data["message"]["content"])

            case "assistant":
                content_blocks: list[ContentBlock] = []
                for block in data["message"]["content"]:
                    match block["type"]:
                        case "text":
                            content_blocks.append(TextBlock(text=block["text"]))
                        case "tool_use":
                            content_blocks.append(
                                ToolUseBlock(
                                    id=block["id"],
                                    name=block["name"],
                                    input=block["input"],
                                )
                            )
                        case "tool_result":
                            content_blocks.append(
                                ToolResultBlock(
                                    tool_use_id=block["tool_use_id"],
                                    content=block.get("content"),
                                    is_error=block.get("is_error"),
                                )
                            )

                return AssistantMessage(content=content_blocks)

            case "system":
                return SystemMessage(
                    subtype=data["subtype"],
                    data=data,
                )

            case "result":
                return ResultMessage(
                    subtype=data["subtype"],
                    duration_ms=data["duration_ms"],
                    duration_api_ms=data["duration_api_ms"],
                    is_error=data["is_error"],
                    num_turns=data["num_turns"],
                    session_id=data["session_id"],
                    total_cost_usd=data.get("total_cost_usd"),
                    usage=data.get("usage"),
                    result=data.get("result"),
                )

            case _:
                return None



================================================
FILE: src/claude_code_sdk/_internal/transport/__init__.py
================================================
"""Transport implementations for Claude SDK."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class Transport(ABC):
    """Abstract transport for Claude communication."""

    @abstractmethod
    async def connect(self) -> None:
        """Initialize connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    async def send_request(
        self, messages: list[dict[str, Any]], options: dict[str, Any]
    ) -> None:
        """Send request to Claude."""
        pass

    @abstractmethod
    def receive_messages(self) -> AsyncIterator[dict[str, Any]]:
        """Receive messages from Claude."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        pass


__all__ = ["Transport"]



================================================
FILE: src/claude_code_sdk/_internal/transport/subprocess_cli.py
================================================
"""Subprocess transport implementation using Claude Code CLI."""

import json
import logging
import os
import shutil
from collections.abc import AsyncIterator
from pathlib import Path
from subprocess import PIPE
from typing import Any

import anyio
from anyio.abc import Process
from anyio.streams.text import TextReceiveStream

from ..._errors import CLIConnectionError, CLINotFoundError, ProcessError
from ..._errors import CLIJSONDecodeError as SDKJSONDecodeError
from ...types import ClaudeCodeOptions
from . import Transport

logger = logging.getLogger(__name__)

_MAX_BUFFER_SIZE = 1024 * 1024  # 1MB buffer limit


class SubprocessCLITransport(Transport):
    """Subprocess transport using Claude Code CLI."""

    def __init__(
        self,
        prompt: str,
        options: ClaudeCodeOptions,
        cli_path: str | Path | None = None,
    ):
        self._prompt = prompt
        self._options = options
        self._cli_path = str(cli_path) if cli_path else self._find_cli()
        self._cwd = str(options.cwd) if options.cwd else None
        self._process: Process | None = None
        self._stdout_stream: TextReceiveStream | None = None
        self._stderr_stream: TextReceiveStream | None = None

    def _find_cli(self) -> str:
        """Find Claude Code CLI binary."""
        if cli := shutil.which("claude"):
            return cli

        locations = [
            Path.home() / ".npm-global/bin/claude",
            Path("/usr/local/bin/claude"),
            Path.home() / ".local/bin/claude",
            Path.home() / "node_modules/.bin/claude",
            Path.home() / ".yarn/bin/claude",
        ]

        for path in locations:
            if path.exists() and path.is_file():
                return str(path)

        node_installed = shutil.which("node") is not None

        if not node_installed:
            error_msg = "Claude Code requires Node.js, which is not installed.\n\n"
            error_msg += "Install Node.js from: https://nodejs.org/\n"
            error_msg += "\nAfter installing Node.js, install Claude Code:\n"
            error_msg += "  npm install -g @anthropic-ai/claude-code"
            raise CLINotFoundError(error_msg)

        raise CLINotFoundError(
            "Claude Code not found. Install with:\n"
            "  npm install -g @anthropic-ai/claude-code\n"
            "\nIf already installed locally, try:\n"
            '  export PATH="$HOME/node_modules/.bin:$PATH"\n'
            "\nOr specify the path when creating transport:\n"
            "  SubprocessCLITransport(..., cli_path='/path/to/claude')"
        )

    def _build_command(self) -> list[str]:
        """Build CLI command with arguments."""
        cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]

        if self._options.system_prompt:
            cmd.extend(["--system-prompt", self._options.system_prompt])

        if self._options.append_system_prompt:
            cmd.extend(["--append-system-prompt", self._options.append_system_prompt])

        if self._options.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self._options.allowed_tools)])

        if self._options.max_turns:
            cmd.extend(["--max-turns", str(self._options.max_turns)])

        if self._options.disallowed_tools:
            cmd.extend(["--disallowedTools", ",".join(self._options.disallowed_tools)])

        if self._options.model:
            cmd.extend(["--model", self._options.model])

        if self._options.permission_prompt_tool_name:
            cmd.extend(
                ["--permission-prompt-tool", self._options.permission_prompt_tool_name]
            )

        if self._options.permission_mode:
            cmd.extend(["--permission-mode", self._options.permission_mode])

        if self._options.continue_conversation:
            cmd.append("--continue")

        if self._options.resume:
            cmd.extend(["--resume", self._options.resume])

        if self._options.mcp_servers:
            cmd.extend(
                ["--mcp-config", json.dumps({"mcpServers": self._options.mcp_servers})]
            )

        cmd.extend(["--print", self._prompt])
        return cmd

    async def connect(self) -> None:
        """Start subprocess."""
        if self._process:
            return

        cmd = self._build_command()
        try:
            self._process = await anyio.open_process(
                cmd,
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                cwd=self._cwd,
                env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "sdk-py"},
            )

            if self._process.stdout:
                self._stdout_stream = TextReceiveStream(self._process.stdout)
            if self._process.stderr:
                self._stderr_stream = TextReceiveStream(self._process.stderr)

        except FileNotFoundError as e:
            # Check if the error comes from the working directory or the CLI
            if self._cwd and not Path(self._cwd).exists():
                raise CLIConnectionError(
                    f"Working directory does not exist: {self._cwd}"
                ) from e
            raise CLINotFoundError(f"Claude Code not found at: {self._cli_path}") from e
        except Exception as e:
            raise CLIConnectionError(f"Failed to start Claude Code: {e}") from e

    async def disconnect(self) -> None:
        """Terminate subprocess."""
        if not self._process:
            return

        if self._process.returncode is None:
            try:
                self._process.terminate()
                with anyio.fail_after(5.0):
                    await self._process.wait()
            except TimeoutError:
                self._process.kill()
                await self._process.wait()
            except ProcessLookupError:
                pass

        self._process = None
        self._stdout_stream = None
        self._stderr_stream = None

    async def send_request(self, messages: list[Any], options: dict[str, Any]) -> None:
        """Not used for CLI transport - args passed via command line."""

    async def receive_messages(self) -> AsyncIterator[dict[str, Any]]:
        """Receive messages from CLI."""
        if not self._process or not self._stdout_stream:
            raise CLIConnectionError("Not connected")

        # Safety constants
        max_stderr_size = 10 * 1024 * 1024  # 10MB
        stderr_timeout = 30.0  # 30 seconds

        json_buffer = ""

        # Process stdout messages first
        try:
            async for line in self._stdout_stream:
                line_str = line.strip()
                if not line_str:
                    continue

                json_lines = line_str.split("\n")

                for json_line in json_lines:
                    json_line = json_line.strip()
                    if not json_line:
                        continue

                    # Keep accumulating partial JSON until we can parse it
                    json_buffer += json_line

                    if len(json_buffer) > _MAX_BUFFER_SIZE:
                        json_buffer = ""
                        raise SDKJSONDecodeError(
                            f"JSON message exceeded maximum buffer size of {_MAX_BUFFER_SIZE} bytes",
                            ValueError(
                                f"Buffer size {len(json_buffer)} exceeds limit {_MAX_BUFFER_SIZE}"
                            ),
                        )

                    try:
                        data = json.loads(json_buffer)
                        json_buffer = ""
                        try:
                            yield data
                        except GeneratorExit:
                            return
                    except json.JSONDecodeError:
                        continue

        except anyio.ClosedResourceError:
            pass
        except GeneratorExit:
            # Client disconnected - still need to clean up
            pass

        # Process stderr with safety limits
        stderr_lines = []
        stderr_size = 0

        if self._stderr_stream:
            try:
                # Use timeout to prevent hanging
                with anyio.fail_after(stderr_timeout):
                    async for line in self._stderr_stream:
                        line_text = line.strip()
                        line_size = len(line_text)

                        # Enforce memory limit
                        if stderr_size + line_size > max_stderr_size:
                            stderr_lines.append(
                                f"[stderr truncated after {stderr_size} bytes]"
                            )
                            # Drain rest of stream without storing
                            async for _ in self._stderr_stream:
                                pass
                            break

                        stderr_lines.append(line_text)
                        stderr_size += line_size

            except TimeoutError:
                stderr_lines.append(
                    f"[stderr collection timed out after {stderr_timeout}s]"
                )
            except anyio.ClosedResourceError:
                pass

        # Check process completion and handle errors
        try:
            returncode = await self._process.wait()
        except Exception:
            returncode = -1

        stderr_output = "\n".join(stderr_lines) if stderr_lines else ""

        # Use exit code for error detection, not string matching
        if returncode is not None and returncode != 0:
            raise ProcessError(
                f"Command failed with exit code {returncode}",
                exit_code=returncode,
                stderr=stderr_output,
            )
        elif stderr_output:
            # Log stderr for debugging but don't fail on non-zero exit
            logger.debug(f"Process stderr: {stderr_output}")

    def is_connected(self) -> bool:
        """Check if subprocess is running."""
        return self._process is not None and self._process.returncode is None



================================================
FILE: tests/conftest.py
================================================
"""Pytest configuration for tests."""


# No async plugin needed since we're using sync tests with anyio.run()



================================================
FILE: tests/test_client.py
================================================
"""Tests for Claude SDK client functionality."""

from unittest.mock import AsyncMock, patch

import anyio

from claude_code_sdk import AssistantMessage, ClaudeCodeOptions, query
from claude_code_sdk.types import TextBlock


class TestQueryFunction:
    """Test the main query function."""

    def test_query_single_prompt(self):
        """Test query with a single prompt."""

        async def _test():
            with patch(
                "claude_code_sdk._internal.client.InternalClient.process_query"
            ) as mock_process:
                # Mock the async generator
                async def mock_generator():
                    yield AssistantMessage(content=[TextBlock(text="4")])

                mock_process.return_value = mock_generator()

                messages = []
                async for msg in query(prompt="What is 2+2?"):
                    messages.append(msg)

                assert len(messages) == 1
                assert isinstance(messages[0], AssistantMessage)
                assert messages[0].content[0].text == "4"

        anyio.run(_test)

    def test_query_with_options(self):
        """Test query with various options."""

        async def _test():
            with patch(
                "claude_code_sdk._internal.client.InternalClient.process_query"
            ) as mock_process:

                async def mock_generator():
                    yield AssistantMessage(content=[TextBlock(text="Hello!")])

                mock_process.return_value = mock_generator()

                options = ClaudeCodeOptions(
                    allowed_tools=["Read", "Write"],
                    system_prompt="You are helpful",
                    permission_mode="acceptEdits",
                    max_turns=5,
                )

                messages = []
                async for msg in query(prompt="Hi", options=options):
                    messages.append(msg)

                # Verify process_query was called with correct prompt and options
                mock_process.assert_called_once()
                call_args = mock_process.call_args
                assert call_args[1]["prompt"] == "Hi"
                assert call_args[1]["options"] == options

        anyio.run(_test)

    def test_query_with_cwd(self):
        """Test query with custom working directory."""

        async def _test():
            with patch(
                "claude_code_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "Done"}],
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1000,
                        "duration_api_ms": 800,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test-session",
                        "total_cost_usd": 0.001,
                    }

                mock_transport.receive_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.disconnect = AsyncMock()

                options = ClaudeCodeOptions(cwd="/custom/path")
                messages = []
                async for msg in query(prompt="test", options=options):
                    messages.append(msg)

                # Verify transport was created with correct parameters
                mock_transport_class.assert_called_once()
                call_kwargs = mock_transport_class.call_args.kwargs
                assert call_kwargs["prompt"] == "test"
                assert call_kwargs["options"].cwd == "/custom/path"

        anyio.run(_test)



================================================
FILE: tests/test_errors.py
================================================
"""Tests for Claude SDK error handling."""

from claude_code_sdk import (
    ClaudeSDKError,
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    ProcessError,
)


class TestErrorTypes:
    """Test error types and their properties."""

    def test_base_error(self):
        """Test base ClaudeSDKError."""
        error = ClaudeSDKError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert isinstance(error, Exception)

    def test_cli_not_found_error(self):
        """Test CLINotFoundError."""
        error = CLINotFoundError("Claude Code not found")
        assert isinstance(error, ClaudeSDKError)
        assert "Claude Code not found" in str(error)

    def test_connection_error(self):
        """Test CLIConnectionError."""
        error = CLIConnectionError("Failed to connect to CLI")
        assert isinstance(error, ClaudeSDKError)
        assert "Failed to connect to CLI" in str(error)

    def test_process_error(self):
        """Test ProcessError with exit code and stderr."""
        error = ProcessError("Process failed", exit_code=1, stderr="Command not found")
        assert error.exit_code == 1
        assert error.stderr == "Command not found"
        assert "Process failed" in str(error)
        assert "exit code: 1" in str(error)
        assert "Command not found" in str(error)

    def test_json_decode_error(self):
        """Test CLIJSONDecodeError."""
        import json

        try:
            json.loads("{invalid json}")
        except json.JSONDecodeError as e:
            error = CLIJSONDecodeError("{invalid json}", e)
            assert error.line == "{invalid json}"
            assert error.original_error == e
            assert "Failed to decode JSON" in str(error)



================================================
FILE: tests/test_integration.py
================================================
"""Integration tests for Claude SDK.

These tests verify end-to-end functionality with mocked CLI responses.
"""

from unittest.mock import AsyncMock, patch

import anyio
import pytest

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    CLINotFoundError,
    ResultMessage,
    query,
)
from claude_code_sdk.types import ToolUseBlock


class TestIntegration:
    """End-to-end integration tests."""

    def test_simple_query_response(self):
        """Test a simple query with text response."""

        async def _test():
            with patch(
                "claude_code_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "2 + 2 equals 4"}],
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1000,
                        "duration_api_ms": 800,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test-session",
                        "total_cost_usd": 0.001,
                    }

                mock_transport.receive_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.disconnect = AsyncMock()

                # Run query
                messages = []
                async for msg in query(prompt="What is 2 + 2?"):
                    messages.append(msg)

                # Verify results
                assert len(messages) == 2

                # Check assistant message
                assert isinstance(messages[0], AssistantMessage)
                assert len(messages[0].content) == 1
                assert messages[0].content[0].text == "2 + 2 equals 4"

                # Check result message
                assert isinstance(messages[1], ResultMessage)
                assert messages[1].total_cost_usd == 0.001
                assert messages[1].session_id == "test-session"

        anyio.run(_test)

    def test_query_with_tool_use(self):
        """Test query that uses tools."""

        async def _test():
            with patch(
                "claude_code_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream with tool use
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Let me read that file for you.",
                                },
                                {
                                    "type": "tool_use",
                                    "id": "tool-123",
                                    "name": "Read",
                                    "input": {"file_path": "/test.txt"},
                                },
                            ],
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1500,
                        "duration_api_ms": 1200,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test-session-2",
                        "total_cost_usd": 0.002,
                    }

                mock_transport.receive_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.disconnect = AsyncMock()

                # Run query with tools enabled
                messages = []
                async for msg in query(
                    prompt="Read /test.txt",
                    options=ClaudeCodeOptions(allowed_tools=["Read"]),
                ):
                    messages.append(msg)

                # Verify results
                assert len(messages) == 2

                # Check assistant message with tool use
                assert isinstance(messages[0], AssistantMessage)
                assert len(messages[0].content) == 2
                assert messages[0].content[0].text == "Let me read that file for you."
                assert isinstance(messages[0].content[1], ToolUseBlock)
                assert messages[0].content[1].name == "Read"
                assert messages[0].content[1].input["file_path"] == "/test.txt"

        anyio.run(_test)

    def test_cli_not_found(self):
        """Test handling when CLI is not found."""

        async def _test():
            with (
                patch("shutil.which", return_value=None),
                patch("pathlib.Path.exists", return_value=False),
                pytest.raises(CLINotFoundError) as exc_info,
            ):
                async for _ in query(prompt="test"):
                    pass

            assert "Claude Code requires Node.js" in str(exc_info.value)

        anyio.run(_test)

    def test_continuation_option(self):
        """Test query with continue_conversation option."""

        async def _test():
            with patch(
                "claude_code_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Continuing from previous conversation",
                                }
                            ],
                        },
                    }

                mock_transport.receive_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.disconnect = AsyncMock()

                # Run query with continuation
                messages = []
                async for msg in query(
                    prompt="Continue",
                    options=ClaudeCodeOptions(continue_conversation=True),
                ):
                    messages.append(msg)

                # Verify transport was created with continuation option
                mock_transport_class.assert_called_once()
                call_kwargs = mock_transport_class.call_args.kwargs
                assert call_kwargs["options"].continue_conversation is True

        anyio.run(_test)



================================================
FILE: tests/test_subprocess_buffering.py
================================================
"""Tests for subprocess transport buffering edge cases."""

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import anyio
import pytest

from claude_code_sdk._errors import CLIJSONDecodeError
from claude_code_sdk._internal.transport.subprocess_cli import (
    _MAX_BUFFER_SIZE,
    SubprocessCLITransport,
)
from claude_code_sdk.types import ClaudeCodeOptions


class MockTextReceiveStream:
    """Mock TextReceiveStream for testing."""

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.index = 0

    def __aiter__(self) -> AsyncIterator[str]:
        return self

    async def __anext__(self) -> str:
        if self.index >= len(self.lines):
            raise StopAsyncIteration
        line = self.lines[self.index]
        self.index += 1
        return line


class TestSubprocessBuffering:
    """Test subprocess transport handling of buffered output."""

    def test_multiple_json_objects_on_single_line(self) -> None:
        """Test parsing when multiple JSON objects are concatenated on a single line.

        In some environments, stdout buffering can cause multiple distinct JSON
        objects to be delivered as a single line with embedded newlines.
        """

        async def _test() -> None:
            json_obj1 = {"type": "message", "id": "msg1", "content": "First message"}
            json_obj2 = {"type": "result", "id": "res1", "status": "completed"}

            buffered_line = json.dumps(json_obj1) + "\n" + json.dumps(json_obj2)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process

            transport._stdout_stream = MockTextReceiveStream([buffered_line])  # type: ignore[assignment]
            transport._stderr_stream = MockTextReceiveStream([])  # type: ignore[assignment]

            messages: list[Any] = []
            async for msg in transport.receive_messages():
                messages.append(msg)

            assert len(messages) == 2
            assert messages[0]["type"] == "message"
            assert messages[0]["id"] == "msg1"
            assert messages[0]["content"] == "First message"
            assert messages[1]["type"] == "result"
            assert messages[1]["id"] == "res1"
            assert messages[1]["status"] == "completed"

        anyio.run(_test)

    def test_json_with_embedded_newlines(self) -> None:
        """Test parsing JSON objects that contain newline characters in string values."""

        async def _test() -> None:
            json_obj1 = {"type": "message", "content": "Line 1\nLine 2\nLine 3"}
            json_obj2 = {"type": "result", "data": "Some\nMultiline\nContent"}

            buffered_line = json.dumps(json_obj1) + "\n" + json.dumps(json_obj2)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([buffered_line])
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.receive_messages():
                messages.append(msg)

            assert len(messages) == 2
            assert messages[0]["content"] == "Line 1\nLine 2\nLine 3"
            assert messages[1]["data"] == "Some\nMultiline\nContent"

        anyio.run(_test)

    def test_multiple_newlines_between_objects(self) -> None:
        """Test parsing with multiple newlines between JSON objects."""

        async def _test() -> None:
            json_obj1 = {"type": "message", "id": "msg1"}
            json_obj2 = {"type": "result", "id": "res1"}

            buffered_line = json.dumps(json_obj1) + "\n\n\n" + json.dumps(json_obj2)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([buffered_line])
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.receive_messages():
                messages.append(msg)

            assert len(messages) == 2
            assert messages[0]["id"] == "msg1"
            assert messages[1]["id"] == "res1"

        anyio.run(_test)

    def test_split_json_across_multiple_reads(self) -> None:
        """Test parsing when a single JSON object is split across multiple stream reads."""

        async def _test() -> None:
            json_obj = {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "x" * 1000},
                        {
                            "type": "tool_use",
                            "id": "tool_123",
                            "name": "Read",
                            "input": {"file_path": "/test.txt"},
                        },
                    ]
                },
            }

            complete_json = json.dumps(json_obj)

            part1 = complete_json[:100]
            part2 = complete_json[100:250]
            part3 = complete_json[250:]

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([part1, part2, part3])
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.receive_messages():
                messages.append(msg)

            assert len(messages) == 1
            assert messages[0]["type"] == "assistant"
            assert len(messages[0]["message"]["content"]) == 2

        anyio.run(_test)

    def test_large_minified_json(self) -> None:
        """Test parsing a large minified JSON (simulating the reported issue)."""

        async def _test() -> None:
            large_data = {"data": [{"id": i, "value": "x" * 100} for i in range(1000)]}
            json_obj = {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "tool_use_id": "toolu_016fed1NhiaMLqnEvrj5NUaj",
                            "type": "tool_result",
                            "content": json.dumps(large_data),
                        }
                    ],
                },
            }

            complete_json = json.dumps(json_obj)

            chunk_size = 64 * 1024
            chunks = [
                complete_json[i : i + chunk_size]
                for i in range(0, len(complete_json), chunk_size)
            ]

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream(chunks)
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.receive_messages():
                messages.append(msg)

            assert len(messages) == 1
            assert messages[0]["type"] == "user"
            assert (
                messages[0]["message"]["content"][0]["tool_use_id"]
                == "toolu_016fed1NhiaMLqnEvrj5NUaj"
            )

        anyio.run(_test)

    def test_buffer_size_exceeded(self) -> None:
        """Test that exceeding buffer size raises an appropriate error."""

        async def _test() -> None:
            huge_incomplete = '{"data": "' + "x" * (_MAX_BUFFER_SIZE + 1000)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([huge_incomplete])
            transport._stderr_stream = MockTextReceiveStream([])

            with pytest.raises(Exception) as exc_info:
                messages: list[Any] = []
                async for msg in transport.receive_messages():
                    messages.append(msg)

            assert isinstance(exc_info.value, CLIJSONDecodeError)
            assert "exceeded maximum buffer size" in str(exc_info.value)

        anyio.run(_test)

    def test_mixed_complete_and_split_json(self) -> None:
        """Test handling a mix of complete and split JSON messages."""

        async def _test() -> None:
            msg1 = json.dumps({"type": "system", "subtype": "start"})

            large_msg = {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "y" * 5000}]},
            }
            large_json = json.dumps(large_msg)

            msg3 = json.dumps({"type": "system", "subtype": "end"})

            lines = [
                msg1 + "\n",
                large_json[:1000],
                large_json[1000:3000],
                large_json[3000:] + "\n" + msg3,
            ]

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream(lines)
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.receive_messages():
                messages.append(msg)

            assert len(messages) == 3
            assert messages[0]["type"] == "system"
            assert messages[0]["subtype"] == "start"
            assert messages[1]["type"] == "assistant"
            assert len(messages[1]["message"]["content"][0]["text"]) == 5000
            assert messages[2]["type"] == "system"
            assert messages[2]["subtype"] == "end"

        anyio.run(_test)



================================================
FILE: tests/test_transport.py
================================================
"""Tests for Claude SDK transport layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import anyio
import pytest

from claude_code_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from claude_code_sdk.types import ClaudeCodeOptions


class TestSubprocessCLITransport:
    """Test subprocess transport implementation."""

    def test_find_cli_not_found(self):
        """Test CLI not found error."""
        from claude_code_sdk._errors import CLINotFoundError

        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(CLINotFoundError) as exc_info,
        ):
            SubprocessCLITransport(prompt="test", options=ClaudeCodeOptions())

        assert "Claude Code requires Node.js" in str(exc_info.value)

    def test_build_command_basic(self):
        """Test building basic CLI command."""
        transport = SubprocessCLITransport(
            prompt="Hello", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
        )

        cmd = transport._build_command()
        assert cmd[0] == "/usr/bin/claude"
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--print" in cmd
        assert "Hello" in cmd

    def test_cli_path_accepts_pathlib_path(self):
        """Test that cli_path accepts pathlib.Path objects."""
        from pathlib import Path

        transport = SubprocessCLITransport(
            prompt="Hello",
            options=ClaudeCodeOptions(),
            cli_path=Path("/usr/bin/claude"),
        )

        assert transport._cli_path == "/usr/bin/claude"

    def test_build_command_with_options(self):
        """Test building CLI command with options."""
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeCodeOptions(
                system_prompt="Be helpful",
                allowed_tools=["Read", "Write"],
                disallowed_tools=["Bash"],
                model="claude-3-5-sonnet",
                permission_mode="acceptEdits",
                max_turns=5,
            ),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--system-prompt" in cmd
        assert "Be helpful" in cmd
        assert "--allowedTools" in cmd
        assert "Read,Write" in cmd
        assert "--disallowedTools" in cmd
        assert "Bash" in cmd
        assert "--model" in cmd
        assert "claude-3-5-sonnet" in cmd
        assert "--permission-mode" in cmd
        assert "acceptEdits" in cmd
        assert "--max-turns" in cmd
        assert "5" in cmd

    def test_session_continuation(self):
        """Test session continuation options."""
        transport = SubprocessCLITransport(
            prompt="Continue from before",
            options=ClaudeCodeOptions(continue_conversation=True, resume="session-123"),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--continue" in cmd
        assert "--resume" in cmd
        assert "session-123" in cmd

    def test_connect_disconnect(self):
        """Test connect and disconnect lifecycle."""

        async def _test():
            with patch("anyio.open_process") as mock_exec:
                mock_process = MagicMock()
                mock_process.returncode = None
                mock_process.terminate = MagicMock()
                mock_process.wait = AsyncMock()
                mock_process.stdout = MagicMock()
                mock_process.stderr = MagicMock()
                mock_exec.return_value = mock_process

                transport = SubprocessCLITransport(
                    prompt="test",
                    options=ClaudeCodeOptions(),
                    cli_path="/usr/bin/claude",
                )

                await transport.connect()
                assert transport._process is not None
                assert transport.is_connected()

                await transport.disconnect()
                mock_process.terminate.assert_called_once()

        anyio.run(_test)

    def test_receive_messages(self):
        """Test parsing messages from CLI output."""
        # This test is simplified to just test the parsing logic
        # The full async stream handling is tested in integration tests
        transport = SubprocessCLITransport(
            prompt="test", options=ClaudeCodeOptions(), cli_path="/usr/bin/claude"
        )

        # The actual message parsing is done by the client, not the transport
        # So we just verify the transport can be created and basic structure is correct
        assert transport._prompt == "test"
        assert transport._cli_path == "/usr/bin/claude"

    def test_connect_with_nonexistent_cwd(self):
        """Test that connect raises CLIConnectionError when cwd doesn't exist."""
        from claude_code_sdk._errors import CLIConnectionError

        async def _test():
            transport = SubprocessCLITransport(
                prompt="test",
                options=ClaudeCodeOptions(cwd="/this/directory/does/not/exist"),
                cli_path="/usr/bin/claude",
            )

            with pytest.raises(CLIConnectionError) as exc_info:
                await transport.connect()

            assert "/this/directory/does/not/exist" in str(exc_info.value)

        anyio.run(_test)



================================================
FILE: tests/test_types.py
================================================
"""Tests for Claude SDK type definitions."""

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
)
from claude_code_sdk.types import TextBlock, ToolResultBlock, ToolUseBlock, UserMessage


class TestMessageTypes:
    """Test message type creation and validation."""

    def test_user_message_creation(self):
        """Test creating a UserMessage."""
        msg = UserMessage(content="Hello, Claude!")
        assert msg.content == "Hello, Claude!"

    def test_assistant_message_with_text(self):
        """Test creating an AssistantMessage with text content."""
        text_block = TextBlock(text="Hello, human!")
        msg = AssistantMessage(content=[text_block])
        assert len(msg.content) == 1
        assert msg.content[0].text == "Hello, human!"

    def test_tool_use_block(self):
        """Test creating a ToolUseBlock."""
        block = ToolUseBlock(
            id="tool-123", name="Read", input={"file_path": "/test.txt"}
        )
        assert block.id == "tool-123"
        assert block.name == "Read"
        assert block.input["file_path"] == "/test.txt"

    def test_tool_result_block(self):
        """Test creating a ToolResultBlock."""
        block = ToolResultBlock(
            tool_use_id="tool-123", content="File contents here", is_error=False
        )
        assert block.tool_use_id == "tool-123"
        assert block.content == "File contents here"
        assert block.is_error is False

    def test_result_message(self):
        """Test creating a ResultMessage."""
        msg = ResultMessage(
            subtype="success",
            duration_ms=1500,
            duration_api_ms=1200,
            is_error=False,
            num_turns=1,
            session_id="session-123",
            total_cost_usd=0.01,
        )
        assert msg.subtype == "success"
        assert msg.total_cost_usd == 0.01
        assert msg.session_id == "session-123"


class TestOptions:
    """Test Options configuration."""

    def test_default_options(self):
        """Test Options with default values."""
        options = ClaudeCodeOptions()
        assert options.allowed_tools == []
        assert options.max_thinking_tokens == 8000
        assert options.system_prompt is None
        assert options.permission_mode is None
        assert options.continue_conversation is False
        assert options.disallowed_tools == []

    def test_claude_code_options_with_tools(self):
        """Test Options with built-in tools."""
        options = ClaudeCodeOptions(
            allowed_tools=["Read", "Write", "Edit"], disallowed_tools=["Bash"]
        )
        assert options.allowed_tools == ["Read", "Write", "Edit"]
        assert options.disallowed_tools == ["Bash"]

    def test_claude_code_options_with_permission_mode(self):
        """Test Options with permission mode."""
        options = ClaudeCodeOptions(permission_mode="bypassPermissions")
        assert options.permission_mode == "bypassPermissions"

    def test_claude_code_options_with_system_prompt(self):
        """Test Options with system prompt."""
        options = ClaudeCodeOptions(
            system_prompt="You are a helpful assistant.",
            append_system_prompt="Be concise.",
        )
        assert options.system_prompt == "You are a helpful assistant."
        assert options.append_system_prompt == "Be concise."

    def test_claude_code_options_with_session_continuation(self):
        """Test Options with session continuation."""
        options = ClaudeCodeOptions(continue_conversation=True, resume="session-123")
        assert options.continue_conversation is True
        assert options.resume == "session-123"

    def test_claude_code_options_with_model_specification(self):
        """Test Options with model specification."""
        options = ClaudeCodeOptions(
            model="claude-3-5-sonnet-20241022", permission_prompt_tool_name="CustomTool"
        )
        assert options.model == "claude-3-5-sonnet-20241022"
        assert options.permission_prompt_tool_name == "CustomTool"



================================================
FILE: .github/workflows/claude-code-review.yml
================================================
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize]
    # Optional: Only run on specific file changes
    # paths:
    # - "src/**/*.ts"
    # - "src/**/*.tsx"
    # - "src/**/*.js"
    # - "src/**/*.jsx"

jobs:
  claude-review:
    # Optional: Filter by PR author
    # if: |
    # github.event.pull_request.user.login == 'external-contributor' ||
    # github.event.pull_request.user.login == 'new-developer' ||
    # github.event.pull_request.author_association == 'FIRST_TIME_CONTRIBUTOR'

    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 1

    - name: Run Claude Code Review
      id: claude-review
      uses: anthropics/claude-code-action@beta
      with:
        anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}

        # Optional: Specify model (defaults to Claude Sonnet 4, uncomment for Claude Opus 4)
        # model: "claude-opus-4-20250514"

        # Direct prompt for automated review (no @claude mention needed)
        direct_prompt: |
          Please review this pull request and provide feedback on:
          - Code quality and best practices
          - Potential bugs or issues
          - Performance considerations
          - Security concerns
          - Test coverage

          Be constructive and helpful in your feedback.

        # Optional: Customize review based on file types
        # direct_prompt: |
        # Review this PR focusing on:
        # - For TypeScript files: Type safety and proper interface usage
        # - For API endpoints: Security, input validation, and error handling
        # - For React components: Performance, accessibility, and reusability
        # - For test files: Coverage, edge cases, and test quality

        # Optional: If automated review posts public comments
        # no_comments: true

        # Optional: Create a summary comment on the PR
        # summary_comment: true

        # Optional: Allow Claude to suggest code changes
        # allow_code_suggestions: true

        # Optional: Limit Claude review scope
        # max_files_to_review: 10
        # max_lines_per_file: 500


================================================
FILE: .github/workflows/claude-issue-triage.yml
================================================
name: Claude Issue Triage

on:
  issues:
    types: [opened]

jobs:
  triage-issue:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
      issues: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Create triage prompt
        run: |
          mkdir -p /tmp/claude-prompts
          cat > /tmp/claude-prompts/triage-prompt.txt << 'EOF'
          You're an issue triage assistant for GitHub issues. Your task is to analyze the issue and select appropriate labels from the provided list.

          IMPORTANT: Don't post any comments or messages to the issue. Your only action should be to apply labels.

          Issue Information:
          - REPO: ${{ github.repository }}
          - ISSUE_NUMBER: ${{ github.event.issue.number }}

          TASK OVERVIEW:

          1. First, fetch the list of labels available in this repository by running: `gh label list`. Run exactly this command with nothing else.

          2. Next, use the GitHub tools to get context about the issue:
             - You have access to these tools:
               - mcp__github__get_issue: Use this to retrieve the current issue's details including title, description, and existing labels
               - mcp__github__get_issue_comments: Use this to read any discussion or additional context provided in the comments
               - mcp__github__update_issue: Use this to apply labels to the issue (do not use this for commenting)
               - mcp__github__search_issues: Use this to find similar issues that might provide context for proper categorization and to identify potential duplicate issues
               - mcp__github__list_issues: Use this to understand patterns in how other issues are labeled
             - Start by using mcp__github__get_issue to get the issue details

          3. Analyze the issue content, considering:
             - The issue title and description
             - The type of issue (bug report, feature request, question, etc.)
             - Technical areas mentioned
             - Severity or priority indicators
             - User impact
             - Components affected

          4. Select appropriate labels from the available labels list provided above:
             - Choose labels that accurately reflect the issue's nature
             - Be specific but comprehensive
             - Select priority labels if you can determine urgency (high-priority, med-priority, or low-priority)
             - Consider platform labels (android, ios) if applicable
             - If you find similar issues using mcp__github__search_issues, consider using a "duplicate" label if appropriate. Only do so if the issue is a duplicate of another OPEN issue.

          5. Apply the selected labels:
             - Use mcp__github__update_issue to apply your selected labels
             - DO NOT post any comments explaining your decision
             - DO NOT communicate directly with users
             - If no labels are clearly applicable, do not apply any labels

          IMPORTANT GUIDELINES:
          - Be thorough in your analysis
          - Only select labels from the provided list above
          - DO NOT post any comments to the issue
          - Your ONLY action should be to apply labels using mcp__github__update_issue
          - It's okay to not add any labels if none are clearly applicable
          EOF

      - name: Setup GitHub MCP Server
        run: |
          mkdir -p /tmp/mcp-config
          cat > /tmp/mcp-config/mcp-servers.json << 'EOF'
          {
            "mcpServers": {
              "github": {
                "command": "docker",
                "args": [
                  "run",
                  "-i",
                  "--rm",
                  "-e",
                  "GITHUB_PERSONAL_ACCESS_TOKEN",
                  "ghcr.io/github/github-mcp-server:sha-7aced2b"
                ],
                "env": {
                  "GITHUB_PERSONAL_ACCESS_TOKEN": "${{ secrets.GITHUB_TOKEN }}"
                }
              }
            }
          }
          EOF

      - name: Run Claude Code for Issue Triage
        uses: anthropics/claude-code-base-action@beta
        with:
          prompt_file: /tmp/claude-prompts/triage-prompt.txt
          allowed_tools: "Bash(gh label list),mcp__github__get_issue,mcp__github__get_issue_comments,mcp__github__update_issue,mcp__github__search_issues,mcp__github__list_issues"
          timeout_minutes: "5"
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          mcp_config: /tmp/mcp-config/mcp-servers.json
          claude_env: |
            GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}


================================================
FILE: .github/workflows/claude.yml
================================================
name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && (contains(github.event.issue.body, '@claude') || contains(github.event.issue.title, '@claude')))
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Run Claude Code
        id: claude
        uses: anthropics/claude-code-action@beta
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          
          # Optional: Specify model (defaults to Claude Sonnet 4, uncomment for Claude Opus 4)
          # model: "claude-opus-4-20250514"
          
          # Optional: Customize the trigger phrase (default: @claude)
          # trigger_phrase: "/claude"
          
          # Optional: Trigger when specific user is assigned to an issue
          # assignee_trigger: "claude-bot"
          
          # Optional: Allow Claude to run specific commands
          # allowed_tools: "Bash(npm install),Bash(npm run build),Bash(npm run test:*),Bash(npm run lint:*)"
          
          # Optional: Add custom instructions for Claude to customize its behavior for your project
          # custom_instructions: |
          #   Follow our coding standards
          #   Ensure all new code has tests
          #   Use TypeScript for new files
          
          # Optional: Custom environment variables for Claude
          # claude_env: |
          #   NODE_ENV: test


================================================
FILE: .github/workflows/create-release-tag.yml
================================================
name: Create Release Tag

on:
  pull_request:
    types: [closed]
    branches: [main]

jobs:
  create-tag:
    if: github.event.pull_request.merged == true && startsWith(github.event.pull_request.head.ref, 'release/v')
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Extract version from branch name
      id: extract_version
      run: |
        BRANCH_NAME="${{ github.event.pull_request.head.ref }}"
        VERSION="${BRANCH_NAME#release/v}"
        echo "version=$VERSION" >> $GITHUB_OUTPUT
    
    - name: Get previous release tag
      id: previous_tag
      run: |
        PREVIOUS_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
        echo "previous_tag=$PREVIOUS_TAG" >> $GITHUB_OUTPUT

    - name: Create and push tag
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        
        # Create annotated tag
        git tag -a "v${{ steps.extract_version.outputs.version }}" \
          -m "Release v${{ steps.extract_version.outputs.version }}"
        
        # Push tag
        git push origin "v${{ steps.extract_version.outputs.version }}"
    
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: v${{ steps.extract_version.outputs.version }}
        release_name: Release v${{ steps.extract_version.outputs.version }}
        body: |
          ## Release v${{ steps.extract_version.outputs.version }}
          
          Published to PyPI: https://pypi.org/project/claude-code-sdk/${{ steps.extract_version.outputs.version }}/
          
          ### Installation
          ```bash
          pip install claude-code-sdk==${{ steps.extract_version.outputs.version }}
          ```
          
          ### What's Changed
          See the [full changelog](https://github.com/${{ github.repository }}/compare/${{ steps.previous_tag.outputs.previous_tag }}...v${{ steps.extract_version.outputs.version }})
        draft: false
        prerelease: false



================================================
FILE: .github/workflows/lint.yml
================================================
name: Lint

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run ruff
      run: |
        ruff check src/ tests/
        ruff format --check src/ tests/
    
    - name: Run mypy
      run: |
        mypy src/


================================================
FILE: .github/workflows/publish.yml
================================================
name: Publish to PyPI

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to publish (e.g., 0.1.0)'
        required: true
        type: string
      test_pypi:
        description: 'Publish to Test PyPI first'
        required: false
        type: boolean
        default: true

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run ruff
      run: |
        ruff check src/ tests/
        ruff format --check src/ tests/
    
    - name: Run mypy
      run: |
        mypy src/

  publish:
    needs: [test, lint]
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    
    steps:
    - uses: actions/checkout@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    
    - name: Update version
      run: |
        # Update version in pyproject.toml
        sed -i 's/version = ".*"/version = "${{ github.event.inputs.version }}"/' pyproject.toml
        sed -i 's/__version__ = ".*"/__version__ = "${{ github.event.inputs.version }}"/' src/claude_code_sdk/__init__.py
    
    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: twine check dist/*
    
    - name: Publish to Test PyPI
      if: ${{ github.event.inputs.test_pypi == 'true' }}
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
      run: |
        twine upload --repository testpypi dist/*
        echo "Package published to Test PyPI"
        echo "Install with: pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ claude-code-sdk==${{ github.event.inputs.version }}"
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        twine upload dist/*
        echo "Package published to PyPI"
        echo "Install with: pip install claude-code-sdk==${{ github.event.inputs.version }}"
    
    - name: Create version update PR
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        # Create a new branch for the version update
        BRANCH_NAME="release/v${{ github.event.inputs.version }}"
        git checkout -b "$BRANCH_NAME"
        
        # Configure git
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        
        # Commit the version changes
        git add pyproject.toml src/claude_code_sdk/__init__.py
        git commit -m "chore: bump version to ${{ github.event.inputs.version }}"
        
        # Push the branch
        git push origin "$BRANCH_NAME"
        
        # Create PR using GitHub CLI (gh)
        gh pr create \
          --title "chore: bump version to ${{ github.event.inputs.version }}" \
          --body "This PR updates the version to ${{ github.event.inputs.version }} after publishing to PyPI.
          
          ## Changes
          - Updated version in \`pyproject.toml\`
          - Updated version in \`src/claude_code_sdk/__init__.py\`
          
          ## Release Information
          - Published to PyPI: https://pypi.org/project/claude-code-sdk/${{ github.event.inputs.version }}/
          - Install with: \`pip install claude-code-sdk==${{ github.event.inputs.version }}\`
          
          ## Next Steps
          After merging this PR, a release tag will be created automatically." \
          --base main \
          --head "$BRANCH_NAME"


================================================
FILE: .github/workflows/test.yml
================================================
name: Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=claude_code_sdk --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

