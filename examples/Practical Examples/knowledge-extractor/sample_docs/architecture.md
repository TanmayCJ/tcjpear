# System Architecture

## Component Overview

The system is built with a modular architecture:

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       v
┌─────────────┐
│   Router    │──────> Selects appropriate agent
└──────┬──────┘
       │
       v
┌─────────────┐
│   Agents    │──────> Technical, Creative, General
└──────┬──────┘
       │
       v
┌─────────────┐
│   Memory    │──────> Stores conversation history
└─────────────┘
```

## Key Design Decisions

1. **Modularity**: Each component is independent
2. **Extensibility**: Easy to add new agents
3. **Memory Management**: Configurable history size
4. **Routing**: Smart agent selection based on context

## Data Flow

1. User provides input
2. Router analyzes and selects agent
3. Agent processes with memory context
4. Response returned to user
5. History updated in memory

## Dependencies

- agents.py: Core agent implementations
- memory.py: Memory management
- router.py: Routing logic
- config.yaml: System configuration

See `setup.txt` for installation details.
