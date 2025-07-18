# TypeScript/JavaScript Coding Rules

## Types
- **No `any`** - use `unknown` then narrow with type guards
- **Explicit returns** on exported functions
- **Interfaces for objects**, type aliases for unions/tuples
- **No `I` prefix** on interfaces (use `User` not `IUser`)

## Code Style
- **`const` by default**, `let` if value changes, never `var`
- **`===` always**, except `== null` to check null/undefined
- **Named functions** for declarations, arrows for callbacks
- **Named exports only** - no default exports

## Errors
- **Every async needs try/catch**
- **Throw `Error` objects**, not strings
- **No empty catches** - handle or rethrow

## Imports
- **ES6 imports only** - no require()
- **Explicit paths** - no assuming index files
- **Order**: external libs first, then internal

## Components
- **Single responsibility** - one purpose per component
- **Composition over inheritance**
- **Props interface required** for all components