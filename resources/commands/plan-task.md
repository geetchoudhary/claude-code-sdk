---
description: Comprehensive task planning assistant that performs deep analysis to create detailed implementation plans with actionable checklists
allowed-tools:
  - Read
  - Grep
  - Glob
  - LS
  - Task
  - TodoWrite
---

# /plan-task - Comprehensive Task Planning Assistant

This command performs deep analysis of your task and codebase to create a detailed implementation plan with actionable checklists.

## How It Works

When you run `/plan-task`, I will:

### Phase 1: Deep Task Analysis
1. **Understand the Requirements**
   - Break down the task into atomic components
   - Identify all explicit and implicit requirements
   - Map out user journeys and edge cases
   - Define success criteria and constraints

2. **Analyze Technical Context**
   - Scan relevant parts of the codebase
   - Identify existing patterns to follow
   - Find reusable components and utilities
   - Understand data flow and dependencies

3. **Research Best Practices**
   - Consider multiple implementation approaches
   - Evaluate trade-offs (performance, maintainability, complexity)
   - Check for security implications
   - Consider scalability and future extensions

### Phase 2: Solution Design
1. **Architecture Planning**
   - Component structure and hierarchy
   - State management approach
   - Data flow design
   - API integration patterns

2. **Technical Decisions**
   - Choose appropriate libraries/tools
   - Define interfaces and types
   - Plan error handling strategy
   - Design testing approach

3. **Implementation Strategy**
   - Optimal order of implementation
   - Dependency management
   - Risk mitigation
   - Parallel work opportunities

### Phase 3: Comprehensive Checklist Generation

The output will include:

#### 1. **Pre-Implementation Checklist**
- [ ] Verify all dependencies are installed
- [ ] Ensure understanding of requirements
- [ ] Review existing similar implementations
- [ ] Set up necessary environment/config

#### 2. **Core Implementation Checklist**
Organized by priority and dependencies:
- [ ] Create file structure
- [ ] Implement core logic
- [ ] Add UI components
- [ ] Integrate with APIs
- [ ] Handle edge cases
- [ ] Add loading/error states

#### 3. **Quality Assurance Checklist**
- [ ] Unit tests for business logic
- [ ] Integration tests for API calls
- [ ] UI/UX testing
- [ ] Accessibility compliance
- [ ] Performance optimization
- [ ] Security review

#### 4. **Final Review Checklist**
- [ ] Code follows project patterns
- [ ] Documentation updated
- [ ] No TypeScript errors
- [ ] Linting passes
- [ ] Bundle size acceptable
- [ ] Cross-browser testing

## Output Format

```markdown
# Implementation Plan: [Task Name]

## 🎯 Task Overview
[Concise summary of what needs to be built]

## 🔍 Requirements Analysis
### Functional Requirements
- [Detailed list of features]

### Non-Functional Requirements
- [Performance, security, accessibility needs]

### Edge Cases & Considerations
- [Special scenarios to handle]

## 🏗️ Technical Architecture

### Component Structure
```
feature/
├── components/
│   ├── MainComponent.tsx
│   └── SubComponent.tsx
├── hooks/
│   └── useFeature.ts
└── utils/
    └── helpers.ts
```

### State Management Plan
[How data will flow through the application]

### API Integration
[Endpoints, request/response handling]

## 🛠️ Implementation Approach

### Phase 1: Foundation (2 hours)
- [ ] Set up file structure
- [ ] Create type definitions
- [ ] Implement basic component shell

### Phase 2: Core Features (4 hours)
- [ ] Build main functionality
- [ ] Integrate with APIs
- [ ] Add state management

### Phase 3: Polish (2 hours)
- [ ] Add loading/error states
- [ ] Implement animations
- [ ] Optimize performance

### Phase 4: Testing (1 hour)
- [ ] Write unit tests
- [ ] Test edge cases
- [ ] Cross-browser check

## ⚠️ Potential Challenges
1. **Challenge**: [Description]
   **Solution**: [Approach to handle it]

## 📋 Complete Implementation Checklist

### Prerequisites
- [ ] Dependencies verified
- [ ] Environment configured
- [ ] Design assets available

### Implementation
- [ ] File structure created
- [ ] Types/interfaces defined
- [ ] Core component built
- [ ] State management implemented
- [ ] API integration complete
- [ ] Form validation working
- [ ] Error handling in place
- [ ] Loading states added
- [ ] Animations implemented
- [ ] Responsive design verified

### Testing
- [ ] Unit tests written
- [ ] Integration tests complete
- [ ] Manual testing done
- [ ] Accessibility tested
- [ ] Performance verified

### Code Quality
- [ ] TypeScript errors resolved
- [ ] Linting passes
- [ ] Code reviewed
- [ ] Patterns followed
- [ ] Documentation updated

### Deployment Ready
- [ ] Build successful
- [ ] Bundle size checked
- [ ] Console errors cleared
- [ ] Feature flags configured
- [ ] Rollback plan ready

## 🚀 Estimated Timeline
- Total: ~9 hours
- Can be parallelized: Yes (UI and API work)
- Critical path: API integration → UI → Testing

## 📝 Notes & Recommendations
- [Any special considerations]
- [Optimization opportunities]
- [Future enhancement ideas]
```

## Usage Examples

### Example 1: Complex Feature
```
/plan-task Create a real-time collaborative editing feature for documents
```

### Example 2: Refactoring Task
```
/plan-task Refactor the authentication system to use JWT tokens instead of sessions
```

### Example 3: Performance Task
```
/plan-task Optimize the dashboard to load in under 2 seconds
```

## Benefits of Using /plan-task

1. **Reduces Implementation Time** - Clear roadmap prevents false starts
2. **Improves Code Quality** - Considers patterns and best practices upfront
3. **Catches Edge Cases** - Thorough analysis identifies potential issues
4. **Enables Better Estimation** - Detailed breakdown helps with time planning
5. **Facilitates Collaboration** - Checklist can be shared with team
6. **Documents Decisions** - Reasoning is captured for future reference

## Tips for Best Results

- **Be Specific**: The more detail you provide, the better the plan
- **Include Constraints**: Mention deadlines, performance requirements, etc.
- **Reference Examples**: Point to similar features you want to emulate
- **State Assumptions**: Clarify any assumptions about the task
- **Define Success**: What does "done" look like?

Ready to plan your implementation thoroughly? Type `/plan-task` followed by your task description!