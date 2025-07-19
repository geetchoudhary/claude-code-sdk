---
description: Execute the implementation plan from /plan-task by working through all checklist items systematically
allowed-tools:
  - Read
  - Write
  - MultiEdit
  - Edit
  - Bash
  - Grep
  - Glob
  - LS
  - TodoWrite
  - Task
  - WebFetch
  - WebSearch
---

# /implement-task - Execute Implementation Plan

This command takes the output from `/plan-task` and systematically implements it by working through all the checklist items.

## What it does:

1. **Parses the implementation plan** to extract all checklist items
2. **Creates a todo list** from the implementation checklist
3. **Works through each item** systematically, marking progress
4. **Runs tests and validation** after implementation
5. **Provides a summary** of what was completed

## Usage:

### Option 1: Provide the plan directly
```
/implement-task
[paste the implementation plan from /plan-task here]
```

### Option 2: Reference a plan file
```
/implement-task from-file implementation-plan.md
```

### Option 3: Continue from a partial implementation
```
/implement-task continue
```

## Implementation Strategy:

1. **Parse Plan**: Extract all checklist items from the provided plan
2. **Create Todo List**: Convert checklist to TodoWrite items with priorities
3. **Implementation Loop**:
   - Pick next pending task
   - Mark as in_progress
   - Implement the task
   - Run validation (type-check, lint if applicable)
   - Mark as completed
   - Move to next task

4. **Quality Checks**: After core implementation:
   - Run type checking
   - Run relevant tests
   - Check for console errors
   - Validate against requirements

5. **Final Summary**: Provide:
   - What was implemented
   - Any issues encountered
   - Remaining tasks (if any)
   - Next recommended steps

## Special Features:

- **Intelligent Implementation**: Understands dependencies between tasks
- **Error Recovery**: If a task fails, logs the issue and continues with others
- **Progress Tracking**: Uses TodoWrite to show real-time progress
- **Validation**: Runs appropriate checks after each major step
- **Resumable**: Can continue from where it left off

## Example Workflow:

```bash
# Step 1: Define and plan your task
/create-task
# Answer the questions...

# Step 2: Create detailed plan
/plan-task Create a user authentication system with JWT

# Step 3: Implement the plan
/implement-task
[paste the plan output here]
```

## Notes:

- The command will ask for confirmation before making significant changes
- It will create backups of files before major modifications
- Progress is tracked in the todo list for transparency
- You can interrupt and resume the implementation at any time

$ARGUMENTS