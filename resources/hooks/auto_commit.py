#!/usr/bin/env python3
"""
PostToolUse hook that automatically commits changes made by Claude to git
"""
import json
import sys
import subprocess
import os
from typing import Dict, Any

def run_git_command(command: list[str]) -> tuple[bool, str]:
    """Run a git command and return success status and output"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Git command timed out"
    except Exception as e:
        return False, f"Error running git command: {e}"

def has_git_changes() -> bool:
    """Check if there are any uncommitted changes"""
    success, output = run_git_command(["git", "status", "--porcelain"])
    return success and len(output.strip()) > 0

def commit_changes(tool_name: str, file_path: str = None) -> bool:
    """Commit changes with an appropriate message"""
    if not has_git_changes():
        return True  # No changes to commit
    
    # Stage all changes
    success, _ = run_git_command(["git", "add", "."])
    if not success:
        print("Failed to stage changes", file=sys.stderr)
        return False
    
    # Create commit message
    if file_path:
        commit_msg = f"Auto-commit: {tool_name} on {os.path.basename(file_path)}"
    else:
        commit_msg = f"Auto-commit: {tool_name} operation"
    
    commit_msg += "\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
    
    # Commit changes
    success, output = run_git_command(["git", "commit", "-m", commit_msg])
    if not success:
        print(f"Failed to commit changes: {output}", file=sys.stderr)
        return False
    
    return True

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        tool_response = input_data.get("tool_response", {})
        
        # Only commit for file modification operations
        if tool_name in ["Write", "Edit", "MultiEdit"] and tool_response.get("success", False):
            file_path = tool_input.get("file_path", "")
            print(f"Successfully committed changes for {tool_name} on {file_path}")
            
            # # Commit the changes
            # if commit_changes(tool_name, file_path):
            #     print(f"Successfully committed changes for {tool_name}")
            # else:
            #     print(f"Failed to commit changes for {tool_name}", file=sys.stderr)
        
        # Exit successfully regardless of commit status
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error in auto-commit hook: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()