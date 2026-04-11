# Documentation

This directory intentionally stays small. Keep durable project facts here and avoid adding one-off notes that repeat the same bringup history.

## Standard Docs

- [architecture.md](architecture.md): hardware split, ROS graph, serial protocol, sensor ownership, and known risks
- [RUNBOOK.md](RUNBOOK.md): build, launch, smoke-test, capture, and troubleshooting commands
- [VALIDATION.md](VALIDATION.md): confirmed hardware/runtime checkpoints and remaining validation limits
- [WEB_CONSOLE.md](WEB_CONSOLE.md): browser console behavior, API scope, capture workflow, and operator safety notes

## Documentation Rules

- Put operator commands in `RUNBOOK.md`.
- Put verified runtime facts in `VALIDATION.md`.
- Put system design and interfaces in `architecture.md`.
- Put web UI/API details in `WEB_CONSOLE.md`.
- Do not create a new docs file unless it has a distinct long-term purpose.
