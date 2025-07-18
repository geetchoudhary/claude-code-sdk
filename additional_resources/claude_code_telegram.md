TITLE: Environment Configuration (.env Example)
DESCRIPTION: Illustrates typical environment variables required for the Claude integration and Telegram bot, including API keys and development settings. Recommended for local development.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_19

LANGUAGE: env
CODE:
```
USE_SDK=true
# ANTHROPIC_API_KEY=sk-ant-api03-your-development-key
DEBUG=true
DEVELOPMENT_MODE=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development
ENABLE_GIT_INTEGRATION=true
ENABLE_FILE_UPLOADS=true
ENABLE_QUICK_ACTIONS=true
```

----------------------------------------

TITLE: Pytest Unit and Async Tests
DESCRIPTION: Provides examples of writing unit tests using `pytest`, including testing configuration loading with custom parameters and asynchronous functions using `pytest.mark.asyncio`. Ensures code correctness and functionality.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_17

LANGUAGE: python
CODE:
```
import pytest
from src.config import create_test_config

def test_feature_with_config():
    """Test feature with specific configuration."""
    config = create_test_config(
        debug=True,
        claude_max_turns=5
    )
    
    # Test implementation
    assert config.debug is True
    assert config.claude_max_turns == 5

@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality."""
    # Test async code
    result = await some_async_function()
    assert result is not None
```

----------------------------------------

TITLE: Example .env Configuration File
DESCRIPTION: An example of a `.env` file showing common configuration parameters for the Telegram bot. It includes settings for Telegram, security, Claude integration, rate limiting, and Claude-specific parameters.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/configuration.md#_snippet_15

LANGUAGE: bash
CODE:
```
# Telegram Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_BOT_USERNAME=my_claude_bot

# Security
APPROVED_DIRECTORY=/home/user/projects
ALLOWED_USERS=123456789,987654321

# Optional: Token Authentication
ENABLE_TOKEN_AUTH=false
AUTH_TOKEN_SECRET=

# Claude Integration
USE_SDK=true                          # Use Python SDK (recommended)
ANTHROPIC_API_KEY=                    # Optional: Only if not using CLI auth

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Claude Settings
CLAUDE_MAX_COST_PER_USER=10.0
CLAUDE_TIMEOUT_SECONDS=300
CLAUDE_ALLOWED_TOOLS=Read,Write,Edit,Bash,Glob,Grep,LS,Task,MultiEdit,NotebookRead,NotebookEdit,WebFetch,TodoRead,TodoWrite,WebSearch
```

----------------------------------------

TITLE: Python Unit Test Example
DESCRIPTION: Provides an example of writing an asynchronous unit test using pytest, including setup and assertions.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/CONTRIBUTING.md#_snippet_8

LANGUAGE: Python
CODE:
```
import pytest
from src.config import create_test_config

@pytest.mark.asyncio
async def test_feature():
    """Test feature functionality."""
    config = create_test_config(debug=True)
    # Test implementation
    assert config.debug is True
```

----------------------------------------

TITLE: Claude SDK Manager for Python
DESCRIPTION: Manages integration with the Claude Code Python SDK. It supports native async operations, streaming responses, and direct API integration, leveraging CLI authentication or API keys. The manager is configured with API keys and timeouts, and the `execute_query` method handles prompt execution, streaming callbacks, and response formatting.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-5-claude-integration.md#_snippet_0

LANGUAGE: python
CODE:
```
import asyncio
from typing import AsyncIterator, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

# Assuming claude_code_sdk and Settings are defined elsewhere
# from claude_code_sdk import query, ClaudeCodeOptions
# from your_settings_module import Settings

# Mock classes for demonstration if not provided
class ClaudeCodeOptions:
    def __init__(self, api_key: str, timeout: int, working_directory: str):
        self.api_key = api_key
        self.timeout = timeout
        self.working_directory = working_directory

    def copy(self):
        return ClaudeCodeOptions(
            api_key=self.api_key,
            timeout=self.timeout,
            working_directory=self.working_directory
        )

async def query(prompt: str, options: ClaudeCodeOptions) -> AsyncIterator[Dict[str, Any]]:
    # Mock implementation of the query function
    print(f"Mock query called with prompt: {prompt}")
    yield {"type": "content", "text": "Mock response content."}
    yield {"type": "metadata", "session_id": "mock-session-123", "cost": 0.001, "duration_ms": 500, "num_turns": 1}

class Settings:
    def __init__(self):
        self.anthropic_api_key_str = "sk-mock-key"
        self.claude_timeout_seconds = 60
        self.approved_directory = "/tmp/approved"

@dataclass
class ClaudeResponse:
    """Response from Claude Code SDK"""
    content: str
    session_id: str
    cost: float
    duration_ms: int
    num_turns: int
    is_error: bool = False
    error_type: Optional[str] = None
    tools_used: list[Dict[str, Any]] = field(default_factory=list)

class ClaudeSDKManager:
    """Manage Claude Code SDK integration"""
    
    def __init__(self, config: Settings):
        self.config = config
        self.options = ClaudeCodeOptions(
            api_key=config.anthropic_api_key_str,
            timeout=config.claude_timeout_seconds,
            working_directory=config.approved_directory
        )
        
    async def execute_query(
        self, 
        prompt: str,
        working_directory: Path,
        session_id: Optional[str] = None,
        stream_callback: Optional[Callable] = None
    ) -> ClaudeResponse:
        """Execute Claude query using SDK"""
        
        last_update = {}
        try:
            # Configure options for this query
            options = self.options.copy()
            options.working_directory = str(working_directory)
            
            # Execute with streaming
            async for update in query(prompt, options):
                if stream_callback:
                    await stream_callback(update)
                last_update = update
                
            # Return final response
            return self._format_response(last_update, session_id)
            
        except Exception as e:
            return ClaudeResponse(
                content=f"Error: {str(e)}",
                session_id=session_id or "unknown",
                cost=0.0,
                duration_ms=0,
                num_turns=0,
                is_error=True,
                error_type=type(e).__name__
            )

    def _format_response(self, update: Dict[str, Any], session_id: Optional[str]) -> ClaudeResponse:
        """Format the SDK response into ClaudeResponse dataclass"""
        # This is a simplified formatter based on expected 'update' structure
        # A real implementation would parse 'update' more robustly
        return ClaudeResponse(
            content=update.get("text", ""),
            session_id=session_id or update.get("session_id", "unknown"),
            cost=update.get("cost", 0.0),
            duration_ms=update.get("duration_ms", 0),
            num_turns=update.get("num_turns", 0),
            is_error=update.get("is_error", False),
            error_type=update.get("error_type", None),
            tools_used=update.get("tools_used", [])
        )

# Example Usage (requires an async context):
# async def main():
#     settings = Settings()
#     manager = ClaudeSDKManager(settings)
#     response = await manager.execute_query(
#         prompt="Write a Python function to calculate factorial.",
#         working_directory=Path("./src/claude"),
#         stream_callback=lambda update: print(f"Stream: {update}")
#     )
#     print(f"Final Response: {response}")

# if __name__ == "__main__":
#     asyncio.run(main())

```

----------------------------------------

TITLE: Python Type Hinting Example
DESCRIPTION: Demonstrates the use of comprehensive type hints for function parameters and return values in Python.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/CONTRIBUTING.md#_snippet_5

LANGUAGE: Python
CODE:
```
from typing import Optional, List, Dict, Any
from pathlib import Path

async def process_data(
    items: List[Dict[str, Any]], 
    config: Optional[Path] = None
) -> bool:
    """Process data with optional config."""
    # Implementation
    return True
```

----------------------------------------

TITLE: Create Configuration File
DESCRIPTION: Copies the example environment file to a new file and instructs the user to edit it with their specific development settings.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_4

LANGUAGE: bash
CODE:
```
cp .env.example .env
# Edit .env with your development settings
```

----------------------------------------

TITLE: Message Formatter Example (Python)
DESCRIPTION: An example Python function demonstrating message formatting, likely for use within the bot's response generation. This snippet shows how to structure messages for clarity and user experience.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-4-bot-core.md#_snippet_15

LANGUAGE: python
CODE:
```
class MessageFormatter:
    def format_code_block(self, code: str, language: str = "") -> str:
        return f"```{{language}}
{{code}}
```"

    def format_bold(self, text: str) -> str:
        return f"*{{text}}*"

    def format_italic(self, text: str) -> str:
        return f"_{{text}}_"

    def format_link(self, text: str, url: str) -> str:
        return f"[{{text}}]({{url}})"

    def format_error(self, message: str) -> str:
        return f"❌ {{message}}"

    def format_success(self, message: str) -> str:
        return f"✅ {{message}}"
```

----------------------------------------

TITLE: Configure Bot for SDK with Direct API Key
DESCRIPTION: Environment variable configuration for using the SDK with a direct Anthropic API key. Requires obtaining an API key from the Anthropic console.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_2

LANGUAGE: env
CODE:
```
USE_SDK=true
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

----------------------------------------

TITLE: Claude Integration Configuration Options
DESCRIPTION: Details the different ways to configure the bot's integration with Claude, including using the SDK with CLI authentication, using an API key directly, or opting for CLI mode. This section covers environment variables and CLI commands for setup.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/configuration.md#_snippet_14

LANGUAGE: APIDOC
CODE:
```
Claude Integration Configuration:

SDK Mode (Default):
  - Uses the Claude Code Python SDK.
  - Supports streaming and better error handling.
  - Can leverage existing Claude CLI authentication or API key.

CLI Mode:
  - Uses Claude Code CLI subprocess.
  - Requires Claude CLI installation.
  - Uses CLI authentication only.

Authentication Options:

Option 1: Use Existing Claude CLI Authentication (Recommended)
  - Install and authenticate Claude CLI:
    claude auth login
  - Configure bot to use SDK with CLI auth:
    USE_SDK=true
    # ANTHROPIC_API_KEY is not needed as SDK uses CLI credentials.

Option 2: Direct API Key
  - Configure bot with API key:
    USE_SDK=true
    ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

Option 3: CLI Mode (Legacy)
  - Use CLI subprocess instead of SDK:
    USE_SDK=false
    # Requires Claude CLI to be installed and authenticated.
```

----------------------------------------

TITLE: Python Structured Logging Example
DESCRIPTION: Shows how to implement structured logging using the structlog library for better log analysis.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/CONTRIBUTING.md#_snippet_7

LANGUAGE: Python
CODE:
```
import structlog

logger = structlog.get_logger()

def some_function():
    logger.info("Operation started", operation="example", user_id=123)
    # Implementation
```

----------------------------------------

TITLE: Claude Code Bot API Documentation
DESCRIPTION: Documentation for interacting with the Claude Code Bot's functionalities via commands and configuration. Covers project analysis, Git operations, quick actions, and session management.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/README.md#_snippet_14

LANGUAGE: APIDOC
CODE:
```
Bot Commands:
  /git: Displays the current Git repository status, including branch, changes, and recent commits.
  /actions: Presents a menu of available quick actions for common development tasks.
  /export: Initiates a session export process, allowing the user to choose an output format (Markdown, HTML, JSON).

Quick Actions:
  Test: Executes the project's test suite.
  Install: Installs project dependencies.
  Format: Formats the project's code according to style guidelines.
  Find TODOs: Locates all 'TODO' comments within the project.
  Build: Compiles or builds the project.
  Git Status: Provides a summary of the Git repository's current state.

Configuration Settings:
  TELEGRAM_BOT_TOKEN: Your Telegram bot's authentication token.
  TELEGRAM_BOT_USERNAME: The username of your Telegram bot.
  APPROVED_DIRECTORY: The absolute path to the base directory for project access.
  ALLOWED_USERS: A comma-separated list of Telegram user IDs permitted to use the bot.
  USE_SDK: Boolean to determine if the Python SDK or CLI subprocess should be used for Claude integration.
  ANTHROPIC_API_KEY: Your Anthropic API key, used if not relying on CLI authentication.
  CLAUDE_MAX_COST_PER_USER: Maximum cost in USD allowed per user.
  CLAUDE_TIMEOUT_SECONDS: Timeout duration in seconds for bot operations.
  CLAUDE_ALLOWED_TOOLS: A comma-separated list of tools the Claude model is permitted to use.
  RATE_LIMIT_REQUESTS: The number of requests allowed within the specified window.
  RATE_LIMIT_WINDOW: The time window in seconds for rate limiting.
  ENABLE_GIT_INTEGRATION: Boolean to enable or disable Git integration features.
  ENABLE_FILE_UPLOADS: Boolean to enable or disable file upload capabilities.
  ENABLE_QUICK_ACTIONS: Boolean to enable or disable the quick actions menu.
  DEBUG: Boolean for enabling debug mode.
  LOG_LEVEL: Sets the logging verbosity (e.g., INFO, DEBUG, ERROR).
```

----------------------------------------

TITLE: Verify Anthropic API Key
DESCRIPTION: Checks if the Anthropic API key environment variable is set correctly for SDK and CLI authentication.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_19

LANGUAGE: bash
CODE:
```
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Should start with: sk-ant-api03-
# Get a new key from: https://console.anthropic.com/
```

----------------------------------------

TITLE: ClaudeIntegration Class API
DESCRIPTION: Provides the main integration point for Claude Code, offering methods to run commands, manage user sessions, and retrieve session details. It handles session creation, command execution with streaming callbacks, and session continuation.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-5-claude-integration.md#_snippet_13

LANGUAGE: APIDOC
CODE:
```
ClaudeIntegration:
  __init__(config: Settings, process_manager: ClaudeProcessManager, session_manager: SessionManager, tool_monitor: ToolMonitor)
    Initializes the Claude integration facade with necessary components.
    Parameters:
      config: Configuration settings for the integration.
      process_manager: Manages the execution of Claude Code processes.
      session_manager: Manages user sessions.
      tool_monitor: Monitors and validates tool calls.

  run_command(prompt: str, working_directory: Path, user_id: int, session_id: Optional[str] = None, on_stream: Optional[Callable[[StreamUpdate], None]] = None) -> ClaudeResponse
    Runs a Claude Code command with full integration, including session management and streaming updates.
    Parameters:
      prompt: The user's prompt or command.
      working_directory: The directory where the command should be executed.
      user_id: The unique identifier for the user.
      session_id: Optional. The ID of an existing session to continue.
      on_stream: Optional. A callback function to handle streaming updates.
    Returns: The ClaudeResponse object containing the command output.
    Notes:
      - Manages session creation or retrieval.
      - Validates tool calls within the stream handler.
      - Updates session state after command execution.

  continue_session(user_id: int, working_directory: Path, prompt: Optional[str] = None) -> Optional[ClaudeResponse]
    Continues the most recent session for a given user in a specific working directory.
    Parameters:
      user_id: The unique identifier for the user.
      working_directory: The directory of the session to continue.
      prompt: Optional. Additional prompt to send to the session.
    Returns: The ClaudeResponse from the continued session, or None if no matching session is found.
    Notes:
      - Retrieves all sessions for the user.
      - Filters sessions by the provided working directory.
      - Selects the latest session based on 'last_used' timestamp.

  get_session_info(session_id: str) -> Optional[Dict[str, Any]]
    Retrieves detailed information about a specific session.
    Parameters:
      session_id: The ID of the session to retrieve information for.
    Returns: A dictionary containing session details (ID, project, timestamps, cost, turns, messages, tools used), or None if the session is not found.
    Notes:
      - Checks active sessions first, then attempts to load from storage.
```

----------------------------------------

TITLE: Configure Bot Environment Variables
DESCRIPTION: Steps to copy the example environment file and edit it with required settings like Telegram token and Claude integration details.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_5

LANGUAGE: bash
CODE:
```
# Copy the example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

----------------------------------------

TITLE: Telegram Bot Usage Example
DESCRIPTION: Demonstrates a typical interaction flow with the Telegram bot, showing directory navigation and code assistance requests.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/README.md#_snippet_0

LANGUAGE: text
CODE:
```
You: cd my-project
Bot: 📂 Changed to: my-project/

You: ls  
Bot: 📁 src/
     📁 tests/
     📄 README.md
     📄 package.json

You: Can you help me add error handling to src/api.py?
Bot: 🤖 I'll help you add robust error handling to your API...
     [Claude analyzes your code and suggests improvements]
```

----------------------------------------

TITLE: Configure Development Environment
DESCRIPTION: Copies the example environment file and instructs to edit it with specific development settings.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/CONTRIBUTING.md#_snippet_2

LANGUAGE: Bash
CODE:
```
cp .env.example .env
# Edit .env with your development settings
```

----------------------------------------

TITLE: Check Telegram Bot Token
DESCRIPTION: Prints the Telegram bot token to the console, which is essential for the bot to connect to the Telegram API.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_16

LANGUAGE: bash
CODE:
```
# Check your bot token
echo $TELEGRAM_BOT_TOKEN
```

----------------------------------------

TITLE: Show Available Make Commands
DESCRIPTION: Displays a help message listing all available commands that can be executed via the 'make' utility.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_11

LANGUAGE: bash
CODE:
```
make help
```

----------------------------------------

TITLE: Required Environment Variables
DESCRIPTION: Essential configuration parameters for the Telegram bot, including Telegram API credentials, security settings, and Claude integration mode.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_6

LANGUAGE: env
CODE:
```
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_BOT_USERNAME=your_bot_username

# Security
APPROVED_DIRECTORY=/path/to/your/projects
ALLOWED_USERS=123456789  # Your Telegram user ID

# Claude Integration (choose based on your authentication method above)
USE_SDK=true                          # true for SDK, false for CLI
ANTHROPIC_API_KEY=                    # Only needed for Option B above
```

----------------------------------------

TITLE: Testing Configuration Loading (Python)
DESCRIPTION: A Python snippet to test the configuration loading mechanism and print the loaded configuration model.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_26

LANGUAGE: python
CODE:
```
from src.config import load_config
config = load_config()
print(config.model_dump())
```

----------------------------------------

TITLE: Structured Logging with Structlog
DESCRIPTION: Shows how to initialize `structlog` and use its logger for info, debug, and error messages, including contextual data. Demonstrates logging within a `try...except` block for robust error reporting.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_16

LANGUAGE: python
CODE:
```
import structlog

logger = structlog.get_logger()

def some_function():
    logger.info("Operation started", operation="example", user_id=123)
    try:
        # Some operation
        logger.debug("Step completed", step="validation")
    except Exception as e:
        logger.error("Operation failed", error=str(e), operation="example")
        raise
```

----------------------------------------

TITLE: Install and Authenticate Claude CLI
DESCRIPTION: Steps to install the Claude CLI and authenticate your session, which the bot can leverage for API access.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
# Install Claude CLI
# Follow instructions at https://claude.ai/code

# Authenticate with Claude
claude

# follow the prompts to authenticate

# The bot will automatically use your CLI credentials
```

----------------------------------------

TITLE: Install Poetry
DESCRIPTION: Installs Poetry, a dependency management and packaging tool for Python, using pip.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install poetry
```

----------------------------------------

TITLE: Run Bot
DESCRIPTION: Starts the Telegram bot application in normal operating mode.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_9

LANGUAGE: bash
CODE:
```
make run
```

----------------------------------------

TITLE: Python Configuration Processing
DESCRIPTION: Demonstrates a Python function for processing configuration settings, potentially with overrides, returning a Path object.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_14

LANGUAGE: python
CODE:
```
from typing import Optional, List, Dict, Any
from pathlib import Path

def process_config(
    settings: Settings, 
    overrides: Optional[Dict[str, Any]] = None
) -> Path:
    """Process configuration with optional overrides."""
    # Implementation
    return Path("/example")
```

----------------------------------------

TITLE: Run the Claude Code Telegram Bot
DESCRIPTION: Commands to start the bot, with options for debug mode (recommended for initial setup) and standard production mode.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_8

LANGUAGE: bash
CODE:
```
# Start in debug mode (recommended for first run)
make run-debug

# Or for production
make run
```

----------------------------------------

TITLE: Optional Environment Variables for Claude Configuration
DESCRIPTION: Settings related to Claude integration, such as the SDK usage, API key, maximum conversation turns, timeouts, cost limits, and allowed tools.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/configuration.md#_snippet_2

LANGUAGE: bash
CODE:
```
# Integration Method
USE_SDK=true                          # Use Python SDK (default) or CLI subprocess
ANTHROPIC_API_KEY=sk-ant-api03-...

# Maximum conversation turns before requiring new session
CLAUDE_MAX_TURNS=10

# Timeout for Claude operations in seconds
CLAUDE_TIMEOUT_SECONDS=300

# Maximum cost per user in USD
CLAUDE_MAX_COST_PER_USER=10.0

# Allowed Claude tools (comma-separated list)
CLAUDE_ALLOWED_TOOLS=Read,Write,Edit,Bash,Glob,Grep,LS,Task,MultiEdit,NotebookRead,NotebookEdit,WebFetch,TodoRead,TodoWrite,WebSearch
```

----------------------------------------

TITLE: Install Development Dependencies
DESCRIPTION: Installs all project dependencies, including development tools and libraries, using the 'make dev' command.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_2

LANGUAGE: bash
CODE:
```
make dev
```

----------------------------------------

TITLE: Run Bot in Debug Mode
DESCRIPTION: Starts the Telegram bot application with enhanced logging for debugging purposes.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_10

LANGUAGE: bash
CODE:
```
make run-debug
```

----------------------------------------

TITLE: Install Bot Dependencies
DESCRIPTION: Commands to clone the repository, install Poetry (if needed), and install project dependencies using make.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_4

LANGUAGE: bash
CODE:
```
# Clone the repository
git clone https://github.com/yourusername/claude-code-telegram.git
cd claude-code-telegram

# Install Poetry (if needed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
make dev
```

----------------------------------------

TITLE: Get Telegram User ID
DESCRIPTION: Instructions on how to obtain your Telegram user ID by messaging a specific bot, which is needed for the ALLOWED_USERS configuration.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_7

LANGUAGE: bash
CODE:
```
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID number
3. Add this number to your `ALLOWED_USERS` setting
```

----------------------------------------

TITLE: Clone Repository
DESCRIPTION: Clones the project repository from a given URL and navigates into the project directory.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_0

LANGUAGE: bash
CODE:
```
git clone <repository-url>
cd claude-code-telegram
```

----------------------------------------

TITLE: Adding New Configuration Option (Python)
DESCRIPTION: Procedure for adding a new configuration setting to the application. Involves updating the settings class, example environment file, and tests.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_23

LANGUAGE: python
CODE:
```
from pydantic import Field

# Add to Settings class in src/config/settings.py
new_setting: bool = Field(False, description="Description of new setting")
```

----------------------------------------

TITLE: Setup Pre-commit Hooks
DESCRIPTION: Installs pre-commit hooks to automate code formatting, linting, and other checks before committing changes.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_3

LANGUAGE: bash
CODE:
```
poetry run pre-commit install
```

----------------------------------------

TITLE: Prevent Secret Commits
DESCRIPTION: Provides examples of files and patterns to add to a `.gitignore` file to prevent committing sensitive information like API keys or private keys.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/SECURITY.md#_snippet_9

LANGUAGE: bash
CODE:
```
# Add to .gitignore
.env
*.key
*.pem
config/secrets.yml
```

----------------------------------------

TITLE: Format Code
DESCRIPTION: Automatically formats all code files in the project according to predefined style guidelines.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_7

LANGUAGE: bash
CODE:
```
make format
```

----------------------------------------

TITLE: Handle Exceptions with Custom Hierarchy
DESCRIPTION: Demonstrates catching specific exceptions and re-raising them as custom `ConfigurationError` or `SecurityError` from `src.exceptions.py`. Shows how to chain exceptions using `from e` for better traceback information.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_15

LANGUAGE: python
CODE:
```
from src.exceptions import ConfigurationError, SecurityError

try:
    # Some operation
    pass
except ValueError as e:
    raise ConfigurationError(f"Invalid configuration: {e}") from e
```

----------------------------------------

TITLE: Install Production Dependencies
DESCRIPTION: Installs only the dependencies required for the production environment, excluding development tools.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_12

LANGUAGE: bash
CODE:
```
make install
```

----------------------------------------

TITLE: Example .env Configuration Template
DESCRIPTION: A template file (`.env.example`) outlining all configurable parameters for the Claude Code Telegram Bot. It covers required settings, security, Claude integration, rate limiting, storage, feature flags, monitoring, and development options.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-2-configuration.md#_snippet_6

LANGUAGE: bash
CODE:
```
# Claude Code Telegram Bot Configuration

# === REQUIRED SETTINGS ===
# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Bot username (without @)
TELEGRAM_BOT_USERNAME=your_bot_username

# Base directory for project access (absolute path)
APPROVED_DIRECTORY=/home/user/projects

# === SECURITY SETTINGS ===
# Comma-separated list of allowed Telegram user IDs (optional)
# Leave empty to allow all users (not recommended for production)
ALLOWED_USERS=123456789,987654321

# Enable token-based authentication
ENABLE_TOKEN_AUTH=false

# Secret for generating auth tokens (required if ENABLE_TOKEN_AUTH=true)
# Generate with: openssl rand -hex 32
AUTH_TOKEN_SECRET=

# === CLAUDE SETTINGS ===
# Maximum conversation turns before requiring new session
CLAUDE_MAX_TURNS=10

# Timeout for Claude operations (seconds)
CLAUDE_TIMEOUT_SECONDS=300

# Maximum cost per user in USD
CLAUDE_MAX_COST_PER_USER=10.0

# === RATE LIMITING ===
# Number of requests allowed per window
RATE_LIMIT_REQUESTS=10

# Rate limit window in seconds
RATE_LIMIT_WINDOW=60

# Burst capacity for rate limiting
RATE_LIMIT_BURST=20

# === STORAGE SETTINGS ===
# Database URL (SQLite by default)
DATABASE_URL=sqlite:///data/bot.db

# Session timeout in hours
SESSION_TIMEOUT_HOURS=24

# Maximum concurrent sessions per user
MAX_SESSIONS_PER_USER=5

# === FEATURE FLAGS ===
# Enable Model Context Protocol
ENABLE_MCP=false

# Path to MCP configuration file
MCP_CONFIG_PATH=

# Enable Git integration
ENABLE_GIT_INTEGRATION=true

# Enable file upload handling
ENABLE_FILE_UPLOADS=true

# Enable quick action buttons
ENABLE_QUICK_ACTIONS=true

# === MONITORING ===
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Enable anonymous telemetry
ENABLE_TELEMETRY=false

# Sentry DSN for error tracking (optional)
SENTRY_DSN=

# === DEVELOPMENT ===
# Enable debug mode
DEBUG=false

# Enable development features
DEVELOPMENT_MODE=false

```

----------------------------------------

TITLE: User Repository: CRUD Operations and Allowed User Retrieval
DESCRIPTION: Provides methods for creating, reading, updating, and retrieving user data from the database. It includes functions to get a user by ID, create a new user, update existing user details, and fetch a list of allowed user IDs.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-6-storage.md#_snippet_8

LANGUAGE: python
CODE:
```
class UserRepository:
    """User data access"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    async def get_user(self, user_id: int) -> Optional[UserModel]:
        """Get user by ID"""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return UserModel.from_row(row) if row else None
    
    async def create_user(self, user: UserModel) -> UserModel:
        """Create new user"""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, telegram_username, is_allowed)
                VALUES (?, ?, ?)
            """, (user.user_id, user.telegram_username, user.is_allowed))
            await conn.commit()
            return user
    
    async def update_user(self, user: UserModel):
        """Update user data"""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE users 
                SET telegram_username = ?, last_active = ?, 
                    total_cost = ?, message_count = ?, session_count = ?
                WHERE user_id = ?
            """, (
                user.telegram_username, user.last_active,
                user.total_cost, user.message_count, user.session_count,
                user.user_id
            ))
            await conn.commit()
    
    async def get_allowed_users(self) -> List[int]:
        """Get list of allowed user IDs"""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT user_id FROM users WHERE is_allowed = TRUE"
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
```

----------------------------------------

TITLE: Claude CLI Interaction (APIDOC)
DESCRIPTION: Details the command-line interface arguments used by the Claude Code tool, as constructed by the `ClaudeProcessManager`. This covers options for prompts, session management, output formats, and safety limits.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-5-claude-integration.md#_snippet_4

LANGUAGE: APIDOC
CODE:
```
claude [options] [prompt]

Executes commands or prompts against the Claude Code model.

Options:
  -p, --prompt <prompt>              The prompt to send to Claude.
  --continue                         Continue the previous session without a new prompt.
  --continue <prompt>                Continue the previous session with a new prompt.
  --resume <session_id>              Resume a specific session using its ID.
  --output-format <format>           Specify the output format. Supported: 'stream-json'.
                                     'stream-json' provides real-time updates.
  --max-turns <number>               Set the maximum number of turns for the conversation.
  --allowedTools <tool_list>         Comma-separated list of allowed tools (e.g., 'python,bash').

Examples:
  # Execute a new prompt
  claude -p "Write a Python script to list files"

  # Continue a session with a new prompt
  claude --continue "Add error handling to the previous script" --resume "session-abc123"

  # Continue a session without a new prompt (e.g., to get final output)
  claude --continue --resume "session-abc123"

  # Execute with specific output format and tool limits
  claude -p "Analyze this data" --output-format stream-json --max-turns 10 --allowedTools python,pandas
```

----------------------------------------

TITLE: Configure Environment Variables
DESCRIPTION: Instructions for copying the example environment file and editing it with essential bot configurations like Telegram token, username, approved directories, and allowed users.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/README.md#_snippet_3

LANGUAGE: shell
CODE:
```
# Copy the example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

----------------------------------------

TITLE: Testing Configuration Loading
DESCRIPTION: Demonstrates how to create a test configuration object with specific overrides using the `create_test_config` function. This is useful for unit testing application logic.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/configuration.md#_snippet_12

LANGUAGE: python
CODE:
```
from src.config import create_test_config

# Create test config with overrides
config = create_test_config(
    claude_max_turns=5,
    debug=True
)
```

----------------------------------------

TITLE: Clean Generated Files
DESCRIPTION: Removes temporary or generated files from the project directory to ensure a clean state.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_13

LANGUAGE: bash
CODE:
```
make clean
```

----------------------------------------

TITLE: Registering Telegram Handlers (Python)
DESCRIPTION: Demonstrates registering various handlers for commands, text messages, documents, photos, and callback queries using `CommandHandler`, `MessageHandler`, and `CallbackQueryHandler`. Includes error handler registration.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-4-bot-core.md#_snippet_3

LANGUAGE: python
CODE:
```
def _register_handlers(self):
    """Register all command and message handlers"""
    # Import handlers
    from .handlers import command, message, callback
    
    # Command handlers
    self.app.add_handler(CommandHandler("start", self._inject_deps(command.start_command)))
    self.app.add_handler(CommandHandler("help", self._inject_deps(command.help_command)))
    self.app.add_handler(CommandHandler("new", self._inject_deps(command.new_session)))
    self.app.add_handler(CommandHandler("continue", self._inject_deps(command.continue_session)))
    self.app.add_handler(CommandHandler("ls", self._inject_deps(command.list_files)))
    self.app.add_handler(CommandHandler("cd", self._inject_deps(command.change_directory)))
    self.app.add_handler(CommandHandler("pwd", self._inject_deps(command.print_working_directory)))
    self.app.add_handler(CommandHandler("projects", self._inject_deps(command.show_projects)))
    self.app.add_handler(CommandHandler("status", self._inject_deps(command.session_status)))
    
    # Message handlers
    self.app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        self._inject_deps(message.handle_text_message)
    ))
    self.app.add_handler(MessageHandler(
        filters.Document.ALL,
        self._inject_deps(message.handle_document)
    ))
    self.app.add_handler(MessageHandler(
        filters.PHOTO,
        self._inject_deps(message.handle_photo)
    ))
    
    # Callback query handler
    self.app.add_handler(CallbackQueryHandler(
        self._inject_deps(callback.handle_callback_query)
    ))
    
    # Error handler
    self.app.add_error_handler(self._error_handler)
```

----------------------------------------

TITLE: Claude and Feature Configuration (.env)
DESCRIPTION: Optional environment variables for customizing Claude integration, rate limiting, and feature enablement. Includes API key, cost limits, timeouts, and allowed tools.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/README.md#_snippet_13

LANGUAGE: env
CODE:
```
# Claude Settings
USE_SDK=true                        # Use Python SDK (default) or CLI subprocess
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MAX_COST_PER_USER=10.0       # Max cost per user in USD
CLAUDE_TIMEOUT_SECONDS=300          # Timeout for operations  
CLAUDE_ALLOWED_TOOLS="Read,Write,Edit,Bash,Glob,Grep,LS,Task,MultiEdit,NotebookRead,NotebookEdit,WebFetch,TodoRead,TodoWrite,WebSearch"

# Rate Limiting  
RATE_LIMIT_REQUESTS=10              # Requests per window
RATE_LIMIT_WINDOW=60                # Window in seconds

# Features
ENABLE_GIT_INTEGRATION=true
ENABLE_FILE_UPLOADS=true
ENABLE_QUICK_ACTIONS=true

# Development
DEBUG=false
LOG_LEVEL=INFO
```

----------------------------------------

TITLE: Python Unit Tests for Configuration
DESCRIPTION: Provides examples of unit tests for configuration loading and validation. It covers testing required fields, parsing user IDs, environment overrides, and the feature flag system, ensuring robust configuration management.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-2-configuration.md#_snippet_9

LANGUAGE: python
CODE:
```
# tests/test_config.py
"""
Test configuration loading and validation
"""

def test_required_fields():
    """Test that missing required fields raise errors"""
    pass
    
def test_validator_allowed_users():
    """Test parsing of comma-separated user IDs"""
    pass
    
def test_environment_overrides():
    """Test environment-specific configurations"""
    pass

def test_feature_flags():
    """Test feature flag system"""
    pass

```

----------------------------------------

TITLE: Configure Bot for SDK with CLI Authentication
DESCRIPTION: Environment variable configuration for using the SDK with existing Claude CLI authentication. ANTHROPIC_API_KEY should be left empty.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_1

LANGUAGE: env
CODE:
```
USE_SDK=true
# Leave ANTHROPIC_API_KEY empty - SDK will use CLI credentials
```

----------------------------------------

TITLE: Python Rate Limiter with Token Bucket and Cost Control
DESCRIPTION: Implements a rate limiting system using the token bucket algorithm for request frequency and a cost-based system for resource usage. It tracks user requests and associated costs, preventing abuse and managing resource allocation. The system uses asyncio for concurrent operations and dataclasses for bucket state.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-3-authentication.md#_snippet_1

LANGUAGE: python
CODE:
```
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting"""
    capacity: int
    tokens: float
    last_update: datetime
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on time passed"""
        now = datetime.utcnow()
        elapsed = (now - self.last_update).total_seconds()
        self.tokens = min(self.capacity, self.tokens + elapsed)
        self.last_update = now

class RateLimiter:
    """Main rate limiting system"""
    
    def __init__(self, config: 'Settings'):
        self.config = config
        self.request_buckets: Dict[int, RateLimitBucket] = {}
        self.cost_tracker: Dict[int, float] = defaultdict(float)
        self.locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def check_rate_limit(self, user_id: int, cost: float = 1.0) -> Tuple[bool, Optional[str]]:
        """Check if request is allowed"""
        async with self.locks[user_id]:
            # Check request rate
            if not self._check_request_rate(user_id):
                return False, "Rate limit exceeded. Please wait before making more requests."
            
            # Check cost limit
            if not self._check_cost_limit(user_id, cost):
                remaining = self.config.claude_max_cost_per_user - self.cost_tracker[user_id]
                return False, f"Cost limit exceeded. Remaining budget: ${remaining:.2f}"
            
            return True, None
    
    def _check_request_rate(self, user_id: int) -> bool:
        """Check request rate limit"""
        if user_id not in self.request_buckets:
            self.request_buckets[user_id] = RateLimitBucket(
                capacity=self.config.rate_limit_burst,
                tokens=self.config.rate_limit_burst,
                last_update=datetime.utcnow()
            )
        
        return self.request_buckets[user_id].consume()
    
    def _check_cost_limit(self, user_id: int, cost: float) -> bool:
        """Check cost-based limit"""
        if self.cost_tracker[user_id] + cost > self.config.claude_max_cost_per_user:
            return False
        
        self.cost_tracker[user_id] += cost
        return True
    
    async def reset_user_limits(self, user_id: int):
        """Reset limits for a user"""
        async with self.locks[user_id]:
            self.cost_tracker[user_id] = 0
            if user_id in self.request_buckets:
                self.request_buckets[user_id].tokens = self.config.rate_limit_burst

```

----------------------------------------

TITLE: Basic Configuration Loading in Python
DESCRIPTION: Shows the basic usage of the `load_config` function to load application settings with automatic environment detection. It illustrates accessing configuration values like the Telegram bot token and Claude max cost.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/configuration.md#_snippet_10

LANGUAGE: python
CODE:
```
from src.config import load_config

# Load with automatic environment detection
config = load_config()

# Access configuration
bot_token = config.telegram_token_str
max_cost = config.claude_max_cost_per_user
```

----------------------------------------

TITLE: Run the Telegram Bot
DESCRIPTION: Commands to start the Telegram bot, either in debug mode for development or in a standard mode for production environments.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/README.md#_snippet_5

LANGUAGE: shell
CODE:
```
# Start in debug mode
make run-debug

# Or for production
make run
```

----------------------------------------

TITLE: Monitor Usage and Costs via Logs
DESCRIPTION: Provides commands to check bot status and monitor logs for cost-related information.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_26

LANGUAGE: bash
CODE:
```
# Check usage in Telegram
/status

# Monitor logs for cost tracking
tail -f logs/bot.log | grep -i cost
```

----------------------------------------

TITLE: Activate Poetry Environment
DESCRIPTION: Activates the virtual environment managed by Poetry for the current project, allowing access to installed dependencies.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/development.md#_snippet_5

LANGUAGE: bash
CODE:
```
poetry shell
```

----------------------------------------

TITLE: Python Configuration Loading Usage Example
DESCRIPTION: Demonstrates a simple usage pattern for the `load_config` function. It shows how to import the function, load the configuration, and access a specific setting like the Telegram bot token, which is retrieved as a secret value.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-2-configuration.md#_snippet_7

LANGUAGE: python
CODE:
```
# Simple usage
from src.config import load_config

config = load_config()
bot_token = config.telegram_bot_token.get_secret_value()

```

----------------------------------------

TITLE: Database Connection Pooling
DESCRIPTION: Provides a context manager to get a database connection from the pool. If the pool is empty, a new connection is created. Connections are returned to the pool or closed if the pool is full.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-6-storage.md#_snippet_6

LANGUAGE: Python
CODE:
```
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Get database connection from pool"""
        async with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
            else:
                conn = await aiosqlite.connect(self.database_path)
                await conn.execute("PRAGMA foreign_keys = ON")
        
        try:
            yield conn
        finally:
            async with self._pool_lock:
                if len(self._connection_pool) < self._pool_size:
                    self._connection_pool.append(conn)
                else:
                    await conn.close()

```

----------------------------------------

TITLE: Environment-Specific Configuration Loading
DESCRIPTION: Illustrates how to explicitly load configuration for a specific environment, such as 'production'. It also shows how to check the current environment using `config.is_production`.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/configuration.md#_snippet_11

LANGUAGE: python
CODE:
```
from src.config import load_config

# Explicitly load production config
config = load_config(env="production")

# Check if running in production
if config.is_production:
    # Production-specific behavior
    pass
```

----------------------------------------

TITLE: Install Claude CLI and Authenticate
DESCRIPTION: Steps to install the Claude CLI and authenticate your session. This is a prerequisite for SDK with CLI authentication.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_0

LANGUAGE: bash
CODE:
```
# 1. Install Claude CLI
# Visit https://claude.ai/code and follow installation instructions

# 2. Authenticate with Claude
claude auth login

# 3. Verify authentication
claude auth status
# Should show: "✓ You are authenticated"
```

----------------------------------------

TITLE: ClaudeCodeBot Initialization and Core Logic (Python)
DESCRIPTION: Details the `ClaudeCodeBot` class, its constructor, and the `initialize` method. Covers setting up the Telegram `Application`, registering commands, handlers, middleware, and configuring webhook or polling.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/todo-4-bot-core.md#_snippet_1

LANGUAGE: python
CODE:
```
class ClaudeCodeBot:
    """Main bot orchestrator"""
    
    def __init__(self, config: Settings, dependencies: Dict[str, Any]):
        self.config = config
        self.deps = dependencies
        self.app: Optional[Application] = None
        self.handlers: Dict[str, Callable] = {}
        
    async def initialize(self):
        """Initialize bot application"""
        # Create application
        self.app = Application.builder().token(
            self.config.telegram_bot_token.get_secret_value()
        ).build()
        
        # Set bot commands for menu
        await self._set_bot_commands()
        
        # Register handlers
        self._register_handlers()
        
        # Add middleware
        self._add_middleware()
        
        # Initialize webhook or polling
        if self.config.webhook_url:
            await self._setup_webhook()
            
    async def start(self):
        """Start the bot"""
        await self.initialize()
        
        if self.config.webhook_url:
            # Webhook mode
            await self.app.run_webhook(
                listen="0.0.0.0",
                port=self.config.webhook_port,
                url_path=self.config.webhook_path,
                webhook_url=self.config.webhook_url
            )
        else:
            # Polling mode
            await self.app.run_polling()
```

----------------------------------------

TITLE: Cost-Based Limiting Configuration
DESCRIPTION: Defines the maximum cost in USD that a user can incur, helping to manage operational expenses.
SOURCE: https://github.com/richardatct/claude-code-telegram/blob/main/docs/setup.md#_snippet_13

LANGUAGE: bash
CODE:
```
CLAUDE_MAX_COST_PER_USER=10.0   # Max cost per user in USD
```