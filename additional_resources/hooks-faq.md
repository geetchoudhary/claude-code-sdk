 

You can use Claude Code hooks to automatically commit changes after tool executions. Here are the main approaches:

## PostToolUse Hook for Automatic Commits

You can create a `PostToolUse` hook that runs after file modifications to automatically commit changes[(1)](https://docs.anthropic.com/en/docs/claude-code/hooks#security-considerations). Here's how to configure it:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "git add . && git commit -m 'Auto-commit: Changes made by Claude'"
          }
        ]
      }
    ]
  }
}
```
[(1)](https://docs.anthropic.com/en/docs/claude-code/hooks#security-considerations)

## Stop Hook for End-of-Session Commits

You can also use a `Stop` hook that runs when Claude finishes responding to commit all changes made during the session[(1)](https://docs.anthropic.com/en/docs/claude-code/hooks#security-considerations):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "git add . && git commit -m 'Session complete: All changes by Claude'"
          }
        ]
      }
    ]
  }
}
```
[(1)](https://docs.anthropic.com/en/docs/claude-code/hooks#security-considerations)

## Configuration Steps

1. Run the `/hooks` slash command in Claude Code[(2)](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)
2. Select the appropriate hook event (`PostToolUse` or `Stop`)[(2)](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)
3. Add your matcher pattern (e.g., `Edit|MultiEdit|Write` for file operations)[(2)](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)
4. Enter your git commit command[(2)](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)
5. Save to your desired settings location[(2)](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)

## Important Considerations

- **Security**: Hooks execute automatically with your credentials, so review commands carefully before adding them[(1)](https://docs.anthropic.com/en/docs/claude-code/hooks#security-considerations)
- **Pre-commit hooks**: If you have pre-commit hooks that modify files, you may need to handle the case where files are changed after staging[(3)](https://github.com/anthropics/claude-code/issues/1000)
- **Selective staging**: Consider whether you want to commit all changes or only specific files modified by Claude[(1)](https://docs.anthropic.com/en/docs/claude-code/hooks#security-considerations)

The hooks will execute automatically whenever Claude performs the matched operations, ensuring your changes are committed without manual intervention[(1)](https://docs.anthropic.com/en/docs/claude-code/hooks#security-considerations).