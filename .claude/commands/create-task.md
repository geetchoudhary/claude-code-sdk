---
description: Interactive task definition assistant that analyzes your codebase and asks targeted questions to create comprehensive task specifications
allowed-tools:
  - Read
  - Grep
  - Glob
  - LS
  - Task
---

# /create-task - Interactive Task Definition Assistant

This command helps you create comprehensive task specifications by analyzing your codebase and asking targeted questions.

## Phase 1: Automatic Codebase Analysis

When you run this command, I'll first analyze your project to understand:

### Technical Environment
- **Framework**: Next.js 15.0.0 with App Router
- **Language**: TypeScript 5.3.3 (strict mode)
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand stores in `/src/stores`
- **API Client**: Custom client in `/src/lib/api-client.ts`
- **Testing**: Vitest for unit tests, Playwright for E2E
- **Package Manager**: pnpm with Turbo monorepo

### Code Patterns Detected
- **Components**: Functional components with TypeScript interfaces
- **File Structure**: Feature-based organization
- **Naming**: PascalCase components, camelCase utilities
- **Error Handling**: Toast notifications via `useToast`
- **Forms**: React Hook Form + Zod validation
- **Routing**: Next.js App Router with layouts

### Available Resources
- **UI Components**: Button, Card, Dialog, Dropdown from `@nextjs-monorepo/ui`
- **Utilities**: cn() for className merging, API utilities
- **Hooks**: useToast, custom auth hooks
- **Icons**: Lucide React icons

---

## Phase 2: Interactive Questions

I'll ask you these questions to understand your specific needs:

### Question 1: What are you building?
**What I need:** Component/feature name and brief description  
**Example:** "NotificationCenter - A dropdown component to display and manage user notifications"

---

### Question 2: Why are we building this?
**What I need:** The problem it solves and user story  
**Format:** As a [user type], I want to [action] so that [benefit]  
**Example:** "Users miss important updates. As a user, I want to see all my notifications in one place so that I can stay informed."

---

### Question 3: What are the core features?
**What I need:** List of must-have functionality (I'll suggest common patterns)  
**Example:**
- View list of notifications
- Mark as read/unread
- Filter by type (info, warning, error)
- Click to navigate to source
- Clear all notifications

---

### Question 4: Do you have design specifications?
**What I need:** Links to designs or describe the UI  
**Example:** "Figma: https://figma.com/file/xyz123 - Notification dropdown in top nav"  
**Note:** I can also work from descriptions if no designs exist

---

### Question 5: Where does the data come from?
**What I need:** API endpoints or data source  
**What I'll check:** Existing API patterns in your codebase  
**Example:** 
```
GET /api/notifications - List notifications
POST /api/notifications/:id/read - Mark as read
DELETE /api/notifications/:id - Dismiss
```

---

### Question 6: What's explicitly OUT of scope?
**What I need:** Boundaries to prevent scope creep  
**Example:**
- Email notification preferences (future phase)
- Push notifications
- Notification scheduling
- Admin management panel

---

### Question 7: How do we measure success?
**What I need:** Acceptance criteria and metrics  
**What I'll add:** Standard requirements from your codebase  
**Example:**
- All notifications load within 200ms
- Keyboard navigation works (Tab, Enter, Escape)
- Works on mobile devices
- No console errors

---

### Question 8: Any special requirements?
**What I need:** Business logic, security, localization  
**Example:**
- Admin notifications highlighted differently
- Sensitive data masked in preview
- Support existing i18n languages (EN, ES, FR, DE, PT, ZH, JA)

---

### Question 9: What's the priority/timeline?
**What I need:** Urgency and dependencies  
**Example:** "High priority - blocks dashboard redesign. Needed by end of sprint (Dec 20)"

---

### Question 10: Any examples to follow?
**What I need:** Reference implementations  
**What I'll find:** Similar patterns in your codebase  
**Example:** "Similar to Slack's notification dropdown" or "Follow our MessageCenter pattern"

---

## Phase 3: Generated Task Format

After gathering information, I'll generate a comprehensive task specification including:

```markdown
# Task: [Your Component Name]

## 1. Context & Problem Statement
[Business context, user story, success metrics]

## 2. Technical Environment
[Auto-filled from codebase analysis]

## 3. Detailed Requirements
### Functional Requirements
[Core features with specifics]

### Non-Functional Requirements
[Performance, accessibility, browser support]

## 4. Data & API Specifications
[Endpoints, schemas, error handling]

## 5. UI/UX Specifications
[Design links, states, animations]

## 6. Implementation Guidelines
### File Structure
[Where files should be created]

### Code Patterns to Follow
[Existing patterns to reuse]

### Dependencies & Imports
[What to use/avoid]

## 7. Testing Requirements
[Unit, integration, E2E test scenarios]

## 8. Definition of Done
[Checklist of completion criteria]

## 9. Out of Scope
[What NOT to build]

## 10. References & Examples
[Similar code in the codebase]
```

---

## How to Use This Command

1. Type `/create-task` in your message
2. I'll analyze your codebase and show what I found
3. I'll ask only the questions I need answered
4. You can answer questions one at a time or all at once
5. I'll generate a complete task specification
6. Use the specification to implement the feature

## Tips for Best Results

- **Be specific** about user interactions and edge cases
- **Include examples** when describing functionality
- **Reference existing components** you want to match
- **Specify what NOT to do** to avoid scope creep
- **Link to designs** when available

Ready to create a well-defined task? Just type `/create-task` to begin!