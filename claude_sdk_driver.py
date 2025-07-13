import anyio
import sys
from pathlib import Path
from claude_code_sdk import (
    query, 
    ClaudeCodeOptions, 
    Message,
    AssistantMessage,
    TextBlock,
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError,
    ResultMessage
)
from typing import Literal, Optional

# Type alias for permission modes
PermissionMode = Literal["default", "acceptEdits", "bypassPermissions"]

PROJECT_ROOT = Path("/Users/mastergeet/Repos/claude_test")

# Configuration for Claude Code
opts = ClaudeCodeOptions(
    cwd=PROJECT_ROOT,                       # give Claude full FS access
    allowed_tools=["Read", "Task", "Write", "LS"],
    permission_mode="acceptEdits",          # auto-approve edits
    max_turns=8                             # stop runaway loops per query
)

# Store session ID for conversation continuity
session_id = None

# Permission modes
PERMISSION_MODES = {
    "interactive": "Use MCP permission prompt tool for interactive approvals",
    "default": "Use Claude Code's default permission system",
    "acceptEdits": "Auto-approve file edits only",
    "bypassPermissions": "Bypass all permission checks (dangerous!)",
    "skip": "Same as bypassPermissions"
}

def get_mcp_config():
    """Get MCP configuration from mcp-servers.json"""
    mcp_config_path = Path(__file__).parent / "mcp-servers.json"
    if mcp_config_path.exists():
        import json
        with open(mcp_config_path) as f:
            return json.load(f)
    return None

async def run_query(prompt: str, resume_session: str | None = None, 
                   permission_mode: str = "default", use_mcp: bool = False):
    """Execute a query and return the session ID for continuity"""
    global session_id
    current_session_id = None
    
    # Configure options with session resumption if available
    query_opts = ClaudeCodeOptions(
        cwd=opts.cwd,
        allowed_tools=opts.allowed_tools,
        permission_mode=permission_mode if permission_mode in ["default", "acceptEdits", "bypassPermissions"] else "default",  # type: ignore
        max_turns=opts.max_turns,
        resume=resume_session if resume_session else None
    )
    
    # Add permission prompt tool if using MCP
    if use_mcp and permission_mode == "interactive":
        # Load MCP configuration
        mcp_config = get_mcp_config()
        if not mcp_config:
            print("\nError: mcp-servers.json not found")
            print("Falling back to default permission mode")
            query_opts = ClaudeCodeOptions(
                cwd=opts.cwd,
                allowed_tools=opts.allowed_tools,
                permission_mode="default",  # type: ignore
                max_turns=opts.max_turns,
                resume=resume_session if resume_session else None
            )
        else:
            print("Using MCP servers")
            # Recreate options with permission prompt tool and MCP servers
            query_opts = ClaudeCodeOptions(
                cwd=opts.cwd,
                allowed_tools=opts.allowed_tools,
                permission_mode=None,  # Let MCP tool handle permissions  # type: ignore
                max_turns=opts.max_turns,
                resume=resume_session if resume_session else None,
                permission_prompt_tool_name="mcp__approval-server__permissions__approve",
                mcp_servers=mcp_config.get("mcpServers", {})
            )
    
    try:
        async for m in query(prompt=prompt, options=query_opts):
            if isinstance(m, Message):
                # Pretty print the message
                if isinstance(m, AssistantMessage):
                    for block in m.content:
                        if isinstance(block, TextBlock):
                            print(f"\n{block.text}")
                else:
                    print(f"\n{m}")
                
            # Capture session ID from result messages
            if isinstance(m, ResultMessage) and hasattr(m, 'session_id'):
                current_session_id = m.session_id
        
        return current_session_id
    
    except CLINotFoundError:
        print("\nError: Claude Code CLI not found. Please install it with:")
        print("  npm install -g @anthropic-ai/claude-code")
        return None
    except ProcessError as e:
        print(f"\nError: Process failed with exit code {e.exit_code}")
        return None
    except ClaudeSDKError as e:
        print(f"\nError: {e}")
        return None
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return None

async def interactive_loop():
    """Run an interactive loop for continuous conversation"""
    global session_id
    
    # Ask user for permission mode
    print("\nSelect permission mode:")
    print("1. Interactive (MCP-based) - Prompt for each tool use")
    print("2. Default - Use Claude Code's built-in prompts")
    print("3. Accept Edits - Auto-approve file edits only")
    print("4. Bypass - Skip all permissions (dangerous!)")
    
    mode_choice = input("\nChoice [1-4, default=2]: ").strip() or "2"
    
    permission_mode = "default"
    use_mcp = False
    
    if mode_choice == "1":
        permission_mode = "interactive"
        use_mcp = True
        print("\n✅ Using MCP-based interactive permissions")
    elif mode_choice == "2":
        permission_mode = "default"
        print("\n✅ Using default Claude Code permissions")
    elif mode_choice == "3":
        permission_mode = "acceptEdits"
        print("\n✅ Auto-approving file edits only")
    elif mode_choice == "4":
        permission_mode = "bypassPermissions"
        print("\n⚠️  WARNING: Bypassing all permissions!")
    
    print("\nClaude Code Interactive Loop")
    print("=" * 40)
    print(f"Working directory: {PROJECT_ROOT}")
    print(f"Permission mode: {permission_mode}")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'new' to start a fresh conversation")
    print("Type 'mode' to change permission mode")
    print("=" * 40)
    
    while True:
        try:
            # Get user input
            prompt = input("\n> ").strip()
            
            # Check for exit commands
            if prompt.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            # Check for new session command
            if prompt.lower() == 'new':
                session_id = None
                print("\nStarting new conversation...")
                continue
            
            # Check for mode change command
            if prompt.lower() == 'mode':
                print("\nSelect new permission mode:")
                print("1. Interactive (MCP-based)")
                print("2. Default")
                print("3. Accept Edits")
                print("4. Bypass")
                
                new_mode = input("Choice [1-4]: ").strip()
                if new_mode == "1":
                    permission_mode = "interactive"
                    use_mcp = True
                elif new_mode == "2":
                    permission_mode = "default"
                    use_mcp = False
                elif new_mode == "3":
                    permission_mode = "acceptEdits"
                    use_mcp = False
                elif new_mode == "4":
                    permission_mode = "bypassPermissions"
                    use_mcp = False
                
                print(f"\n✅ Permission mode changed to: {permission_mode}")
                continue
            
            # Skip empty prompts
            if not prompt:
                continue
            
            # Run the query with session continuation
            print("\nProcessing...")
            new_session_id = await run_query(prompt, resume_session=session_id, 
                                           permission_mode=permission_mode, use_mcp=use_mcp)
            
            # Update session ID if we got a new one
            if new_session_id:
                session_id = new_session_id
                print(f"\n[Session: {session_id[:8]}...]")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit or continue with a new prompt.")
        except Exception as e:
            print(f"\nError in loop: {e}")

async def main():
    """Main entry point"""
    try:
        if len(sys.argv) > 1:
            # Parse command line arguments
            args = sys.argv[1:]
            permission_mode = "default"
            use_mcp = False
            
            # Check for --permission flag
            if "--permission" in args:
                idx = args.index("--permission")
                if idx + 1 < len(args):
                    mode = args[idx + 1]
                    if mode == "interactive":
                        permission_mode = "interactive"
                        use_mcp = True
                    elif mode in ["default", "acceptEdits", "bypassPermissions", "skip"]:
                        permission_mode = mode
                    args = args[:idx] + args[idx+2:]  # Remove flag and value
            
            # Run single query
            prompt = " ".join(args)
            print(f"Running single query: {prompt}")
            print(f"Permission mode: {permission_mode}")
            await run_query(prompt, permission_mode=permission_mode, use_mcp=use_mcp)
        else:
            # Otherwise, run interactive loop
            await interactive_loop()
    finally:
        pass  # MCP servers are managed externally

if __name__ == "__main__":
    anyio.run(main)
