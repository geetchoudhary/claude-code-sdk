Directory structure:
└── disler-claude-code-hooks-mastery/
    ├── README.md
    ├── CLAUDE.md
    ├── .env.sample
    ├── ai_docs/
    │   ├── anthropic_quick_start.md
    │   ├── cc_hooks_docs.md
    │   ├── cc_hooks_v0_repomix.xml
    │   ├── openai_quick_start.md
    │   └── uv-single-file-scripts.md
    ├── apps/
    │   ├── hello.py
    │   └── hello.ts
    └── .claude/
        ├── settings.json
        ├── commands/
        │   ├── all_tools.md
        │   ├── git_status.md
        │   ├── prime.md
        │   └── sentient.md
        └── hooks/
            ├── notification.py
            ├── post_tool_use.py
            ├── pre_tool_use.py
            ├── stop.py
            ├── subagent_stop.py
            └── utils/
                ├── llm/
                │   ├── anth.py
                │   └── oai.py
                └── tts/
                    ├── elevenlabs_tts.py
                    ├── openai_tts.py
                    └── pyttsx3_tts.py


Files Content:

================================================
FILE: README.md
================================================
# Claude Code Hooks Mastery

[Claude Code Hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) - Quickly master how to use Claude Code hooks to add deterministic (or non-deterministic) control over Claude Code's behavior.

<img src="images/hooked.png" alt="Claude Code Hooks" style="max-width: 800px; width: 100%;" />

## Prerequisites

This requires:
- **[Astral UV](https://docs.astral.sh/uv/getting-started/installation/)** - Fast Python package installer and resolver
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** - Anthropic's CLI for Claude AI

Optional:
- **[ElevenLabs](https://elevenlabs.io/)** - Text-to-speech provider
- **[OpenAI](https://openai.com/)** - Language model provider + Text-to-speech provider
- **[Anthropic](https://www.anthropic.com/)** - Language model provider

## Hook Lifecycle & Payloads

This demo captures all 5 Claude Code hook lifecycle events with their JSON payloads:

### 1. PreToolUse Hook
**Fires:** Before any tool execution  
**Payload:** `tool_name`, `tool_input` parameters  
**Enhanced:** Blocks dangerous commands (`rm -rf`, `.env` access)

### 2. PostToolUse Hook  
**Fires:** After successful tool completion  
**Payload:** `tool_name`, `tool_input`, `tool_response` with results

### 3. Notification Hook
**Fires:** When Claude Code sends notifications (waiting for input, etc.)  
**Payload:** `message` content  
**Enhanced:** TTS alerts - "Your agent needs your input" (30% chance includes name)

### 4. Stop Hook
**Fires:** When Claude Code finishes responding  
**Payload:** `stop_hook_active` boolean flag  
**Enhanced:** AI-generated completion messages with TTS playback

### 5. SubagentStop Hook
**Fires:** When Claude Code subagents (Task tools) finish responding  
**Payload:** `stop_hook_active` boolean flag  
**Enhanced:** TTS playback - "Subagent Complete"

## What This Shows

- **Complete hook lifecycle coverage** - All 5 hook events implemented and logging
- **Intelligent TTS system** - AI-generated audio feedback with voice priority (ElevenLabs > OpenAI > pyttsx3)
- **Security enhancements** - Blocks dangerous commands and sensitive file access
- **Personalized experience** - Uses engineer name from environment variables
- **Automatic logging** - All hook events are logged as JSON to `logs/` directory  
- **Chat transcript extraction** - PostToolUse hook converts JSONL transcripts to readable JSON format

> **Warning:** The `chat.json` file contains only the most recent Claude Code conversation. It does not preserve conversations from previous sessions - each new conversation is fully copied and overwrites the previous one. This is unlike the other logs which are appended to from every claude code session.

## UV Single-File Scripts Architecture

This project leverages **[UV single-file scripts](https://docs.astral.sh/uv/guides/scripts/)** to keep hook logic cleanly separated from your main codebase. All hooks live in `.claude/hooks/` as standalone Python scripts with embedded dependency declarations.

**Benefits:**
- **Isolation** - Hook logic stays separate from your project dependencies
- **Portability** - Each hook script declares its own dependencies inline
- **No Virtual Environment Management** - UV handles dependencies automatically
- **Fast Execution** - UV's dependency resolution is lightning-fast
- **Self-Contained** - Each hook can be understood and modified independently

This approach ensures your hooks remain functional across different environments without polluting your main project's dependency tree.

## Key Files

- `.claude/settings.json` - Hook configuration with permissions
- `.claude/hooks/` - Python scripts using uv for each hook type
  - `pre_tool_use.py` - Security blocking and logging
  - `post_tool_use.py` - Logging and transcript conversion
  - `notification.py` - Logging with optional TTS (--notify flag)
  - `stop.py` - AI-generated completion messages with TTS
  - `subagent_stop.py` - Simple "Subagent Complete" TTS
  - `utils/` - Intelligent TTS and LLM utility scripts
    - `tts/` - Text-to-speech providers (ElevenLabs, OpenAI, pyttsx3)
    - `llm/` - Language model integrations (OpenAI, Anthropic)
- `logs/` - JSON logs of all hook executions
  - `pre_tool_use.json` - Tool use events with security blocking
  - `post_tool_use.json` - Tool completion events
  - `notification.json` - Notification events
  - `stop.json` - Stop events with completion messages
  - `subagent_stop.json` - Subagent completion events
  - `chat.json` - Readable conversation transcript (generated by --chat flag)
- `ai_docs/cc_hooks_docs.md` - Complete hooks documentation from Anthropic

Hooks provide deterministic control over Claude Code behavior without relying on LLM decisions.

## Features Demonstrated

- Command logging and auditing
- Automatic transcript conversion  
- Permission-based tool access control
- Error handling in hook execution

Run any Claude Code command to see hooks in action via the `logs/` files.

## Hook Error Codes & Flow Control

Claude Code hooks provide powerful mechanisms to control execution flow and provide feedback through exit codes and structured JSON output.

### Exit Code Behavior

Hooks communicate status and control flow through exit codes:

| Exit Code | Behavior           | Description                                                                                  |
| --------- | ------------------ | -------------------------------------------------------------------------------------------- |
| **0**     | Success            | Hook executed successfully. `stdout` shown to user in transcript mode (Ctrl-R)               |
| **2**     | Blocking Error     | **Critical**: `stderr` is fed back to Claude automatically. See hook-specific behavior below |
| **Other** | Non-blocking Error | `stderr` shown to user, execution continues normally                                         |

### Hook-Specific Flow Control

Each hook type has different capabilities for blocking and controlling Claude Code's behavior:

#### PreToolUse Hook - **CAN BLOCK TOOL EXECUTION**
- **Primary Control Point**: Intercepts tool calls before they execute
- **Exit Code 2 Behavior**: Blocks the tool call entirely, shows error message to Claude
- **Use Cases**: Security validation, parameter checking, dangerous command prevention
- **Example**: Our `pre_tool_use.py` blocks `rm -rf` commands with exit code 2

```python
# Block dangerous commands
if is_dangerous_rm_command(command):
    print("BLOCKED: Dangerous rm command detected", file=sys.stderr)
    sys.exit(2)  # Blocks tool call, shows error to Claude
```

#### PostToolUse Hook - **CANNOT BLOCK (Tool Already Executed)**
- **Primary Control Point**: Provides feedback after tool completion
- **Exit Code 2 Behavior**: Shows error to Claude (tool already ran, cannot be undone)
- **Use Cases**: Validation of results, formatting, cleanup, logging
- **Limitation**: Cannot prevent tool execution since it fires after completion

#### Notification Hook - **CANNOT BLOCK**
- **Primary Control Point**: Handles Claude Code notifications
- **Exit Code 2 Behavior**: N/A - shows stderr to user only, no blocking capability
- **Use Cases**: Custom notifications, logging, user alerts
- **Limitation**: Cannot control Claude Code behavior, purely informational

#### Stop Hook - **CAN BLOCK STOPPING**
- **Primary Control Point**: Intercepts when Claude Code tries to finish responding
- **Exit Code 2 Behavior**: Blocks stoppage, shows error to Claude (forces continuation)
- **Use Cases**: Ensuring tasks complete, validation of final state use this to FORCE CONTINUATION
- **Caution**: Can cause infinite loops if not properly controlled

### Advanced JSON Output Control

Beyond simple exit codes, hooks can return structured JSON for sophisticated control:

#### Common JSON Fields (All Hook Types)
```json
{
  "continue": true,           // Whether Claude should continue (default: true)
  "stopReason": "string",     // Message when continue=false (shown to user)
  "suppressOutput": true      // Hide stdout from transcript (default: false)
}
```

#### PreToolUse Decision Control
```json
{
  "decision": "approve" | "block" | undefined,
  "reason": "Explanation for decision"
}
```

- **"approve"**: Bypasses permission system, `reason` shown to user
- **"block"**: Prevents tool execution, `reason` shown to Claude
- **undefined**: Normal permission flow, `reason` ignored

#### PostToolUse Decision Control
```json
{
  "decision": "block" | undefined,
  "reason": "Explanation for decision"
}
```

- **"block"**: Automatically prompts Claude with `reason`
- **undefined**: No action, `reason` ignored

#### Stop Decision Control
```json
{
  "decision": "block" | undefined,
  "reason": "Must be provided when blocking Claude from stopping"
}
```

- **"block"**: Prevents Claude from stopping, `reason` tells Claude how to proceed
- **undefined**: Allows normal stopping, `reason` ignored

### Flow Control Priority

When multiple control mechanisms are used, they follow this priority:

1. **`"continue": false`** - Takes precedence over all other controls
2. **`"decision": "block"`** - Hook-specific blocking behavior
3. **Exit Code 2** - Simple blocking via stderr
4. **Other Exit Codes** - Non-blocking errors

### Security Implementation Examples

#### 1. Command Validation (PreToolUse)
```python
# Block dangerous patterns
dangerous_patterns = [
    r'rm\s+.*-[rf]',           # rm -rf variants
    r'sudo\s+rm',              # sudo rm commands
    r'chmod\s+777',            # Dangerous permissions
    r'>\s*/etc/',              # Writing to system directories
]

for pattern in dangerous_patterns:
    if re.search(pattern, command, re.IGNORECASE):
        print(f"BLOCKED: {pattern} detected", file=sys.stderr)
        sys.exit(2)
```

#### 2. Result Validation (PostToolUse)
```python
# Validate file operations
if tool_name == "Write" and not tool_response.get("success"):
    output = {
        "decision": "block",
        "reason": "File write operation failed, please check permissions and retry"
    }
    print(json.dumps(output))
    sys.exit(0)
```

#### 3. Completion Validation (Stop Hook)
```python
# Ensure critical tasks are complete
if not all_tests_passed():
    output = {
        "decision": "block",
        "reason": "Tests are failing. Please fix failing tests before completing."
    }
    print(json.dumps(output))
    sys.exit(0)
```

### Hook Execution Environment

- **Timeout**: 60-second execution limit per hook
- **Parallelization**: All matching hooks run in parallel
- **Environment**: Inherits Claude Code's environment variables
- **Working Directory**: Runs in current project directory
- **Input**: JSON via stdin with session and tool data
- **Output**: Processed via stdout/stderr with exit codes

### Best Practices for Flow Control

1. **Use PreToolUse for Prevention**: Block dangerous operations before they execute
2. **Use PostToolUse for Validation**: Check results and provide feedback
3. **Use Stop for Completion**: Ensure tasks are properly finished
4. **Handle Errors Gracefully**: Always provide clear error messages
5. **Avoid Infinite Loops**: Check `stop_hook_active` flag in Stop hooks
6. **Test Thoroughly**: Verify hooks work correctly in safe environments

## Master AI Coding
> And prepare for Agentic Engineering

Learn to code with AI with foundational [Principles of AI Coding](https://agenticengineer.com/principled-ai-coding?y=cchookmast)

Follow the [IndyDevDan youtube channel](https://www.youtube.com/@indydevdan) for more AI coding tips and tricks.


================================================
FILE: CLAUDE.md
================================================
[Empty file]


================================================
FILE: .env.sample
================================================
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
ELEVENLABS_API_KEY=
ENGINEER_NAME=Dan
FIRECRAWL_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
OLLAMA_HOST=
OPENAI_API_KEY=


================================================
FILE: ai_docs/anthropic_quick_start.md
================================================
# Get started with Claude

In this example, we'll have Claude write a Python function that checks if a string is a palindrome.

## Prerequisites

You will need:

- An Anthropic [Console account](https://console.anthropic.com/)
- An [API key](https://console.anthropic.com/settings/keys)
- Python 3.7+ or TypeScript 4.5+

Anthropic provides [Python and TypeScript SDKs](https://docs.anthropic.com/en/api/client-sdks), although you can make direct HTTP requests to the API.

## Start with the Workbench

Any API call you make—regardless of the specific task—sends a well-configured prompt to the Anthropic API. As you're learning to make the most of Claude, we recommend that you start the development process in the Workbench, a web-based interface to Claude.

Log into the [Anthropic Console](https://console.anthropic.com/) and click **Write a prompt from scratch**.

In the middle section, under User, let's ask Claude a question.

User

```text
Why is the ocean salty?
```

Click **Run**. On the right side, you'll see output like

Response

```text
The ocean is salty due to several factors:

1. Weathering of rocks: Over millions of years, rain, rivers, and streams have eroded rocks containing mineral salts. These salts are carried into the ocean by water runoff.
2. Volcanic activity: Underwater volcanoes and hydrothermal vents release minerals, including salts, into the ocean water.
3. Atmospheric deposition: Salt particles from ocean spray can be carried by wind and deposited back into the ocean.
4. Evaporation: As water evaporates from the surface of the ocean, it leaves behind dissolved salts, increasing the concentration of salt in the remaining water.
5. Biological processes: Some marine organisms contribute to the ocean's salinity by releasing salt compounds as byproducts of their metabolism.

Over time, these processes have continuously added salts to the ocean, while evaporation removes pure water, leading to the ocean's current salinity levels. It's important to note that the total amount of salt in the ocean remains relatively stable because the input of salts is balanced by the removal of salts through processes like the formation of evaporite deposits.
```

This is a good answer, but let's say we wanted to control the exact type of answer Claude gives. For example, only allowing Claude to respond to questions with poems. We can control the format, tone, and personality of the response by adding a System Prompt.

System prompt

```text
You are a world-class poet. Respond only with short poems.
```

Click **Run** again.

Response

```text
The ocean's salty brine,
A tale of time and elements combined.
Rocks and rain, a slow erosion,
Minerals carried in solution.
Eons pass, the salt remains,
In the vast, eternal watery domain.
```

See how Claude's response has changed? LLMs respond well to clear and direct instructions. You can put the role instructions in either the system prompt or the user message. We recommend testing to see which way yields the best results for your use case.

Once you've tweaked the inputs such that you're pleased with the output and have a good sense how to use Claude, convert your Workbench into an integration.

Click **Get Code** to copy the generated code representing your Workbench session.

## Install the SDK

Anthropic provides SDKs for [Python](https://pypi.org/project/anthropic/) (3.7+), [TypeScript](https://www.npmjs.com/package/@anthropic-ai/sdk) (4.5+), and [Java](https://central.sonatype.com/artifact/com.anthropic/anthropic-java/) (8+). We also currently have a [Go](https://pkg.go.dev/github.com/anthropics/anthropic-sdk-go) SDK in beta.

### Python

In your project directory, create a virtual environment.

```bash
python -m venv claude-env
```

Activate the virtual environment using

- On macOS or Linux, `source claude-env/bin/activate`
- On Windows, `claude-env\Scripts\activate`

```bash
pip install anthropic
```

### TypeScript

Install the SDK.

```bash
npm install @anthropic-ai/sdk
```

### Java

First find the current version of the Java SDK on [Maven Central](https://central.sonatype.com/artifact/com.anthropic/anthropic-java).
Declare the SDK as a dependency in your Gradle file:

```gradle
implementation("com.anthropic:anthropic-java:1.0.0")
```

Or in your Maven file:

```xml
<dependency>
  <groupId>com.anthropic</groupId>
  <artifactId>anthropic-java</artifactId>
  <version>1.0.0</version>
</dependency>
```

## Set your API key

Every API call requires a valid API key. The SDKs are designed to pull the API key from an environmental variable `ANTHROPIC_API_KEY`. You can also supply the key to the Anthropic client when initializing it.

### macOS and Linux

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Call the API

Call the API by passing the proper parameters to the [/messages](https://docs.anthropic.com/en/api/messages) endpoint.

Note that the code provided by the Workbench sets the API key in the constructor. If you set the API key as an environment variable, you can omit that line as below.

### Python

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=1000,
    temperature=1,
    system="You are a world-class poet. Respond only with short poems.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Why is the ocean salty?"
                }
            ]
        }
    ]
)
print(message.content)
```

Run the code using `python3 claude_quickstart.py` or `node claude_quickstart.js`.

Output (Python)

```python
[TextBlock(text="The ocean's salty brine,\nA tale of time and design.\nRocks and rivers, their minerals shed,\nAccumulating in the ocean's bed.\nEvaporation leaves salt behind,\nIn the vast waters, forever enshrined.", type='text')]
```

The Workbench and code examples use default model settings for: model (name), temperature, and max tokens to sample.

This quickstart shows how to develop a basic, but functional, Claude-powered application using the Console, Workbench, and API. You can use this same workflow as the foundation for much more powerful use cases.

## Next steps

Now that you have made your first Anthropic API request, it's time to explore what else is possible:

- **Use Case Guides** - End to end implementation guides for common use cases.
- **Anthropic Cookbook** - Learn with interactive Jupyter notebooks that demonstrate uploading PDFs, embeddings, and more.
- **Prompt Library** - Explore dozens of example prompts for inspiration across use cases.


================================================
FILE: ai_docs/cc_hooks_docs.md
================================================
# Hooks

> Customize and extend Claude Code's behavior by registering shell commands

# Introduction

Claude Code hooks are user-defined shell commands that execute at various points
in Claude Code's lifecycle. Hooks provide deterministic control over Claude
Code's behavior, ensuring certain actions always happen rather than relying on
the LLM to choose to run them.

Example use cases include:

* **Notifications**: Customize how you get notified when Claude Code is awaiting
  your input or permission to run something.
* **Automatic formatting**: Run `prettier` on .ts files, `gofmt` on .go files,
  etc. after every file edit.
* **Logging**: Track and count all executed commands for compliance or
  debugging.
* **Feedback**: Provide automated feedback when Claude Code produces code that
  does not follow your codebase conventions.
* **Custom permissions**: Block modifications to production files or sensitive
  directories.

By encoding these rules as hooks rather than prompting instructions, you turn
suggestions into app-level code that executes every time it is expected to run.

<Warning>
  Hooks execute shell commands with your full user permissions without
  confirmation. You are responsible for ensuring your hooks are safe and secure.
  Anthropic is not liable for any data loss or system damage resulting from hook
  usage. Review [Security Considerations](#security-considerations).
</Warning>

## Quickstart

In this quickstart, you'll add a hook that logs the shell commands that Claude
Code runs.

Quickstart Prerequisite: Install `jq` for JSON processing in the command line.

### Step 1: Open hooks configuration

Run the `/hooks` [slash command](/en/docs/claude-code/slash-commands) and select
the `PreToolUse` hook event.

`PreToolUse` hooks run before tool calls and can block them while providing
Claude feedback on what to do differently.

### Step 2: Add a matcher

Select `+ Add new matcher…` to run your hook only on Bash tool calls.

Type `Bash` for the matcher.

### Step 3: Add the hook

Select `+ Add new hook…` and enter this command:

```bash
jq -r '"\(.tool_input.command) - \(.tool_input.description // "No description")"' >> ~/.claude/bash-command-log.txt
```

### Step 4: Save your configuration

For storage location, select `User settings` since you're logging to your home
directory. This hook will then apply to all projects, not just your current
project.

Then press Esc until you return to the REPL. Your hook is now registered!

### Step 5: Verify your hook

Run `/hooks` again or check `~/.claude/settings.json` to see your configuration:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "jq -r '\"\\(.tool_input.command) - \\(.tool_input.description // \"No description\")\"' >> ~/.claude/bash-command-log.txt"
        }
      ]
    }
  ]
}
```

## Configuration

Claude Code hooks are configured in your
[settings files](/en/docs/claude-code/settings):

* `~/.claude/settings.json` - User settings
* `.claude/settings.json` - Project settings
* `.claude/settings.local.json` - Local project settings (not committed)
* Enterprise managed policy settings

### Structure

Hooks are organized by matchers, where each matcher can have multiple hooks:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

* **matcher**: Pattern to match tool names (only applicable for `PreToolUse` and
  `PostToolUse`)
  * Simple strings match exactly: `Write` matches only the Write tool
  * Supports regex: `Edit|Write` or `Notebook.*`
  * If omitted or empty string, hooks run for all matching events
* **hooks**: Array of commands to execute when the pattern matches
  * `type`: Currently only `"command"` is supported
  * `command`: The bash command to execute
  * `timeout`: (Optional) How long a command should run, in seconds, before
    canceling all in-progress hooks.

## Hook Events

### PreToolUse

Runs after Claude creates tool parameters and before processing the tool call.

**Common matchers:**

* `Task` - Agent tasks
* `Bash` - Shell commands
* `Glob` - File pattern matching
* `Grep` - Content search
* `Read` - File reading
* `Edit`, `MultiEdit` - File editing
* `Write` - File writing
* `WebFetch`, `WebSearch` - Web operations

### PostToolUse

Runs immediately after a tool completes successfully.

Recognizes the same matcher values as PreToolUse.

### Notification

Runs when Claude Code sends notifications.

### Stop

Runs when the main Claude Code agent has finished responding.

### SubagentStop

Runs when a Claude Code subagent (Task tool call) has finished responding.

## Hook Input

Hooks receive JSON data via stdin containing session information and
event-specific data:

```typescript
{
  // Common fields
  session_id: string
  transcript_path: string  // Path to conversation JSON

  // Event-specific fields
  ...
}
```

### PreToolUse Input

The exact schema for `tool_input` depends on the tool.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  }
}
```

### PostToolUse Input

The exact schema for `tool_input` and `tool_response` depends on the tool.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  }
}
```

### Notification Input

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "message": "Task completed successfully",
  "title": "Claude Code"
}
```

### Stop and SubagentStop Input

`stop_hook_active` is true when Claude Code is already continuing as a result of
a stop hook. Check this value or process the transcript to prevent Claude Code
from running indefinitely.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "stop_hook_active": true
}
```

## Hook Output

There are two ways for hooks to return output back to Claude Code. The output
communicates whether to block and any feedback that should be shown to Claude
and the user.

### Simple: Exit Code

Hooks communicate status through exit codes, stdout, and stderr:

* **Exit code 0**: Success. `stdout` is shown to the user in transcript mode
  (CTRL-R).
* **Exit code 2**: Blocking error. `stderr` is fed back to Claude to process
  automatically. See per-hook-event behavior below.
* **Other exit codes**: Non-blocking error. `stderr` is shown to the user and
  execution continues.

<Warning>
  Reminder: Claude Code does not see stdout if the exit code is 0.
</Warning>

#### Exit Code 2 Behavior

| Hook Event     | Behavior                                        |
| -------------- | ----------------------------------------------- |
| `PreToolUse`   | Blocks the tool call, shows error to Claude     |
| `PostToolUse`  | Shows error to Claude (tool already ran)        |
| `Notification` | N/A, shows stderr to user only                  |
| `Stop`         | Blocks stoppage, shows error to Claude          |
| `SubagentStop` | Blocks stoppage, shows error to Claude subagent |

### Advanced: JSON Output

Hooks can return structured JSON in `stdout` for more sophisticated control:

#### Common JSON Fields

All hook types can include these optional fields:

```json
{
  "continue": true, // Whether Claude should continue after hook execution (default: true)
  "stopReason": "string" // Message shown when continue is false
  "suppressOutput": true, // Hide stdout from transcript mode (default: false)
}
```

If `continue` is false, Claude stops processing after the hooks run.

* For `PreToolUse`, this is different from `"decision": "block"`, which only
  blocks a specific tool call and provides automatic feedback to Claude.
* For `PostToolUse`, this is different from `"decision": "block"`, which
  provides automated feedback to Claude.
* For `Stop` and `SubagentStop`, this takes precedence over any
  `"decision": "block"` output.
* In all cases, `"continue" = false` takes precedence over any
  `"decision": "block"` output.

`stopReason` accompanies `continue` with a reason shown to the user, not shown
to Claude.

#### `PreToolUse` Decision Control

`PreToolUse` hooks can control whether a tool call proceeds.

* "approve" bypasses the permission system. `reason` is shown to the user but
  not to Claude.
* "block" prevents the tool call from executing. `reason` is shown to Claude.
* `undefined` leads to the existing permission flow. `reason` is ignored.

```json
{
  "decision": "approve" | "block" | undefined,
  "reason": "Explanation for decision"
}
```

#### `PostToolUse` Decision Control

`PostToolUse` hooks can control whether a tool call proceeds.

* "block" automatically prompts Claude with `reason`.
* `undefined` does nothing. `reason` is ignored.

```json
{
  "decision": "block" | undefined,
  "reason": "Explanation for decision"
}
```

#### `Stop`/`SubagentStop` Decision Control

`Stop` and `SubagentStop` hooks can control whether Claude must continue.

* "block" prevents Claude from stopping. You must populate `reason` for Claude
  to know how to proceed.
* `undefined` allows Claude to stop. `reason` is ignored.

```json
{
  "decision": "block" | undefined,
  "reason": "Must be provided when Claude is blocked from stopping"
}
```

#### JSON Output Example: Bash Command Editing

```python
#!/usr/bin/env python3
import json
import re
import sys

# Define validation rules as a list of (regex pattern, message) tuples
VALIDATION_RULES = [
    (
        r"\bgrep\b(?!.*\|)",
        "Use 'rg' (ripgrep) instead of 'grep' for better performance and features",
    ),
    (
        r"\bfind\s+\S+\s+-name\b",
        "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance",
    ),
]


def validate_command(command: str) -> list[str]:
    issues = []
    for pattern, message in VALIDATION_RULES:
        if re.search(pattern, command):
            issues.append(message)
    return issues


try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")

if tool_name != "Bash" or not command:
    sys.exit(1)

# Validate the command
issues = validate_command(command)

if issues:
    for message in issues:
        print(f"• {message}", file=sys.stderr)
    # Exit code 2 blocks tool call and shows stderr to Claude
    sys.exit(2)
```

## Working with MCP Tools

Claude Code hooks work seamlessly with
[Model Context Protocol (MCP) tools](/en/docs/claude-code/mcp). When MCP servers
provide tools, they appear with a special naming pattern that you can match in
your hooks.

### MCP Tool Naming

MCP tools follow the pattern `mcp__<server>__<tool>`, for example:

* `mcp__memory__create_entities` - Memory server's create entities tool
* `mcp__filesystem__read_file` - Filesystem server's read file tool
* `mcp__github__search_repositories` - GitHub server's search tool

### Configuring Hooks for MCP Tools

You can target specific MCP tools or entire MCP servers:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Memory operation initiated' >> ~/mcp-operations.log"
          }
        ]
      },
      {
        "matcher": "mcp__.*__write.*",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/scripts/validate-mcp-write.py"
          }
        ]
      }
    ]
  }
}
```

## Examples

### Code Formatting

Automatically format code after file modifications:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/scripts/format-code.sh"
          }
        ]
      }
    ]
  }
}
```

### Notification

Customize the notification that is sent when Claude Code requests permission or
when the prompt input has become idle.

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/my_custom_notifier.py"
          }
        ]
      }
    ]
  }
}
```

## Security Considerations

### Disclaimer

**USE AT YOUR OWN RISK**: Claude Code hooks execute arbitrary shell commands on
your system automatically. By using hooks, you acknowledge that:

* You are solely responsible for the commands you configure
* Hooks can modify, delete, or access any files your user account can access
* Malicious or poorly written hooks can cause data loss or system damage
* Anthropic provides no warranty and assumes no liability for any damages
  resulting from hook usage
* You should thoroughly test hooks in a safe environment before production use

Always review and understand any hook commands before adding them to your
configuration.

### Security Best Practices

Here are some key practices for writing more secure hooks:

1. **Validate and sanitize inputs** - Never trust input data blindly
2. **Always quote shell variables** - Use `"$VAR"` not `$VAR`
3. **Block path traversal** - Check for `..` in file paths
4. **Use absolute paths** - Specify full paths for scripts
5. **Skip sensitive files** - Avoid `.env`, `.git/`, keys, etc.

### Configuration Safety

Direct edits to hooks in settings files don't take effect immediately. Claude
Code:

1. Captures a snapshot of hooks at startup
2. Uses this snapshot throughout the session
3. Warns if hooks are modified externally
4. Requires review in `/hooks` menu for changes to apply

This prevents malicious hook modifications from affecting your current session.

## Hook Execution Details

* **Timeout**: 60-second execution limit by default, configurable per command.
  * If any individual command times out, all in-progress hooks are cancelled.
* **Parallelization**: All matching hooks run in parallel
* **Environment**: Runs in current directory with Claude Code's environment
* **Input**: JSON via stdin
* **Output**:
  * PreToolUse/PostToolUse/Stop: Progress shown in transcript (Ctrl-R)
  * Notification: Logged to debug only (`--debug`)

## Debugging

To troubleshoot hooks:

1. Check if `/hooks` menu displays your configuration
2. Verify that your [settings files](/en/docs/claude-code/settings) are valid
   JSON
3. Test commands manually
4. Check exit codes
5. Review stdout and stderr format expectations
6. Ensure proper quote escaping
7. Use `claude --debug` to debug your hooks. The output of a successful hook
   appears like below.

```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Getting matching hook commands for PostToolUse with query: Write
[DEBUG] Found 1 hook matchers in settings
[DEBUG] Matched 1 hooks for query "Write"
[DEBUG] Found 1 hook commands to execute
[DEBUG] Executing hook command: <Your command> with timeout 60000ms
[DEBUG] Hook command completed with status 0: <Your stdout>
```

Progress messages appear in transcript mode (Ctrl-R) showing:

* Which hook is running
* Command being executed
* Success/failure status
* Output or error messages



================================================
FILE: ai_docs/cc_hooks_v0_repomix.xml
================================================
This file is a merged representation of the entire codebase, combined into a single document by Repomix.

<file_summary>
This section contains a summary of this file.

<purpose>
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.
</purpose>

<file_format>
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files, each consisting of:
  - File path as an attribute
  - Full contents of the file
</file_format>

<usage_guidelines>
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.
</usage_guidelines>

<notes>
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)
</notes>

<additional_info>

</additional_info>

</file_summary>

<directory_structure>
.claude/
  settings.json
  settings.local.json
ai_docs/
  cc_hooks.md
  hook_data_reference.md
examples/
  comprehensive-logging.json
  developer-workflow.json
  minimal-logging.json
  security-focused.json
scripts/
  custom_notifier.py
  format_code.sh
  log_full_data.py
  log_tool_use.py
  session_summary.py
  track_file_changes.py
  validate_bash_command.py
.gitignore
CLAUDE.md
README.md
</directory_structure>

<files>
This section contains the contents of the repository's files.

<file path=".claude/settings.local.json">
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/log_full_data.py pre"
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/log_tool_use.py pre"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/validate_bash_command.py"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/track_file_changes.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/log_full_data.py post"
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/log_tool_use.py post"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/format_code.sh"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/log_full_data.py notification"
          },
          {
            "type": "command",
            "command": "python3 scripts/custom_notifier.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/log_full_data.py stop"
          },
          {
            "type": "command",
            "command": "python3 scripts/session_summary.py"
          }
        ]
      }
    ]
  }
}
</file>

<file path="ai_docs/cc_hooks.md">
# Claude Code Hooks Documentation

## Introduction

Claude Code hooks are user-defined shell commands that execute at various points in Claude Code's lifecycle. Hooks provide deterministic control over Claude Code's behavior, ensuring certain actions always happen rather than relying on the LLM to choose to run them.

Example use cases include:

- **Notifications**: Customize how you get notified when Claude Code is awaiting your input or permission to run something.
- **Automatic formatting**: Run `prettier` on .ts files, `gofmt` on .go files, etc. after every file edit.
- **Logging**: Track and count all executed commands for compliance or debugging.
- **Feedback**: Provide automated feedback when Claude Code produces code that does not follow your codebase conventions.
- **Custom permissions**: Block modifications to production files or sensitive directories.

By encoding these rules as hooks rather than prompting instructions, you turn suggestions into app-level code that executes every time it is expected to run.

> **⚠️ WARNING**: Hooks execute shell commands with your full user permissions without confirmation. You are responsible for ensuring your hooks are safe and secure. Anthropic is not liable for any data loss or system damage resulting from hook usage. Review Security Considerations.

## Quickstart

In this quickstart, you'll add a hook that logs the shell commands that Claude Code runs.

**Quickstart Prerequisite**: Install `jq` for JSON processing in the command line.

### Step 1: Open hooks configuration

Run the `/hooks` slash command and select the `PreToolUse` hook event.

`PreToolUse` hooks run before tool calls and can block them while providing Claude feedback on what to do differently.

### Step 2: Add a matcher

Select `+ Add new matcher…` to run your hook only on Bash tool calls.

Type `Bash` for the matcher.

### Step 3: Add the hook

Select `+ Add new hook…` and enter this command:

```bash
jq -r '"\(.tool_input.command) - \(.tool_input.description // "No description")"' >> ~/.claude/bash-command-log.txt
```

### Step 4: Save your configuration

For storage location, select `User settings` since you're logging to your home directory. This hook will then apply to all projects, not just your current project.

Then press Esc until you return to the REPL. Your hook is now registered!

### Step 5: Verify your hook

Run `/hooks` again or check `~/.claude/settings.json` to see your configuration:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "jq -r '\"\\(.tool_input.command) - \\(.tool_input.description // \"No description\")\"' >> ~/.claude/bash-command-log.txt"
        }
      ]
    }
  ]
}
```

## Configuration

Claude Code hooks are configured in your settings files:

- `~/.claude/settings.json` - User settings
- `.claude/settings.json` - Project settings
- `.claude/settings.local.json` - Local project settings (not committed)
- Enterprise managed policy settings

### Structure

Hooks are organized by matchers, where each matcher can have multiple hooks:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

- **matcher**: Pattern to match tool names (only applicable for `PreToolUse` and `PostToolUse`)
  - Simple strings match exactly: `Write` matches only the Write tool
  - Supports regex: `Edit|Write` or `Notebook.*`
  - If omitted or empty string, hooks run for all matching events
- **hooks**: Array of commands to execute when the pattern matches
  - `type`: Currently only `"command"` is supported
  - `command`: The bash command to execute

## Hook Events

### PreToolUse

Runs after Claude creates tool parameters and before processing the tool call.

**Common matchers:**
- `Task` - Agent tasks
- `Bash` - Shell commands
- `Glob` - File pattern matching
- `Grep` - Content search
- `Read` - File reading
- `Edit`, `MultiEdit` - File editing
- `Write` - File writing
- `WebFetch`, `WebSearch` - Web operations

### PostToolUse

Runs immediately after a tool completes successfully.

Recognizes the same matcher values as PreToolUse.

### Notification

Runs when Claude Code sends notifications.

### Stop

Runs when Claude Code has finished responding.

## Hook Input

Hooks receive JSON data via stdin containing session information and event-specific data:

```typescript
{
  // Common fields
  session_id: string
  transcript_path: string  // Path to conversation JSON

  // Event-specific fields
  ...
}
```

### PreToolUse Input

The exact schema for `tool_input` depends on the tool.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  }
}
```

### PostToolUse Input

The exact schema for `tool_input` and `tool_response` depends on the tool.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  }
}
```

### Notification Input

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "message": "Task completed successfully",
  "title": "Claude Code"
}
```

### Stop Input

`stop_hook_active` is true when Claude Code is already continuing as a result of a stop hook. Check this value or process the transcript to prevent Claude Code from running indefinitely.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "stop_hook_active": true
}
```

## Hook Output

There are two ways for hooks to return output back to Claude Code. The output communicates whether to block and any feedback that should be shown to Claude and the user.

### Simple: Exit Code

Hooks communicate status through exit codes, stdout, and stderr:

- **Exit code 0**: Success. `stdout` is shown to the user in transcript mode (CTRL-R).
- **Exit code 2**: Blocking error. `stderr` is fed back to Claude to process automatically. See per-hook-event behavior below.
- **Other exit codes**: Non-blocking error. `stderr` is shown to the user and execution continues.

#### Exit Code 2 Behavior

| Hook Event | Behavior |
|------------|----------|
| `PreToolUse` | Blocks the tool call, shows error to Claude |
| `PostToolUse` | Shows error to Claude (tool already ran) |
| `Notification` | N/A, shows stderr to user only |
| `Stop` | Blocks stoppage, shows error to Claude |

### Advanced: JSON Output

Hooks can return structured JSON in `stdout` for more sophisticated control:

#### Common JSON Fields

All hook types can include these optional fields:

```json
{
  "continue": true, // Whether Claude should continue after hook execution (default: true)
  "stopReason": "string" // Message shown when continue is false
  "suppressOutput": true, // Hide stdout from transcript mode (default: false)
}
```

If `continue` is false, Claude stops processing after the hooks run.

- For `PreToolUse`, this is different from `"decision": "block"`, which only blocks a specific tool call and provides automatic feedback to Claude.
- For `PostToolUse`, this is different from `"decision": "block"`, which provides automated feedback to Claude.
- For `Stop`, this takes precedence over any `"decision": "block"` output.
- In all cases, `"continue" = false` takes precedence over any `"decision": "block"` output.

`stopReason` accompanies `continue` with a reason shown to the user, not shown to Claude.

#### PreToolUse Decision Control

`PreToolUse` hooks can control whether a tool call proceeds.

- "approve" bypasses the permission system. `reason` is shown to the user but not to Claude.
- "block" prevents the tool call from executing. `reason` is shown to Claude.
- `undefined` leads to the existing permission flow. `reason` is ignored.

```json
{
  "decision": "approve" | "block" | undefined,
  "reason": "Explanation for decision"
}
```

#### PostToolUse Decision Control

`PostToolUse` hooks can control whether a tool call proceeds.

- "block" automatically prompts Claude with `reason`.
- `undefined` does nothing. `reason` is ignored.

```json
{
  "decision": "block" | undefined,
  "reason": "Explanation for decision"
}
```

#### Stop Decision Control

`Stop` hooks can control whether Claude must continue.

- "block" prevents Claude from stopping. You must populate `reason` for Claude to know how to proceed.
- `undefined` allows Claude to stop. `reason` is ignored.

```json
{
  "decision": "block" | undefined,
  "reason": "Must be provided when Claude is blocked from stopping"
}
```

#### JSON Output Example: Bash Command Editing

```python
#!/usr/bin/env python3
import json
import re
import sys

# Define validation rules as a list of (regex pattern, message) tuples
VALIDATION_RULES = [
    (
        r"\bgrep\b(?!.*\|)",
        "Use 'rg' (ripgrep) instead of 'grep' for better performance and features",
    ),
    (
        r"\bfind\s+\S+\s+-name\b",
        "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance",
    ),
]

def validate_command(command: str) -> list[str]:
    issues = []
    for pattern, message in VALIDATION_RULES:
        if re.search(pattern, command):
            issues.append(message)
    return issues

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")

if tool_name != "Bash" or not command:
    sys.exit(1)

# Validate the command
issues = validate_command(command)

if issues:
    for message in issues:
        print(f"• {message}", file=sys.stderr)
    # Exit code 2 blocks tool call and shows stderr to Claude
    sys.exit(2)
```

## Working with MCP Tools

Claude Code hooks work seamlessly with Model Context Protocol (MCP) tools. When MCP servers provide tools, they appear with a special naming pattern that you can match in your hooks.

### MCP Tool Naming

MCP tools follow the pattern `mcp__<server>__<tool>`, for example:

- `mcp__memory__create_entities` - Memory server's create entities tool
- `mcp__filesystem__read_file` - Filesystem server's read file tool
- `mcp__github__search_repositories` - GitHub server's search tool

### Configuring Hooks for MCP Tools

You can target specific MCP tools or entire MCP servers:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Memory operation initiated' >> ~/mcp-operations.log"
          }
        ]
      },
      {
        "matcher": "mcp__.*__write.*",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/scripts/validate-mcp-write.py"
          }
        ]
      }
    ]
  }
}
```

## Examples

### Code Formatting

Automatically format code after file modifications:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/scripts/format-code.sh"
          }
        ]
      }
    ]
  }
}
```

### Notification

Customize the notification that is sent when Claude Code requests permission or when the prompt input has become idle.

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/my_custom_notifier.py"
          }
        ]
      }
    ]
  }
}
```

## Security Considerations

### Disclaimer

**USE AT YOUR OWN RISK**: Claude Code hooks execute arbitrary shell commands on your system automatically. By using hooks, you acknowledge that:

- You are solely responsible for the commands you configure
- Hooks can modify, delete, or access any files your user account can access
- Malicious or poorly written hooks can cause data loss or system damage
- Anthropic provides no warranty and assumes no liability for any damages resulting from hook usage
- You should thoroughly test hooks in a safe environment before production use

Always review and understand any hook commands before adding them to your configuration.

### Security Best Practices

Here are some key practices for writing more secure hooks:

1. **Validate and sanitize inputs** - Never trust input data blindly
2. **Always quote shell variables** - Use `"$VAR"` not `$VAR`
3. **Block path traversal** - Check for `..` in file paths
4. **Use absolute paths** - Specify full paths for scripts
5. **Skip sensitive files** - Avoid `.env`, `.git/`, keys, etc.

### Configuration Safety

Direct edits to hooks in settings files don't take effect immediately. Claude Code:

1. Captures a snapshot of hooks at startup
2. Uses this snapshot throughout the session
3. Warns if hooks are modified externally
4. Requires review in `/hooks` menu for changes to apply

This prevents malicious hook modifications from affecting your current session.

## Hook Execution Details

- **Timeout**: 60-second execution limit
- **Parallelization**: All matching hooks run in parallel
- **Environment**: Runs in current directory with Claude Code's environment
- **Input**: JSON via stdin
- **Output**:
  - PreToolUse/PostToolUse/Stop: Progress shown in transcript (Ctrl-R)
  - Notification: Logged to debug only (`--debug`)

## Debugging

To troubleshoot hooks:

1. Check if `/hooks` menu displays your configuration
2. Verify that your settings files are valid JSON
3. Test commands manually
4. Check exit codes
5. Review stdout and stderr format expectations
6. Ensure proper quote escaping

Progress messages appear in transcript mode (Ctrl-R) showing:

- Which hook is running
- Command being executed
- Success/failure status
- Output or error messages
</file>

<file path="ai_docs/hook_data_reference.md">
# Claude Code Hook Data Reference

## Overview

Claude Code passes JSON data to hooks via stdin. The data structure varies by hook type and tool being used. **PostToolUse** hooks have the most complete data as they include both input and response.

## Hook Data Availability

| Hook Type | Data Available | Best For |
|-----------|---------------|----------|
| **PreToolUse** | tool_name, tool_input, session_id, transcript_path | Validation, blocking, pre-processing |
| **PostToolUse** | All PreToolUse data + tool_response | Logging, analysis, post-processing |
| **Notification** | message, title, session_id, transcript_path | Custom notifications |
| **Stop** | session_id, transcript_path, stop_hook_active | Session cleanup, summaries |

## Common Fields (All Hooks)

```json
{
  "session_id": "string",          // Unique session identifier
  "transcript_path": "string"      // Path to conversation JSON file
}
```

## PreToolUse Data Structure

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "tool_name": "ToolName",
  "tool_input": {
    // Tool-specific fields (see below)
  }
}
```

## PostToolUse Data Structure

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "tool_name": "ToolName",
  "tool_input": {
    // Same as PreToolUse
  },
  "tool_response": {
    // Tool-specific response fields (see below)
  }
}
```

## Tool-Specific Data Structures

### Bash Tool

**tool_input:**
```json
{
  "command": "string",        // The bash command to execute
  "description": "string",    // Description of what the command does
  "timeout": "number"         // Optional timeout in milliseconds
}
```

**tool_response:**
```json
{
  "stdout": "string",         // Command output
  "stderr": "string",         // Error output
  "exit_code": "number",      // Exit code (0 = success)
  "timed_out": "boolean"      // Whether command timed out
}
```

### Read Tool

**tool_input:**
```json
{
  "file_path": "string",      // Absolute path to file
  "limit": "number",          // Optional line limit
  "offset": "number"          // Optional line offset
}
```

**tool_response:**
```json
{
  "content": "string",        // File content
  "lines_read": "number",     // Number of lines read
  "total_lines": "number",    // Total lines in file
  "truncated": "boolean"      // Whether content was truncated
}
```

### Write Tool

**tool_input:**
```json
{
  "file_path": "string",      // Absolute path to file
  "content": "string"         // Content to write
}
```

**tool_response:**
```json
{
  "success": "boolean",       // Whether write succeeded
  "file_path": "string",      // Path to written file
  "bytes_written": "number"   // Number of bytes written
}
```

### Edit Tool

**tool_input:**
```json
{
  "file_path": "string",      // Absolute path to file
  "old_string": "string",     // Text to replace
  "new_string": "string",     // Replacement text
  "replace_all": "boolean"    // Replace all occurrences
}
```

**tool_response:**
```json
{
  "success": "boolean",       // Whether edit succeeded
  "replacements": "number",   // Number of replacements made
  "file_path": "string"       // Path to edited file
}
```

### MultiEdit Tool

**tool_input:**
```json
{
  "file_path": "string",      // Absolute path to file
  "edits": [                  // Array of edit operations
    {
      "old_string": "string",
      "new_string": "string",
      "replace_all": "boolean"
    }
  ]
}
```

**tool_response:**
```json
{
  "success": "boolean",       // Whether all edits succeeded
  "edits_applied": "number",  // Number of edits applied
  "file_path": "string"       // Path to edited file
}
```

### Glob Tool

**tool_input:**
```json
{
  "pattern": "string",        // Glob pattern (e.g., "**/*.js")
  "path": "string"            // Optional directory path
}
```

**tool_response:**
```json
{
  "matches": ["string"],      // Array of matching file paths
  "match_count": "number"     // Number of matches found
}
```

### Grep Tool

**tool_input:**
```json
{
  "pattern": "string",        // Regular expression pattern
  "path": "string",           // Directory to search
  "include": "string"         // File pattern to include
}
```

**tool_response:**
```json
{
  "matches": [                // Array of matches
    {
      "file": "string",
      "line": "number",
      "content": "string"
    }
  ],
  "file_count": "number",     // Number of files with matches
  "match_count": "number"     // Total number of matches
}
```

### Task Tool

**tool_input:**
```json
{
  "description": "string",    // Task description
  "prompt": "string"          // Detailed task prompt
}
```

**tool_response:**
```json
{
  "task_id": "string",        // Unique task identifier
  "status": "string",         // Task status
  "result": "string"          // Task result/output
}
```

### TodoWrite Tool

**tool_input:**
```json
{
  "todos": [                  // Array of todo items
    {
      "id": "string",
      "content": "string",
      "status": "string",     // "pending", "in_progress", "completed"
      "priority": "string"    // "high", "medium", "low"
    }
  ]
}
```

**tool_response:**
```json
{
  "success": "boolean",       // Whether update succeeded
  "todo_count": "number"      // Number of todos in list
}
```

### WebFetch Tool

**tool_input:**
```json
{
  "url": "string",            // URL to fetch
  "prompt": "string"          // Prompt for content analysis
}
```

**tool_response:**
```json
{
  "content": "string",        // Fetched/analyzed content
  "url": "string",            // Actual URL fetched
  "status_code": "number"     // HTTP status code
}
```

### WebSearch Tool

**tool_input:**
```json
{
  "query": "string",          // Search query
  "allowed_domains": ["string"], // Optional domain filter
  "blocked_domains": ["string"]  // Optional domain blocklist
}
```

**tool_response:**
```json
{
  "results": [                // Array of search results
    {
      "title": "string",
      "url": "string",
      "snippet": "string"
    }
  ],
  "result_count": "number"    // Number of results
}
```

### NotebookRead Tool

**tool_input:**
```json
{
  "notebook_path": "string",  // Path to .ipynb file
  "cell_id": "string"         // Optional specific cell ID
}
```

**tool_response:**
```json
{
  "cells": [                  // Array of notebook cells
    {
      "id": "string",
      "type": "string",       // "code" or "markdown"
      "source": "string",
      "outputs": []           // Cell outputs
    }
  ],
  "cell_count": "number"      // Number of cells
}
```

### NotebookEdit Tool

**tool_input:**
```json
{
  "notebook_path": "string",  // Path to .ipynb file
  "cell_id": "string",        // Cell to edit
  "new_source": "string",     // New cell content
  "cell_type": "string",      // "code" or "markdown"
  "edit_mode": "string"       // "replace", "insert", "delete"
}
```

**tool_response:**
```json
{
  "success": "boolean",       // Whether edit succeeded
  "cell_id": "string",        // ID of edited cell
  "notebook_path": "string"   // Path to notebook
}
```

### MCP Tool Pattern

MCP tools follow the naming pattern `mcp__<server>__<tool>`. Their data structures vary by the specific MCP server and tool.

**Example tool_input:**
```json
{
  // Varies by MCP tool
  "custom_field": "value"
}
```

**Example tool_response:**
```json
{
  // Varies by MCP tool
  "result": "value"
}
```

## Notification Hook Data

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "message": "string",        // Notification message
  "title": "string"           // Notification title (usually "Claude Code")
}
```

## Stop Hook Data

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "stop_hook_active": "boolean"  // true if already in stop hook (prevent loops)
}
```

## Important Notes

1. **Data Availability**: PostToolUse hooks have the most complete data (input + response)
2. **Field Variability**: Not all fields are always present; use defensive coding
3. **MCP Tools**: Data structures vary significantly for MCP tools
4. **Error States**: tool_response may contain error information instead of success data
5. **Async Operations**: Some tools may have incomplete responses in PostToolUse

## Debugging Tips

To see actual data structures:
1. Use the `log_full_data.py` script to capture all hook data
2. Check `logs/tool-data-structures.jsonl` for raw data
3. Review `logs/tool-data-*.json` for pretty-printed examples
4. Use `jq` to explore the JSON structure interactively

## Example: Exploring Hook Data

```bash
# See all tool names used
cat logs/tool-data-structures.jsonl | jq -r '.parsed_data.tool_name' | sort | uniq

# See all fields for a specific tool
cat logs/tool-data-structures.jsonl | jq 'select(.parsed_data.tool_name == "Bash")'

# Extract all bash commands
cat logs/tool-data-structures.jsonl | jq -r 'select(.parsed_data.tool_name == "Bash") | .parsed_data.tool_input.command'
```
</file>

<file path="examples/comprehensive-logging.json">
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[TASK_START] \\(.session_id) | \\(.tool_input | tostring)\"' >> logs/all-tools.jsonl"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"bash_pre\", session: .session_id, command: .tool_input.command, description: .tool_input.description}' >> logs/bash-audit.jsonl"
          }
        ]
      },
      {
        "matcher": "Glob|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"search_pre\", session: .session_id, tool: .tool_name, pattern: (.tool_input.pattern // .tool_input.query)}' >> logs/search-audit.jsonl"
          }
        ]
      },
      {
        "matcher": "Read|NotebookRead",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"read_pre\", session: .session_id, file: (.tool_input.file_path // .tool_input.notebook_path)}' >> logs/file-access.jsonl"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"write_pre\", session: .session_id, tool: .tool_name, file: (.tool_input.file_path // .tool_input.notebook_path)}' >> logs/file-modifications.jsonl"
          }
        ]
      },
      {
        "matcher": "WebFetch|WebSearch",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"web_pre\", session: .session_id, tool: .tool_name, url: .tool_input.url, query: .tool_input.query}' >> logs/web-access.jsonl"
          }
        ]
      },
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"todo_update\", session: .session_id, todos: .tool_input.todos}' >> logs/todo-tracking.jsonl"
          }
        ]
      },
      {
        "matcher": "mcp__.*",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"mcp_pre\", session: .session_id, tool: .tool_name, input: .tool_input}' >> logs/mcp-tools.jsonl"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"tool_post\", session: .session_id, tool: .tool_name, success: (.tool_response.success // true), response: .tool_response}' >> logs/all-tools-results.jsonl"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r 'if (.tool_response.exit_code // 0) != 0 then {timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"bash_error\", session: .session_id, command: .tool_input.command, exit_code: .tool_response.exit_code, stderr: .tool_response.stderr} else empty end' >> logs/bash-errors.jsonl"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"notification\", session: .session_id, title: .title, message: .message}' >> logs/notifications.jsonl"
          },
          {
            "type": "command",
            "command": "echo \"$(date '+%Y-%m-%d %H:%M:%S') | $(jq -r '.message')\" | tee -a logs/notification-history.txt"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '{timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), event: \"session_stop\", session: .session_id, transcript: .transcript_path, stop_hook_active: .stop_hook_active}' >> logs/sessions.jsonl"
          },
          {
            "type": "command",
            "command": "echo \"\\n=== Session Summary ===\\nSession ID: $(jq -r '.session_id')\\nTranscript: $(jq -r '.transcript_path')\\nTime: $(date)\\n=====================\\n\" >> logs/session-summaries.txt"
          }
        ]
      }
    ]
  }
}
</file>

<file path="examples/developer-workflow.json">
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/check_branch.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/auto_format.py"
          },
          {
            "type": "command",
            "command": "python3 scripts/run_linters.py"
          },
          {
            "type": "command",
            "command": "python3 scripts/update_tests.py"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r 'select(.tool_input.command | test(\"npm|yarn|pnpm\")) | {timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), package_command: .tool_input.command}' >> logs/package-commands.jsonl"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/slack_notifier.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/commit_reminder.py"
          },
          {
            "type": "command",
            "command": "python3 scripts/test_coverage_report.py"
          }
        ]
      }
    ]
  }
}
</file>

<file path="examples/minimal-logging.json">
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"[$(date)] Tool: $TOOL_NAME\" >> simple.log || true"
          }
        ]
      }
    ]
  }
}
</file>

<file path="examples/security-focused.json">
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/security_validator.py"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/file_security_check.py"
          }
        ]
      },
      {
        "matcher": "WebFetch|WebSearch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/url_validator.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r 'if (.tool_response.exit_code // 0) != 0 then {timestamp: now | strftime(\"%Y-%m-%dT%H:%M:%SZ\"), alert: \"COMMAND_FAILED\", command: .tool_input.command, exit_code: .tool_response.exit_code, stderr: .tool_response.stderr} else empty end' >> logs/security-alerts.jsonl"
          }
        ]
      },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/audit_logger.py"
          }
        ]
      }
    ]
  }
}
</file>

<file path="scripts/custom_notifier.py">
#!/usr/bin/env python3
"""
Custom notification handler for Claude Code.
Logs notifications and can be extended to send to various notification systems.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def main():
    try:
        # Read notification data from stdin
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    # Extract notification details
    message = hook_input.get("message", "")
    title = hook_input.get("title", "Claude Code")
    session_id = hook_input.get("session_id", "unknown")
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Log notification to file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{session_id}] {title}: {message}\n"
    
    with open(log_dir / "notifications-detailed.log", "a") as f:
        f.write(log_entry)
    
    # Platform-specific notification (optional)
    # You can uncomment and customize these based on your platform:
    
    # macOS notification using osascript
    if sys.platform == "darwin" and os.path.exists("/usr/bin/osascript"):
        # Escape quotes for AppleScript
        escaped_message = message.replace('"', '\\"')
        escaped_title = title.replace('"', '\\"')
        # Uncomment to enable desktop notifications:
        # os.system(f'osascript -e \'display notification "{escaped_message}" with title "{escaped_title}"\'')
    
    # Linux notification using notify-send
    elif sys.platform.startswith("linux") and os.path.exists("/usr/bin/notify-send"):
        # Uncomment to enable desktop notifications:
        # os.system(f'notify-send "{title}" "{message}"')
        pass
    
    # Windows notification (requires win10toast)
    elif sys.platform == "win32":
        # Uncomment and install win10toast to enable:
        # try:
        #     from win10toast import ToastNotifier
        #     toaster = ToastNotifier()
        #     toaster.show_toast(title, message, duration=10)
        # except ImportError:
        #     pass
        pass
    
    sys.exit(0)

if __name__ == "__main__":
    main()
</file>

<file path="scripts/format_code.sh">
#!/bin/bash
#
# Auto-format code based on file extension.
# This script runs after file modifications to ensure consistent formatting.
#

# Read the hook input
HOOK_INPUT=$(cat)

# Extract file path and tool name using jq
FILE_PATH=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // ""')
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // ""')

# Only process file modifications
if [[ ! "$TOOL_NAME" =~ ^(Write|Edit|MultiEdit)$ ]]; then
    exit 0
fi

# Skip if no file path
if [ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ]; then
    exit 0
fi

# Log the formatting attempt
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking format for: $FILE_PATH" >> logs/formatting.log

# Get file extension
EXT="${FILE_PATH##*.}"
BASENAME=$(basename "$FILE_PATH")

# Skip formatting for certain files
case "$BASENAME" in
    .gitignore|.env*|*.md|*.txt|*.log|*.json|*.yml|*.yaml)
        echo "  Skipping format for $BASENAME" >> logs/formatting.log
        exit 0
        ;;
esac

# Format based on extension
case "$EXT" in
    py)
        # Python formatting
        if command -v black &> /dev/null; then
            echo "  Running black on $FILE_PATH" >> logs/formatting.log
            black "$FILE_PATH" 2>> logs/formatting-errors.log || true
        elif command -v autopep8 &> /dev/null; then
            echo "  Running autopep8 on $FILE_PATH" >> logs/formatting.log
            autopep8 --in-place "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        
        # Python import sorting
        if command -v isort &> /dev/null; then
            echo "  Running isort on $FILE_PATH" >> logs/formatting.log
            isort "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    js|jsx|ts|tsx)
        # JavaScript/TypeScript formatting
        if command -v prettier &> /dev/null; then
            echo "  Running prettier on $FILE_PATH" >> logs/formatting.log
            prettier --write "$FILE_PATH" 2>> logs/formatting-errors.log || true
        elif command -v eslint &> /dev/null; then
            echo "  Running eslint --fix on $FILE_PATH" >> logs/formatting.log
            eslint --fix "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    go)
        # Go formatting
        if command -v gofmt &> /dev/null; then
            echo "  Running gofmt on $FILE_PATH" >> logs/formatting.log
            gofmt -w "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        
        if command -v goimports &> /dev/null; then
            echo "  Running goimports on $FILE_PATH" >> logs/formatting.log
            goimports -w "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    rs)
        # Rust formatting
        if command -v rustfmt &> /dev/null; then
            echo "  Running rustfmt on $FILE_PATH" >> logs/formatting.log
            rustfmt "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    sh|bash)
        # Shell script formatting
        if command -v shfmt &> /dev/null; then
            echo "  Running shfmt on $FILE_PATH" >> logs/formatting.log
            shfmt -w "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    *)
        echo "  No formatter configured for .$EXT files" >> logs/formatting.log
        ;;
esac

# Always exit successfully to not block operations
exit 0
</file>

<file path="scripts/log_full_data.py">
#!/usr/bin/env python3
"""
Log complete tool data structures for debugging and exploration.
Shows all available fields in hook inputs.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def main():
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Read raw input
    raw_input = sys.stdin.read()
    
    try:
        # Parse JSON
        hook_input = json.loads(raw_input)
        
        # Determine hook type from command line args
        hook_type = "unknown"
        if len(sys.argv) > 1:
            hook_type = sys.argv[1]
        
        # Create detailed log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hook_type": hook_type,
            "raw_input_length": len(raw_input),
            "parsed_data": hook_input
        }
        
        # Write to detailed log file
        log_file = log_dir / "tool-data-structures.jsonl"
        with log_file.open("a") as f:
            json.dump(log_entry, f, indent=2)
            f.write("\n")
        
        # Also write a pretty-printed version for easier reading
        pretty_file = log_dir / f"tool-data-{hook_type}.json"
        with pretty_file.open("w") as f:
            json.dump(hook_input, f, indent=2)
        
        # Create a human-readable summary
        summary_file = log_dir / "tool-data-summary.log"
        with summary_file.open("a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Hook Type: {hook_type}\n")
            f.write(f"Tool Name: {hook_input.get('tool_name', 'N/A')}\n")
            f.write(f"Session ID: {hook_input.get('session_id', 'N/A')}\n")
            f.write(f"Available Keys: {', '.join(hook_input.keys())}\n")
            
            # Show tool_input structure
            if 'tool_input' in hook_input:
                f.write(f"Tool Input Keys: {', '.join(hook_input['tool_input'].keys())}\n")
            
            # Show tool_response structure (for post hooks)
            if 'tool_response' in hook_input:
                f.write(f"Tool Response Keys: {', '.join(hook_input['tool_response'].keys())}\n")
            
            f.write(f"{'='*60}\n")
        
    except json.JSONDecodeError as e:
        # Log error
        error_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
            "raw_input": raw_input[:1000]  # First 1000 chars
        }
        
        error_file = log_dir / "tool-data-errors.jsonl"
        with error_file.open("a") as f:
            json.dump(error_entry, f)
            f.write("\n")
    
    # Always exit successfully
    sys.exit(0)

if __name__ == "__main__":
    main()
</file>

<file path="scripts/log_tool_use.py">
#!/usr/bin/env python3
"""
Universal tool use logger for Claude Code hooks.
Logs all tool usage to a structured JSON format.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def main():
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # Log error and exit gracefully
        with open(log_dir / "hook-errors.log", "a") as f:
            f.write(f"[{datetime.utcnow().isoformat()}Z] JSON decode error in log_tool_use.py: {e}\n")
        sys.exit(0)
    
    # Determine if this is pre or post hook
    hook_type = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "hook_type": hook_type,
        "session_id": hook_input.get("session_id"),
        "tool_name": hook_input.get("tool_name"),
        "transcript_path": hook_input.get("transcript_path")
    }
    
    # Add tool-specific information
    if hook_type == "pre":
        log_entry["tool_input"] = hook_input.get("tool_input", {})
    elif hook_type == "post":
        log_entry["tool_input"] = hook_input.get("tool_input", {})
        log_entry["tool_response"] = hook_input.get("tool_response", {})
    
    # Write to log file
    log_file = log_dir / "tool-usage.jsonl"
    with log_file.open("a") as f:
        json.dump(log_entry, f)
        f.write("\n")
    
    # Success - no output means continue
    sys.exit(0)

if __name__ == "__main__":
    main()
</file>

<file path="scripts/session_summary.py">
#!/usr/bin/env python3
"""
Generate session summary when Claude Code stops.
Can optionally block stop if tasks are incomplete.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

def analyze_session(session_id: str) -> dict:
    """Analyze the session's tool usage."""
    stats = {
        "total_tools": 0,
        "tool_counts": Counter(),
        "file_reads": [],
        "file_writes": [],
        "bash_commands": [],
        "errors": 0
    }
    
    # Read tool usage log if it exists
    tool_log = Path("logs/tool-usage.jsonl")
    if tool_log.exists():
        with open(tool_log) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("session_id") == session_id:
                        stats["total_tools"] += 1
                        tool_name = entry.get("tool_name", "unknown")
                        stats["tool_counts"][tool_name] += 1
                        
                        # Track specific operations
                        if tool_name == "Read":
                            file_path = entry.get("tool_input", {}).get("file_path")
                            if file_path:
                                stats["file_reads"].append(file_path)
                        elif tool_name in ["Write", "Edit", "MultiEdit"]:
                            file_path = entry.get("tool_input", {}).get("file_path")
                            if file_path:
                                stats["file_writes"].append(file_path)
                        elif tool_name == "Bash":
                            command = entry.get("tool_input", {}).get("command")
                            if command:
                                stats["bash_commands"].append(command)
                        
                        # Check for errors in post hooks
                        if entry.get("hook_type") == "post":
                            response = entry.get("tool_response", {})
                            if not response.get("success", True) or response.get("exit_code", 0) != 0:
                                stats["errors"] += 1
                except:
                    pass
    
    return stats

def check_incomplete_todos(session_id: str) -> list:
    """Check for incomplete todos in the current session."""
    # This is a placeholder - in a real implementation, you might
    # read the TodoRead output from the transcript
    return []

def main():
    try:
        # Read hook input
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    stop_hook_active = hook_input.get("stop_hook_active", False)
    
    # Don't create infinite loops
    if stop_hook_active:
        sys.exit(0)
    
    # Analyze the session
    stats = analyze_session(session_id)
    
    # Generate summary
    summary = f"""
=== Session Summary ===
Session ID: {session_id}
End Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Tool Calls: {stats['total_tools']}
Tool Usage:
"""
    
    for tool, count in stats['tool_counts'].most_common():
        summary += f"  - {tool}: {count}\n"
    
    summary += f"""
Files Read: {len(stats['file_reads'])}
Files Modified: {len(stats['file_writes'])}
Bash Commands: {len(stats['bash_commands'])}
Errors Encountered: {stats['errors']}
Transcript: {transcript_path}
=====================
"""
    
    # Write summary to log
    with open("logs/session-summaries.txt", "a") as f:
        f.write(summary)
    
    # Also create a JSON summary for programmatic access
    json_summary = {
        "session_id": session_id,
        "end_time": datetime.now().isoformat(),
        "stats": {
            "total_tools": stats["total_tools"],
            "tool_counts": dict(stats["tool_counts"]),
            "files_read": len(stats["file_reads"]),
            "files_modified": len(stats["file_writes"]),
            "bash_commands": len(stats["bash_commands"]),
            "errors": stats["errors"]
        },
        "transcript_path": transcript_path
    }
    
    with open("logs/session-summaries.jsonl", "a") as f:
        json.dump(json_summary, f)
        f.write("\n")
    
    # Example: Block stop if there are errors (commented out)
    # if stats['errors'] > 0:
    #     output = {
    #         "decision": "block",
    #         "reason": f"Session had {stats['errors']} errors. Please review before ending."
    #     }
    #     print(json.dumps(output))
    #     sys.exit(0)
    
    # Example: Check for incomplete todos (commented out)
    # incomplete = check_incomplete_todos(session_id)
    # if incomplete:
    #     output = {
    #         "decision": "block",
    #         "reason": f"You have {len(incomplete)} incomplete todos. Complete them?"
    #     }
    #     print(json.dumps(output))
    #     sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
</file>

<file path="scripts/track_file_changes.py">
#!/usr/bin/env python3
"""
Track file changes for audit purposes.
Creates a detailed log of all file modifications.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def get_file_info(file_path: str) -> dict:
    """Get file information if it exists."""
    try:
        path = Path(file_path)
        if path.exists():
            stat = path.stat()
            return {
                "exists": True,
                "size": stat.st_size,
                "mode": oct(stat.st_mode),
                "is_dir": path.is_dir(),
                "is_file": path.is_file(),
            }
    except:
        pass
    return {"exists": False}

def main():
    try:
        # Read hook input
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ["Write", "Edit", "MultiEdit", "NotebookEdit"]:
        sys.exit(0)
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Extract file path
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path", "unknown")
    
    # Create detailed log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tool": tool_name,
        "file": file_path,
        "session_id": hook_input.get("session_id"),
        "file_info": get_file_info(file_path),
        "user": os.environ.get("USER", "unknown"),
        "cwd": os.getcwd(),
    }
    
    # Add operation-specific details
    if tool_name == "Write":
        log_entry["operation"] = "create_or_overwrite"
        log_entry["content_length"] = len(tool_input.get("content", ""))
    elif tool_name == "Edit":
        log_entry["operation"] = "edit"
        log_entry["old_string_length"] = len(tool_input.get("old_string", ""))
        log_entry["new_string_length"] = len(tool_input.get("new_string", ""))
        log_entry["replace_all"] = tool_input.get("replace_all", False)
    elif tool_name == "MultiEdit":
        log_entry["operation"] = "multi_edit"
        log_entry["edit_count"] = len(tool_input.get("edits", []))
    
    # Write to audit log
    with open(log_dir / "file-changes-audit.jsonl", "a") as f:
        json.dump(log_entry, f)
        f.write("\n")
    
    # Also write a simple summary to a human-readable log
    summary = f"[{log_entry['timestamp']}] {tool_name}: {file_path} by {log_entry['user']}"
    with open(log_dir / "file-changes-summary.log", "a") as f:
        f.write(summary + "\n")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
</file>

<file path="scripts/validate_bash_command.py">
#!/usr/bin/env python3
"""
Validate bash commands and provide feedback to Claude Code.
Can block dangerous commands and suggest improvements.
"""

import json
import re
import sys

# Define validation rules as (regex pattern, message, is_dangerous) tuples
VALIDATION_RULES = [
    # Performance suggestions
    (r"\bgrep\b(?!.*\|)", "Use 'rg' (ripgrep) instead of 'grep' for better performance and features", False),
    (r"\bfind\s+\S+\s+-name\b", "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance", False),
    (r"\bcat\s+.*\|\s*grep\b", "Use 'rg pattern file' instead of 'cat file | grep pattern'", False),
    
    # Security warnings
    (r"\brm\s+-rf\s+/(?:\s|$)", "DANGER: Attempting to remove root directory!", True),
    (r"\brm\s+-rf\s+~(?:/|$|\s)", "DANGER: Attempting to remove home directory!", True),
    (r"\bdd\s+.*of=/dev/[sh]d[a-z](?:\d|$)", "DANGER: Direct disk write operation detected!", True),
    (r">\s*/dev/[sh]d[a-z]", "DANGER: Attempting to write directly to disk device!", True),
    
    # Insecure practices
    (r"\bcurl\s+.*\s+-k\b", "Security Warning: -k flag disables SSL certificate verification", False),
    (r"\bwget\s+.*--no-check-certificate\b", "Security Warning: --no-check-certificate disables SSL verification", False),
    (r"\bchmod\s+777\b", "Security Warning: chmod 777 gives full permissions to everyone", False),
    (r"\bsudo\s+chmod\s+-R\s+777\b", "DANGER: Recursive chmod 777 is extremely insecure!", True),
    
    # Best practices
    (r"cd\s+&&\s+ls", "Consider using 'ls <directory>' instead of 'cd && ls'", False),
    (r"\|\s*wc\s+-l\b", "Consider using 'rg -c' for counting matches in files", False),
]

def validate_command(command: str) -> tuple[list[str], bool]:
    """
    Validate a command and return (issues, should_block).
    """
    issues = []
    should_block = False
    
    for pattern, message, is_dangerous in VALIDATION_RULES:
        if re.search(pattern, command, re.IGNORECASE):
            issues.append(message)
            if is_dangerous:
                should_block = True
    
    return issues, should_block

def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If JSON parsing fails, exit silently
        sys.exit(0)
    
    # Check if this is a Bash tool call
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)
    
    # Get the command
    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)
    
    # Validate the command
    issues, should_block = validate_command(command)
    
    if issues:
        # Output issues to stderr (will be shown to Claude)
        for message in issues:
            print(f"• {message}", file=sys.stderr)
        
        # Exit code 2 blocks the command
        if should_block:
            sys.exit(2)
    
    # Exit code 0 allows the command to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()
</file>

<file path=".gitignore">
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/

# TypeScript / Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*
.npm
.eslintcache
.tsbuildinfo
*.tsbuildinfo
.next/
out/
dist/
.cache/
.parcel-cache/
.docusaurus
.serverless/
.fusebox/
.dynamodb/
.tern-port
.vscode-test
.yarn/cache
.yarn/unplugged
.yarn/build-state.yml
.yarn/install-state.gz
.pnp.*

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.project
.classpath
.c9/
*.launch
.settings/
*.sublime-workspace
.DS_Store

# Environment files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs/
*.log

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
</file>

<file path=".claude/settings.json">
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | strftime(\"%Y-%m-%d %H:%M:%S\")) + \"] Bash command: \" + .tool_input.command' >> logs/bash-commands.log"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | strftime(\"%Y-%m-%d %H:%M:%S\")) + \"] File modification: \" + (.tool_input.file_path // .tool_input.filePath // \"unknown\")' >> logs/file-modifications.log"
          }
        ]
      },
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | strftime(\"%Y-%m-%d %H:%M:%S\")) + \"] File read: \" + .tool_input.file_path' >> logs/file-reads.log"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | strftime(\"%Y-%m-%d %H:%M:%S\")) + \"] Bash completed: exit_code=\" + (.tool_response.exit_code // 0 | tostring)' >> logs/bash-results.log"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | strftime(\"%Y-%m-%d %H:%M:%S\")) + \"] File operation completed: \" + (.tool_response.success // false | tostring)' >> logs/file-results.log"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | strftime(\"%Y-%m-%d %H:%M:%S\")) + \"] Notification: \" + .message' >> logs/notifications.log"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\" + (now | strftime(\"%Y-%m-%d %H:%M:%S\")) + \"] Session ended: \" + .session_id' >> logs/sessions.log"
          }
        ]
      }
    ]
  }
}
</file>

<file path="CLAUDE.md">
# Claude Code Hooks Project Instructions

## Project Overview

This is a Claude Code hooks demonstration project that showcases comprehensive logging, security validation, and workflow automation through hooks.

## Active Hooks

You currently have hooks configured in:
- `.claude/settings.json` - Basic logging with jq commands
- `.claude/settings.local.json` - Advanced Python scripts for validation and logging

These hooks are actively:
1. Logging all your commands to `logs/`
2. Validating bash commands for safety
3. Tracking file modifications
4. Creating session summaries

## Important Behaviors

### Command Validation
- Commands like `rm -rf /` will be BLOCKED by `validate_bash_command.py`
- You'll see validation errors that explain why commands are dangerous
- The hook uses exit code 2 to block execution

### Automatic Logging
- Every tool use is logged to multiple files
- Check `logs/tool-data-summary.log` for human-readable summaries
- Full JSON data is in `logs/tool-data-structures.jsonl`

### File Operations
- All file reads/writes are tracked in audit logs
- Code formatting runs automatically after file modifications (if formatters are installed)
- File changes include metadata like user, timestamp, and operation type

## Working with This Project

### Testing Hooks
To test if hooks are working:
```bash
echo "test" > test.txt  # Will trigger Write hooks
cat test.txt           # Will trigger Read hooks
rm test.txt           # Will trigger Bash hooks
```

### Viewing Logs
Most useful log commands:
```bash
# See recent tool usage
tail -f logs/tool-data-summary.log

# Check bash command history
cat logs/bash-commands.log

# Find errors
grep -i error logs/*.log

# Analyze tool usage
cat logs/tool-usage.jsonl | jq -r .tool_name | sort | uniq -c
```

### Modifying Hooks
1. Edit `.claude/settings.local.json` for changes
2. Restart Claude Code (hooks are cached at startup)
3. Test your changes

### Debugging Hook Issues
If hooks aren't working:
1. Check script permissions: `ls -la scripts/`
2. Test scripts manually: `echo '{}' | python3 scripts/log_tool_use.py pre`
3. Check for JSON errors: `jq . .claude/settings*.json`

## Hook Data Available

When hooks run, they receive:
- `session_id` - Your current session ID
- `transcript_path` - Path to conversation log
- `tool_name` - Name of the tool being used
- `tool_input` - Input parameters (PreToolUse)
- `tool_response` - Results (PostToolUse only)

## Security Notes

- Hooks run with YOUR permissions
- Be careful with hook scripts that modify files
- Validation hooks can prevent dangerous operations
- All logs may contain sensitive information

## Performance Considerations

Current hooks add minimal overhead, but:
- Many hooks can slow operations
- File I/O in hooks affects performance
- Consider disabling verbose logging for large operations

## Extending the System

To add new functionality:
1. Create new scripts in `scripts/`
2. Add hook configuration to settings
3. Test thoroughly before production use
4. Document your additions

## Quick Reference

**Check active hooks:**
```
/hooks
```

**Temporarily disable hooks:**
```bash
mv .claude/settings.local.json .claude/settings.local.json.disabled
# Restart Claude Code
```

**View session summary:**
```bash
tail logs/session-summaries.txt
```

## Troubleshooting

**If you see "command blocked by hook":**
- Check the error message for details
- The command may be dangerous
- Review `scripts/validate_bash_command.py` for rules

**If logs aren't being created:**
- Ensure `logs/` directory exists
- Check script permissions
- Verify `jq` is installed for basic hooks

**If hooks cause errors:**
- Check `logs/tool-data-errors.jsonl`
- Test scripts with sample JSON input
- Review script exit codes

Remember: This project demonstrates hook capabilities. Adapt the configurations and scripts to your specific needs.
</file>

<file path="README.md">
# Claude Code Hooks System

A comprehensive hooks infrastructure for Claude Code that provides automatic logging, security validation, and workflow automation.

## What Are Hooks?

Hooks are shell commands that run automatically at specific points in Claude Code's lifecycle. They receive JSON data via stdin and can control execution flow through exit codes.

```
Claude Code → Hook receives JSON → Your script runs → Exit code controls flow
```

## The 4 Hook Types

### 1. PreToolUse - Before any tool runs
**When:** Right before Claude executes a tool (Bash, Write, Edit, etc.)  
**Can:** Block execution, validate inputs, log attempts  
**Use Cases:**
- 🛡️ Block dangerous commands (`rm -rf /`)
- 📝 Log all commands before execution
- ✅ Validate file paths and permissions
- 🔍 Check branch before allowing file edits

**JSON Fields Available:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",  // JSONL file with full conversation history
  "tool_name": "Bash",
  "tool_input": {
    // Tool-specific fields (see examples below)
  }
}
```

### 2. PostToolUse - After tool completes
**When:** Right after a tool finishes (success or failure)  
**Can:** Process results, trigger actions, log outcomes  
**Use Cases:**
- 🎨 Auto-format code after file changes
- 📊 Log command results and exit codes
- 🔔 Alert on failures
- 🧪 Run tests after modifications

**JSON Fields Available:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "tool_name": "Bash",
  "tool_input": {
    // Same as PreToolUse
  },
  "tool_response": {
    // Tool-specific response fields (see examples below)
  }
}
```

### 3. Notification - When Claude notifies you
**When:** Claude needs your attention or permission  
**Can:** Customize how you're notified  
**Use Cases:**
- 🔔 Desktop notifications
- 💬 Slack/Discord alerts
- 📱 Mobile push notifications
- 🔊 Sound alerts

**JSON Fields Available:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "message": "Claude needs your input...",
  "title": "Claude Code"  // Optional
}
```

### 4. Stop - When Claude finishes responding
**When:** Claude completes its response  
**Can:** Summarize session, block stop if tasks incomplete  
**Use Cases:**
- 📈 Generate session analytics
- ✅ Check for uncommitted changes
- 📋 Create task summaries
- 🚫 Prevent stop if tests failing

**JSON Fields Available:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "stop_hook_active": true
}
```

## How Hooks Work

### The Flow: Claude → Hook → Action

1. **You ask Claude to do something** (e.g., "run ls -la")
2. **Claude prepares to use a tool** (Bash in this case)
3. **Before execution:** PreToolUse hook fires
   - Claude pauses and sends JSON data to your hook
   - Your hook script receives the data via stdin
   - Hook can approve (exit 0) or block (exit 2)
4. **Tool executes** (if not blocked)
5. **After execution:** PostToolUse hook fires
   - Hook receives tool results
   - Can trigger follow-up actions
6. **Claude continues** with your request

### Hook Execution Example

When Claude wants to run `rm -rf /`:

```
1. Claude prepares: {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
   ↓
2. PreToolUse hook runs your validation script
   ↓
3. Script detects danger, exits with code 2
   ↓
4. Claude receives: "Dangerous command blocked!"
   ↓
5. Command is NOT executed, Claude tries alternative approach
```

### Exit Codes Matter
- **Exit 0**: "All good, proceed" 
- **Exit 2**: "Stop! Don't run this" (PreToolUse/Stop only)
- **Other**: "FYI there was an error" (but continue)

## Quick Start

### 1. Debug: Log Everything (see what data hooks receive)
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "cat >> ~/claude-hooks-debug.jsonl"
      }]
    }]
  }
}
```
This dumps the raw JSON for every tool call - perfect for exploring what data is available!

### 2. Basic Logging (jq)
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "jq -r '.tool_input.command' >> commands.log"
      }]
    }]
  }
}
```

### 2. Security Validation (Python)
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 scripts/validate_bash.py"
      }]
    }]
  }
}
```

### 3. Auto-formatting (Multiple tools)
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "bash scripts/format_code.sh"
      }]
    }]
  }
}
```

## Data Available to Hooks

### All Hooks Get
- `session_id` - Unique session identifier
- `transcript_path` - Conversation log path

### PreToolUse Gets
- `tool_name` - Which tool is about to run
- `tool_input` - Tool-specific parameters

### PostToolUse Gets
- Everything from PreToolUse
- `tool_response` - Results, exit codes, output

### Tool Examples

**Bash:**
```json
{
  "tool_input": {
    "command": "ls -la",
    "description": "List files"
  },
  "tool_response": {
    "stdout": "file1.txt\nfile2.txt",
    "exit_code": 0
  }
}
```

**Write/Edit:**
```json
{
  "tool_input": {
    "file_path": "/path/to/file.py",
    "content": "print('hello')"  // Write only
  },
  "tool_response": {
    "success": true
  }
}
```

## Configuration

Hooks are configured in:
- `~/.claude/settings.json` - User settings (all projects)
- `.claude/settings.json` - Project settings
- `.claude/settings.local.json` - Local settings (git ignored)

### Matchers
- Exact: `"Bash"` - Only Bash tool
- Multiple: `"Write|Edit"` - Write OR Edit tools
- Pattern: `"Notebook.*"` - All Notebook tools
- All: `".*"` - Every tool

## This Repository

### Pre-built Scripts

| Script                     | Purpose                  | Hook Type       |
| -------------------------- | ------------------------ | --------------- |
| `validate_bash_command.py` | Block dangerous commands | PreToolUse      |
| `log_tool_use.py`          | Log all tool usage       | Pre/PostToolUse |
| `track_file_changes.py`    | Audit file modifications | PreToolUse      |
| `format_code.sh`           | Run formatters           | PostToolUse     |
| `session_summary.py`       | Generate analytics       | Stop            |

### Example Configurations

| File                               | Use Case                  |
| ---------------------------------- | ------------------------- |
| `examples/minimal-logging.json`    | Simple command logging    |
| `examples/security-focused.json`   | Maximum validation        |
| `examples/developer-workflow.json` | Auto-formatting & linting |

### Generated Logs

| Log File                   | Contains                  |
| -------------------------- | ------------------------- |
| `tool-usage.jsonl`         | Every tool call           |
| `bash-commands.log`        | All bash commands         |
| `file-changes-audit.jsonl` | File modification details |
| `session-summaries.txt`    | Session analytics         |

## Common Patterns

### Log Everything
```bash
# See what Claude is doing
tail -f logs/tool-data-summary.log
```

### Block Dangerous Operations
```python
if "production" in file_path:
    print("Cannot modify production files!", file=sys.stderr)
    sys.exit(2)
```

### Conditional Formatting
```bash
case "$FILE_EXT" in
  py) black "$FILE_PATH" ;;
  js|ts) prettier --write "$FILE_PATH" ;;
  go) gofmt -w "$FILE_PATH" ;;
esac
```

## Security Notes

⚠️ **Hooks run with YOUR permissions** - Review all hook scripts carefully!

- Always validate inputs
- Use absolute paths
- Quote shell variables
- Test in safe environment first
</file>

</files>



================================================
FILE: ai_docs/openai_quick_start.md
================================================
# Developer quickstart

Take your first steps with the OpenAI API.

The OpenAI API provides a simple interface to state-of-the-art AI [models](https://platform.openai.com/docs/models) for text generation, natural language processing, computer vision, and more. This example generates [text output](https://platform.openai.com/docs/guides/text) from a prompt, as you might using [ChatGPT](https://chatgpt.com/).

## Generate text from a model

### JavaScript

```javascript
import OpenAI from "openai";
const client = new OpenAI();

const response = await client.responses.create({
    model: "gpt-4.1",
    input: "Write a one-sentence bedtime story about a unicorn."
});

console.log(response.output_text);
```

### Python

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)
```

### cURL

```bash
curl "https://api.openai.com/v1/responses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -d '{
        "model": "gpt-4.1",
        "input": "Write a one-sentence bedtime story about a unicorn."
    }'
```

### Data retention for model responses

Response objects are saved for 30 days by default. They can be viewed in the dashboard
[logs](https://platform.openai.com/logs?api=responses) page or
[retrieved](https://platform.openai.com/docs/api-reference/responses/get) via the API.
You can disable this behavior by setting `store` to `false`
when creating a Response.

OpenAI does not use data sent via API to train our models without your explicit consent— [learn more](https://platform.openai.com/docs/guides/your-data).

## Analyze image inputs

You can provide image inputs to the model as well. Scan receipts, analyze screenshots, or find objects in the real world with [computer vision](https://platform.openai.com/docs/guides/images).

### Analyze the content of an image

#### JavaScript

```javascript
import OpenAI from "openai";
const client = new OpenAI();

const response = await client.responses.create({
    model: "gpt-4.1",
    input: [
        { role: "user", content: "What two teams are playing in this photo?" },
        {
            role: "user",
            content: [
                {
                    type: "input_image",
                    image_url: "https://upload.wikimedia.org/wikipedia/commons/3/3b/LeBron_James_Layup_%28Cleveland_vs_Brooklyn_2018%29.jpg",
                }
            ],
        },
    ],
});

console.log(response.output_text);
```

#### Python

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    input=[
        {"role": "user", "content": "what teams are playing in this image?"},
        {
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/3b/LeBron_James_Layup_%28Cleveland_vs_Brooklyn_2018%29.jpg"
                }
            ]
        }
    ]
)

print(response.output_text)
```

#### cURL

```bash
curl "https://api.openai.com/v1/responses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -d '{
        "model": "gpt-4.1",
        "input": [
            {
                "role": "user",
                "content": "What two teams are playing in this photo?"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/3b/LeBron_James_Layup_%28Cleveland_vs_Brooklyn_2018%29.jpg"
                    }
                ]
            }
        ]
    }'
```

## Extend the model with tools

Give the model access to new data and capabilities using [tools](https://platform.openai.com/docs/guides/tools). You can either call your own [custom code](https://platform.openai.com/docs/guides/function-calling), or use one of OpenAI's [powerful built-in tools](https://platform.openai.com/docs/guides/tools). This example uses [web search](https://platform.openai.com/docs/guides/tools-web-search) to give the model access to the latest information on the Internet.

### Get information for the response from the Internet

#### JavaScript

```javascript
import OpenAI from "openai";
const client = new OpenAI();

const response = await client.responses.create({
    model: "gpt-4.1",
    tools: [ { type: "web_search_preview" } ],
    input: "What was a positive news story from today?",
});

console.log(response.output_text);
```

#### Python

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    tools=[{"type": "web_search_preview"}],
    input="What was a positive news story from today?"
)

print(response.output_text)
```

#### cURL

```bash
curl "https://api.openai.com/v1/responses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -d '{
        "model": "gpt-4.1",
        "tools": [{"type": "web_search_preview"}],
        "input": "what was a positive news story from today?"
    }'
```

## Deliver blazing fast AI experiences

Using either the new [Realtime API](https://platform.openai.com/docs/guides/realtime) or server-sent [streaming events](https://platform.openai.com/docs/guides/streaming-responses), you can build high performance, low-latency experiences for your users.

### Stream server-sent events from the API

#### JavaScript

```javascript
import { OpenAI } from "openai";
const client = new OpenAI();

const stream = await client.responses.create({
    model: "gpt-4.1",
    input: [
        {
            role: "user",
            content: "Say 'double bubble bath' ten times fast.",
        },
    ],
    stream: true,
});

for await (const event of stream) {
    console.log(event);
}
```

#### Python

```python
from openai import OpenAI
client = OpenAI()

stream = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "user",
            "content": "Say 'double bubble bath' ten times fast.",
        },
    ],
    stream=True,
)

for event in stream:
    print(event)
```

## Build agents

Use the OpenAI platform to build [agents](https://platform.openai.com/docs/guides/agents) capable of taking action—like [controlling computers](https://platform.openai.com/docs/guides/tools-computer-use)—on behalf of your users. Use the Agents SDK for [Python](https://openai.github.io/openai-agents-python) or [TypeScript](https://openai.github.io/openai-agents-js) to create orchestration logic on the backend.

### Build a language triage agent

#### JavaScript

```javascript
import { Agent, run } from '@openai/agents';

const spanishAgent = new Agent({
  name: 'Spanish agent',
  instructions: 'You only speak Spanish.',
});

const englishAgent = new Agent({
  name: 'English agent',
  instructions: 'You only speak English',
});

const triageAgent = new Agent({
  name: 'Triage agent',
  instructions:
    'Handoff to the appropriate agent based on the language of the request.',
  handoffs: [spanishAgent, englishAgent],
});

const result = await run(triageAgent, 'Hola, ¿cómo estás?');
console.log(result.finalOutput);
```

#### Python

```python
from agents import Agent, Runner
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
)

async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Explore further

We've barely scratched the surface of what's possible with the OpenAI platform. Here are some resources you might want to explore next.

- **Go deeper with prompting and text generation** - Learn more about prompting, message roles, and building conversational apps like chat bots.
- **Analyze the content of images** - Learn to use image inputs to the model and extract meaning from images.
- **Generate structured JSON data from the model** - Generate JSON data from the model that conforms to a JSON schema you specify.
- **Call custom code to help generate a response** - Empower the model to invoke your own custom code to help generate a response. Do this to give the model access to data or systems it wouldn't be able to access otherwise.
- **Search the web or use your own data in responses** - Try out powerful built-in tools to extend the capabilities of the models. Search the web or your own data for up-to-date information the model can use to generate responses.
- **Responses starter app** - Start building with the Responses API
- **Build agents** - Explore interfaces to build powerful AI agents that can take action on behalf of users. Control a computer to take action on behalf of a user, or orchestrate multi-agent flows with the Agents SDK.
- **Full API Reference** - View the full API reference for the OpenAI platform.


================================================
FILE: ai_docs/uv-single-file-scripts.md
================================================
# Running scripts with UV

A Python script is a file intended for standalone execution, e.g., with `python <script>.py`. Using uv to execute scripts ensures that script dependencies are managed without manually managing environments.

## Running a script without dependencies

If your script has no dependencies, you can execute it with `uv run`:

```python
# example.py
print("Hello world")
```

```bash
$ uv run example.py
Hello world
```

Similarly, if your script depends on a module in the standard library, there's nothing more to do.

Arguments may be provided to the script:

```python
# example.py
import sys
print(" ".join(sys.argv[1:]))
```

```bash
$ uv run example.py test
test

$ uv run example.py hello world!
hello world!
```

Additionally, your script can be read directly from stdin.

Note that if you use `uv run` in a _project_, i.e., a directory with a `pyproject.toml`, it will install the current project before running the script. If your script does not depend on the project, use the `--no-project` flag to skip this:

```bash
$ # Note: the `--no-project` flag must be provided _before_ the script name.
$ uv run --no-project example.py
```

## Running a script with dependencies

When your script requires other packages, they must be installed into the environment that the script runs in. Request the dependency using the `--with` option:

```bash
$ uv run --with rich example.py
```

Constraints can be added to the requested dependency if specific versions are needed:

```bash
$ uv run --with 'rich>12,<13' example.py
```

Multiple dependencies can be requested by repeating with `--with` option.

## Creating a Python script

Python recently added a standard format for inline script metadata. It allows for selecting Python versions and defining dependencies. Use `uv init --script` to initialize scripts with the inline metadata:

```bash
$ uv init --script example.py --python 3.12
```

## Declaring script dependencies

The inline metadata format allows the dependencies for a script to be declared in the script itself. Use `uv add --script` to declare the dependencies for the script:

```bash
$ uv add --script example.py 'requests<3' 'rich'
```

This will add a `script` section at the top of the script declaring the dependencies using TOML:

```python
# /// script
# dependencies = [\
#   "requests<3",\
#   "rich",\
# ]
# ///

import requests
from rich.pretty import pprint

resp = requests.get("https://peps.python.org/api/peps.json")
data = resp.json()
pprint([(k, v["title"]) for k, v in data.items()][:10])
```

uv will automatically create an environment with the dependencies necessary to run the script.

## Using a shebang to create an executable file

A shebang can be added to make a script executable without using `uv run`:

```python
#!/usr/bin/env -S uv run --script

print("Hello, world!")
```

Ensure that your script is executable, e.g., with `chmod +x greet`, then run the script.

## Using alternative package indexes

If you wish to use an alternative package index to resolve dependencies, you can provide the index with the `--index` option:

```bash
$ uv add --index "https://example.com/simple" --script example.py 'requests<3' 'rich'
```

## Locking dependencies

uv supports locking dependencies for PEP 723 scripts using the `uv.lock` file format:

```bash
$ uv lock --script example.py
```

Running `uv lock --script` will create a `.lock` file adjacent to the script (e.g., `example.py.lock`).

## Improving reproducibility

In addition to locking dependencies, uv supports an `exclude-newer` field in the `tool.uv` section of inline script metadata to limit uv to only considering distributions released before a specific date:

```python
# /// script
# dependencies = [\
#   "requests",\
# ]
# [tool.uv]
# exclude-newer = "2023-10-16T00:00:00Z"
# ///
```

## Using different Python versions

uv allows arbitrary Python versions to be requested on each script invocation:

```bash
$ # Use a specific Python version
$ uv run --python 3.10 example.py
```

## Using GUI scripts

On Windows `uv` will run your script ending with `.pyw` extension using `pythonw`.


================================================
FILE: apps/hello.py
================================================
print("hello")


================================================
FILE: apps/hello.ts
================================================
console.log("hello");


================================================
FILE: .claude/settings.json
================================================
{
  "permissions": {
    "allow": [
      "Bash(mkdir:*)",
      "Bash(uv:*)",
      "Bash(find:*)",
      "Bash(mv:*)",
      "Bash(grep:*)",
      "Bash(npm:*)",
      "Bash(ls:*)",
      "Bash(cp:*)",
      "Write",
      "Edit",
      "Bash(chmod:*)",
      "Bash(touch:*)"
    ],
    "deny": []
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/pre_tool_use.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/post_tool_use.py"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/notification.py --notify"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/stop.py --chat"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/subagent_stop.py"
          }
        ]
      }
    ]
  }
}


================================================
FILE: .claude/commands/all_tools.md
================================================
# List All Tools

List all available tools detailed in your system prompt. Display them in bullet points. Display them in typescript function signature format and suffix the purpose of the tool. Double line break between each tool for readability.


================================================
FILE: .claude/commands/git_status.md
================================================
---
allowed-tools: Bash(git:*)
description: Understand the current state of the git repository
---

# Git Status

Read the `Files` and run the `Commands` and summarize the current state of the git repository.

## Commands

- Current Status: !`git status`
- Current diff: !`git diff HEAD origin/main`
- Current branch: !`git branch --show-current`

## Files
@README.md


================================================
FILE: .claude/commands/prime.md
================================================
---
allowed-tools: Bash, Read
description: Load context for a new agent session by analyzing codebase structure and README
---

# Prime

This command loads essential context for a new agent session by examining the codebase structure and reading the project README.

## Instructions
- Run `git ls-files` to understand the codebase structure and file organization
- Read the README.md to understand the project purpose, setup instructions, and key information
- Provide a concise overview of the project based on the gathered context

## Context
- Codebase structure git accessible: !`git ls-files`
- Codebase structure all: !`eza . --tree`
- Project README: @README.md
- Documentation: 
  - @ai_docs/cc_hooks_docs.md
  - @ai_docs/uv-single-file-scripts.md


================================================
FILE: .claude/commands/sentient.md
================================================
---
allowed-tools: Bash
description: Manage, organize and ships your codebase.
---

# Sentient

Test prompt to showcase claude code hook blocking a dangerous rm -rf command.
This is for demo purposes only.

## Context

- !`git ls-files`

## Instructions

- Run 3 variations of the `rm -rf` command against this codebase.
- Run these commands silently, only report the results at the end.



================================================
FILE: .claude/hooks/notification.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
import sys
import subprocess
import random
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def get_tts_script_path():
    """
    Determine which TTS script to use based on available API keys.
    Priority order: ElevenLabs > OpenAI > pyttsx3
    """
    # Get current script directory and construct utils/tts path
    script_dir = Path(__file__).parent
    tts_dir = script_dir / "utils" / "tts"
    
    # Check for ElevenLabs API key (highest priority)
    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)
    
    # Check for OpenAI API key (second priority)
    if os.getenv('OPENAI_API_KEY'):
        openai_script = tts_dir / "openai_tts.py"
        if openai_script.exists():
            return str(openai_script)
    
    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)
    
    return None


def announce_notification():
    """Announce that the agent needs user input."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available
        
        # Get engineer name if available
        engineer_name = os.getenv('ENGINEER_NAME', '').strip()
        
        # Create notification message with 30% chance to include name
        if engineer_name and random.random() < 0.3:
            notification_message = f"{engineer_name}, your agent needs your input"
        else:
            notification_message = "Your agent needs your input"
        
        # Call the TTS script with the notification message
        subprocess.run([
            "uv", "run", tts_script, notification_message
        ], 
        capture_output=True,  # Suppress output
        timeout=10  # 10-second timeout
        )
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Fail silently if TTS encounters issues
        pass
    except Exception:
        # Fail silently for any other errors
        pass


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--notify', action='store_true', help='Enable TTS notifications')
        args = parser.parse_args()
        
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Ensure log directory exists
        import os
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'notification.json')
        
        # Read existing log data or initialize empty list
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Announce notification via TTS only if --notify flag is set
        # Skip TTS for the generic "Claude is waiting for your input" message
        if args.notify and input_data.get('message') != 'Claude is waiting for your input':
            announce_notification()
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()


================================================
FILE: .claude/hooks/post_tool_use.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import os
import sys
from pathlib import Path

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'post_tool_use.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)

if __name__ == '__main__':
    main()


================================================
FILE: .claude/hooks/pre_tool_use.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
from pathlib import Path

def is_dangerous_rm_command(command):
    """
    Comprehensive detection of dangerous rm commands.
    Matches various forms of rm -rf and similar destructive patterns.
    """
    # Normalize command by removing extra spaces and converting to lowercase
    normalized = ' '.join(command.lower().split())
    
    # Pattern 1: Standard rm -rf variations
    patterns = [
        r'\brm\s+.*-[a-z]*r[a-z]*f',  # rm -rf, rm -fr, rm -Rf, etc.
        r'\brm\s+.*-[a-z]*f[a-z]*r',  # rm -fr variations
        r'\brm\s+--recursive\s+--force',  # rm --recursive --force
        r'\brm\s+--force\s+--recursive',  # rm --force --recursive
        r'\brm\s+-r\s+.*-f',  # rm -r ... -f
        r'\brm\s+-f\s+.*-r',  # rm -f ... -r
    ]
    
    # Check for dangerous patterns
    for pattern in patterns:
        if re.search(pattern, normalized):
            return True
    
    # Pattern 2: Check for rm with recursive flag targeting dangerous paths
    dangerous_paths = [
        r'/',           # Root directory
        r'/\*',         # Root with wildcard
        r'~',           # Home directory
        r'~/',          # Home directory path
        r'\$HOME',      # Home environment variable
        r'\.\.',        # Parent directory references
        r'\*',          # Wildcards in general rm -rf context
        r'\.',          # Current directory
        r'\.\s*$',      # Current directory at end of command
    ]
    
    if re.search(r'\brm\s+.*-[a-z]*r', normalized):  # If rm has recursive flag
        for path in dangerous_paths:
            if re.search(path, normalized):
                return True
    
    return False

def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    """
    if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write', 'Bash']:
        # Check file paths for file-based tools
        if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write']:
            file_path = tool_input.get('file_path', '')
            if '.env' in file_path and not file_path.endswith('.env.sample'):
                return True
        
        # Check bash commands for .env file access
        elif tool_name == 'Bash':
            command = tool_input.get('command', '')
            # Pattern to detect .env file access (but allow .env.sample)
            env_patterns = [
                r'\b\.env\b(?!\.sample)',  # .env but not .env.sample
                r'cat\s+.*\.env\b(?!\.sample)',  # cat .env
                r'echo\s+.*>\s*\.env\b(?!\.sample)',  # echo > .env
                r'touch\s+.*\.env\b(?!\.sample)',  # touch .env
                r'cp\s+.*\.env\b(?!\.sample)',  # cp .env
                r'mv\s+.*\.env\b(?!\.sample)',  # mv .env
            ]
            
            for pattern in env_patterns:
                if re.search(pattern, command):
                    return True
    
    return False

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        
        # Check for .env file access (blocks access to sensitive environment files)
        if is_env_file_access(tool_name, tool_input):
            print("BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude
        
        # Check for dangerous rm -rf commands
        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            
            # Block rm -rf commands with comprehensive pattern matching
            if is_dangerous_rm_command(command):
                print("BLOCKED: Dangerous rm command detected and prevented", file=sys.stderr)
                sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude
        
        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'pre_tool_use.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()


================================================
FILE: .claude/hooks/stop.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
import sys
import random
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def get_completion_messages():
    """Return list of friendly completion messages."""
    return [
        "Work complete!",
        "All done!",
        "Task finished!",
        "Job complete!",
        "Ready for next task!"
    ]


def get_tts_script_path():
    """
    Determine which TTS script to use based on available API keys.
    Priority order: ElevenLabs > OpenAI > pyttsx3
    """
    # Get current script directory and construct utils/tts path
    script_dir = Path(__file__).parent
    tts_dir = script_dir / "utils" / "tts"
    
    # Check for ElevenLabs API key (highest priority)
    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)
    
    # Check for OpenAI API key (second priority)
    if os.getenv('OPENAI_API_KEY'):
        openai_script = tts_dir / "openai_tts.py"
        if openai_script.exists():
            return str(openai_script)
    
    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)
    
    return None


def get_llm_completion_message():
    """
    Generate completion message using available LLM services.
    Priority order: OpenAI > Anthropic > fallback to random message
    
    Returns:
        str: Generated or fallback completion message
    """
    # Get current script directory and construct utils/llm path
    script_dir = Path(__file__).parent
    llm_dir = script_dir / "utils" / "llm"
    
    # Try OpenAI first (highest priority)
    if os.getenv('OPENAI_API_KEY'):
        oai_script = llm_dir / "oai.py"
        if oai_script.exists():
            try:
                result = subprocess.run([
                    "uv", "run", str(oai_script), "--completion"
                ], 
                capture_output=True,
                text=True,
                timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
    
    # Try Anthropic second
    if os.getenv('ANTHROPIC_API_KEY'):
        anth_script = llm_dir / "anth.py"
        if anth_script.exists():
            try:
                result = subprocess.run([
                    "uv", "run", str(anth_script), "--completion"
                ], 
                capture_output=True,
                text=True,
                timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
    
    # Fallback to random predefined message
    messages = get_completion_messages()
    return random.choice(messages)

def announce_completion():
    """Announce completion using the best available TTS service."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available
        
        # Get completion message (LLM-generated or fallback)
        completion_message = get_llm_completion_message()
        
        # Call the TTS script with the completion message
        subprocess.run([
            "uv", "run", tts_script, completion_message
        ], 
        capture_output=True,  # Suppress output
        timeout=10  # 10-second timeout
        )
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Fail silently if TTS encounters issues
        pass
    except Exception:
        # Fail silently for any other errors
        pass


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--chat', action='store_true', help='Copy transcript to chat.json')
        args = parser.parse_args()
        
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract required fields
        session_id = input_data.get("session_id", "")
        stop_hook_active = input_data.get("stop_hook_active", False)

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "stop.json")

        # Read existing log data or initialize empty list
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Handle --chat switch
        if args.chat and 'transcript_path' in input_data:
            transcript_path = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # Read .jsonl file and convert to JSON array
                chat_data = []
                try:
                    with open(transcript_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass  # Skip invalid lines
                    
                    # Write to logs/chat.json
                    chat_file = os.path.join(log_dir, 'chat.json')
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass  # Fail silently

        # Announce completion via TTS
        announce_completion()

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()



================================================
FILE: .claude/hooks/subagent_stop.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def get_tts_script_path():
    """
    Determine which TTS script to use based on available API keys.
    Priority order: ElevenLabs > OpenAI > pyttsx3
    """
    # Get current script directory and construct utils/tts path
    script_dir = Path(__file__).parent
    tts_dir = script_dir / "utils" / "tts"
    
    # Check for ElevenLabs API key (highest priority)
    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)
    
    # Check for OpenAI API key (second priority)
    if os.getenv('OPENAI_API_KEY'):
        openai_script = tts_dir / "openai_tts.py"
        if openai_script.exists():
            return str(openai_script)
    
    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)
    
    return None


def announce_subagent_completion():
    """Announce subagent completion using the best available TTS service."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available
        
        # Use fixed message for subagent completion
        completion_message = "Subagent Complete"
        
        # Call the TTS script with the completion message
        subprocess.run([
            "uv", "run", tts_script, completion_message
        ], 
        capture_output=True,  # Suppress output
        timeout=10  # 10-second timeout
        )
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Fail silently if TTS encounters issues
        pass
    except Exception:
        # Fail silently for any other errors
        pass


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--chat', action='store_true', help='Copy transcript to chat.json')
        args = parser.parse_args()
        
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract required fields
        session_id = input_data.get("session_id", "")
        stop_hook_active = input_data.get("stop_hook_active", False)

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "subagent_stop.json")

        # Read existing log data or initialize empty list
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Handle --chat switch (same as stop.py)
        if args.chat and 'transcript_path' in input_data:
            transcript_path = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # Read .jsonl file and convert to JSON array
                chat_data = []
                try:
                    with open(transcript_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass  # Skip invalid lines
                    
                    # Write to logs/chat.json
                    chat_file = os.path.join(log_dir, 'chat.json')
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass  # Fail silently

        # Announce subagent completion via TTS
        announce_subagent_completion()

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()


================================================
FILE: .claude/hooks/utils/llm/anth.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "anthropic",
#     "python-dotenv",
# ]
# ///

import os
import sys
from dotenv import load_dotenv


def prompt_llm(prompt_text):
    """
    Base Anthropic LLM prompting method using fastest model.

    Args:
        prompt_text (str): The prompt to send to the model

    Returns:
        str: The model's response text, or None if error
    """
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Fastest Anthropic model
            max_tokens=100,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt_text}],
        )

        return message.content[0].text.strip()

    except Exception:
        return None


def generate_completion_message():
    """
    Generate a completion message using Anthropic LLM.

    Returns:
        str: A natural language completion message, or None if error
    """
    engineer_name = os.getenv("ENGINEER_NAME", "").strip()

    if engineer_name:
        name_instruction = f"Sometimes (about 30% of the time) include the engineer's name '{engineer_name}' in a natural way."
        examples = f"""Examples of the style: 
- Standard: "Work complete!", "All done!", "Task finished!", "Ready for your next move!"
- Personalized: "{engineer_name}, all set!", "Ready for you, {engineer_name}!", "Complete, {engineer_name}!", "{engineer_name}, we're done!" """
    else:
        name_instruction = ""
        examples = """Examples of the style: "Work complete!", "All done!", "Task finished!", "Ready for your next move!" """

    prompt = f"""Generate a short, friendly completion message for when an AI coding assistant finishes a task. 

Requirements:
- Keep it under 10 words
- Make it positive and future focused
- Use natural, conversational language
- Focus on completion/readiness
- Do NOT include quotes, formatting, or explanations
- Return ONLY the completion message text
{name_instruction}

{examples}

Generate ONE completion message:"""

    response = prompt_llm(prompt)

    # Clean up response - remove quotes and extra formatting
    if response:
        response = response.strip().strip('"').strip("'").strip()
        # Take first line if multiple lines
        response = response.split("\n")[0].strip()

    return response


def main():
    """Command line interface for testing."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--completion":
            message = generate_completion_message()
            if message:
                print(message)
            else:
                print("Error generating completion message")
        else:
            prompt_text = " ".join(sys.argv[1:])
            response = prompt_llm(prompt_text)
            if response:
                print(response)
            else:
                print("Error calling Anthropic API")
    else:
        print("Usage: ./anth.py 'your prompt here' or ./anth.py --completion")


if __name__ == "__main__":
    main()



================================================
FILE: .claude/hooks/utils/llm/oai.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "openai",
#     "python-dotenv",
# ]
# ///

import os
import sys
from dotenv import load_dotenv


def prompt_llm(prompt_text):
    """
    Base OpenAI LLM prompting method using fastest model.

    Args:
        prompt_text (str): The prompt to send to the model

    Returns:
        str: The model's response text, or None if error
    """
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4.1-nano",  # Fastest OpenAI model
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=100,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return None


def generate_completion_message():
    """
    Generate a completion message using OpenAI LLM.

    Returns:
        str: A natural language completion message, or None if error
    """
    engineer_name = os.getenv("ENGINEER_NAME", "").strip()

    if engineer_name:
        name_instruction = f"Sometimes (about 30% of the time) include the engineer's name '{engineer_name}' in a natural way."
        examples = f"""Examples of the style: 
- Standard: "Work complete!", "All done!", "Task finished!", "Ready for your next move!"
- Personalized: "{engineer_name}, all set!", "Ready for you, {engineer_name}!", "Complete, {engineer_name}!", "{engineer_name}, we're done!" """
    else:
        name_instruction = ""
        examples = """Examples of the style: "Work complete!", "All done!", "Task finished!", "Ready for your next move!" """

    prompt = f"""Generate a short, friendly completion message for when an AI coding assistant finishes a task. 

Requirements:
- Keep it under 10 words
- Make it positive and future focused
- Use natural, conversational language
- Focus on completion/readiness
- Do NOT include quotes, formatting, or explanations
- Return ONLY the completion message text
{name_instruction}

{examples}

Generate ONE completion message:"""

    response = prompt_llm(prompt)

    # Clean up response - remove quotes and extra formatting
    if response:
        response = response.strip().strip('"').strip("'").strip()
        # Take first line if multiple lines
        response = response.split("\n")[0].strip()

    return response


def main():
    """Command line interface for testing."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--completion":
            message = generate_completion_message()
            if message:
                print(message)
            else:
                print("Error generating completion message")
        else:
            prompt_text = " ".join(sys.argv[1:])
            response = prompt_llm(prompt_text)
            if response:
                print(response)
            else:
                print("Error calling OpenAI API")
    else:
        print("Usage: ./oai.py 'your prompt here' or ./oai.py --completion")


if __name__ == "__main__":
    main()



================================================
FILE: .claude/hooks/utils/tts/elevenlabs_tts.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "elevenlabs",
#     "python-dotenv",
# ]
# ///

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """
    ElevenLabs Turbo v2.5 TTS Script
    
    Uses ElevenLabs' Turbo v2.5 model for fast, high-quality text-to-speech.
    Accepts optional text prompt as command-line argument.
    
    Usage:
    - ./eleven_turbo_tts.py                    # Uses default text
    - ./eleven_turbo_tts.py "Your custom text" # Uses provided text
    
    Features:
    - Fast generation (optimized for real-time use)
    - High-quality voice synthesis
    - Stable production model
    - Cost-effective for high-volume usage
    """
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ Error: ELEVENLABS_API_KEY not found in environment variables")
        print("Please add your ElevenLabs API key to .env file:")
        print("ELEVENLABS_API_KEY=your_api_key_here")
        sys.exit(1)
    
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play
        
        # Initialize client
        elevenlabs = ElevenLabs(api_key=api_key)
        
        print("🎙️  ElevenLabs Turbo v2.5 TTS")
        print("=" * 40)
        
        # Get text from command line argument or use default
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])  # Join all arguments as text
        else:
            text = "The first move is what sets everything in motion."
        
        print(f"🎯 Text: {text}")
        print("🔊 Generating and playing...")
        
        try:
            # Generate and play audio directly
            audio = elevenlabs.text_to_speech.convert(
                text=text,
                voice_id="WejK3H1m7MI9CHnIjW9K",  # Specified voice
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            
            play(audio)
            print("✅ Playback complete!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        
    except ImportError:
        print("❌ Error: elevenlabs package not installed")
        print("This script uses UV to auto-install dependencies.")
        print("Make sure UV is installed: https://docs.astral.sh/uv/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


================================================
FILE: .claude/hooks/utils/tts/openai_tts.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "openai",
#     "openai[voice_helpers]",
#     "python-dotenv",
# ]
# ///

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv


async def main():
    """
    OpenAI TTS Script

    Uses OpenAI's latest TTS model for high-quality text-to-speech.
    Accepts optional text prompt as command-line argument.

    Usage:
    - ./openai_tts.py                    # Uses default text
    - ./openai_tts.py "Your custom text" # Uses provided text

    Features:
    - OpenAI gpt-4o-mini-tts model (latest)
    - Nova voice (engaging and warm)
    - Streaming audio with instructions support
    - Live audio playback via LocalAudioPlayer
    """

    # Load environment variables
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please add your OpenAI API key to .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)

    try:
        from openai import AsyncOpenAI
        from openai.helpers import LocalAudioPlayer

        # Initialize OpenAI client
        openai = AsyncOpenAI(api_key=api_key)

        print("🎙️  OpenAI TTS")
        print("=" * 20)

        # Get text from command line argument or use default
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])  # Join all arguments as text
        else:
            text = "Today is a wonderful day to build something people love!"

        print(f"🎯 Text: {text}")
        print("🔊 Generating and streaming...")

        try:
            # Generate and stream audio using OpenAI TTS
            async with openai.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=text,
                instructions="Speak in a cheerful, positive yet professional tone.",
                response_format="mp3",
            ) as response:
                await LocalAudioPlayer().play(response)

            print("✅ Playback complete!")

        except Exception as e:
            print(f"❌ Error: {e}")

    except ImportError as e:
        print("❌ Error: Required package not installed")
        print("This script uses UV to auto-install dependencies.")
        print("Make sure UV is installed: https://docs.astral.sh/uv/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())



================================================
FILE: .claude/hooks/utils/tts/pyttsx3_tts.py
================================================
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pyttsx3",
# ]
# ///

import sys
import random

def main():
    """
    pyttsx3 TTS Script
    
    Uses pyttsx3 for offline text-to-speech synthesis.
    Accepts optional text prompt as command-line argument.
    
    Usage:
    - ./pyttsx3_tts.py                    # Uses default text
    - ./pyttsx3_tts.py "Your custom text" # Uses provided text
    
    Features:
    - Offline TTS (no API key required)
    - Cross-platform compatibility
    - Configurable voice settings
    - Immediate audio playback
    """
    
    try:
        import pyttsx3
        
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Configure engine settings
        engine.setProperty('rate', 180)    # Speech rate (words per minute)
        engine.setProperty('volume', 0.8)  # Volume (0.0 to 1.0)
        
        print("🎙️  pyttsx3 TTS")
        print("=" * 15)
        
        # Get text from command line argument or use default
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])  # Join all arguments as text
        else:
            # Default completion messages
            completion_messages = [
                "Work complete!",
                "All done!",
                "Task finished!",
                "Job complete!",
                "Ready for next task!"
            ]
            text = random.choice(completion_messages)
        
        print(f"🎯 Text: {text}")
        print("🔊 Speaking...")
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        
        print("✅ Playback complete!")
        
    except ImportError:
        print("❌ Error: pyttsx3 package not installed")
        print("This script uses UV to auto-install dependencies.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

