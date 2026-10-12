# Open Swarm

**Parallel AI Agent Orchestration. One Unified Workspace.**

Open Swarm is a local-first desktop application for orchestrating multiple AI coding agents in parallel. It provides a unified environment for agent execution, human-in-the-loop approvals, conversation management, and isolated development workflows.

Built for developers who need visibility, control, and coordination across concurrent AI-assisted tasks.

<p align="center">
  <img src="assets/icon.png" alt="Open Swarm" width="88" />
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2563EB?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Platform-macOS-555555?style=flat-square" alt="macOS" />
  <img src="https://img.shields.io/badge/Frontend-React%20%7C%20TypeScript-3178C6?style=flat-square" alt="React and TypeScript" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square" alt="FastAPI" />
  <a href="https://github.com/openswarm-ai/openswarm/stargazers"><img src="https://img.shields.io/github/stars/openswarm-ai/openswarm?style=flat-square" alt="GitHub stars" /></a>
  <a href="https://github.com/openswarm-ai/openswarm/pulls"><img src="https://img.shields.io/badge/Contributions-Welcome-16A34A?style=flat-square" alt="Contributions welcome" /></a>
</p>

<p align="center">
  <a href="#key-capabilities">Capabilities</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#getting-started">Get started</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

## Overview

As AI coding agents become capable of handling increasingly complex tasks, coordinating them effectively becomes a challenge of its own. Separate terminals, fragmented conversations, competing file changes, and scattered approval requests make parallel execution difficult to manage.

Open Swarm brings these workflows into a single desktop environment.

The application combines a spatial workspace, real-time agent communication, centralized permission management, and Git worktree isolation to make multi-agent development more observable and manageable.

<p align="center">
  <img src="assets/screenshot.png" alt="Open Swarm application dashboard" width="100%" />
</p>

## Design principles

| Principle | Implementation |
|---|---|
| Local-first | Run the application locally without a cloud relay or third-party application backend. |
| Human oversight | Review tool requests and configure permission policies before agent actions proceed. |
| Parallel execution | Coordinate multiple agents through a shared workspace. |
| Workspace isolation | Use Git worktrees and separate branches for independent agent tasks. |
| Operational visibility | Inspect agent conversations, pending approvals, code changes, and session costs. |

## Key capabilities

### Workspace orchestration

A spatial canvas provides a unified view of concurrent work.

- Arrange agent cards, view cards, and embedded browser cards.
- Navigate an expandable workspace with pan and zoom.
- Maintain separate dashboards for different workspaces.
- Monitor multiple agent sessions from one interface.

### Agent interaction and control

Manage agent conversations throughout the development lifecycle.

- Stream responses in real time over WebSockets.
- Persist conversation history across restarts.
- Edit previous messages and navigate conversation branches.
- Resume closed sessions.
- Track costs per agent session.

### Permission management

Keep developers in control of agent tool execution.

- Review approval requests in a centralized interface.
- Approve or deny individual requests.
- Batch-approve pending requests.
- Configure per-tool policies: `Always Allow`, `Ask`, or `Deny`.

### Isolated development workflows

Support concurrent engineering tasks with independent Git worktrees.

- Maintain separate branches for individual agents.
- Reduce interference between parallel workstreams.
- Inspect uncommitted changes through the integrated diff viewer.

### Extensible agent environment

Configure reusable instructions, tools, and execution modes.

| Component | Capabilities |
|---|---|
| Prompt templates | Structured inputs and `/` slash commands |
| Skills library | Skill management and synchronization with `~/.claude/skills/` |
| MCP integration | stdio, HTTP, and SSE transports; tool discovery |
| Agent modes | Agent, Ask, Plan, View Builder, and Skill Builder |
| Custom modes | Configurable system prompts and tool restrictions |
| Interactive outputs | HTML, CSS, JavaScript, iframe rendering, and backend Python execution |
| Workspace integrations | Google Workspace OAuth support |

### Developer experience

- Dark and light themes with centralized design tokens.
- Keyboard-driven navigation and approval workflows.
- Persistent application settings.
- Real-time USD cost tracking.
- Interactive views and agent-generated outputs.

## Architecture

Open Swarm separates the desktop shell, user interface, backend services, and agent integrations.

```text
┌──────────────────────────────────────────────────────────┐
│                     Electron Shell                       │
│             Desktop lifecycle and updates                │
├───────────────────────────┬──────────────────────────────┤
│         Frontend          │           Backend            │
│                           │                              │
│  React + TypeScript       │  FastAPI                     │
│  Redux Toolkit            │  Agent Manager               │
│  Spatial Dashboard        │  REST API                    │
│  Agent Chat               │  WebSocket Services          │
│  Templates & Skills       │  MCP Tool Discovery          │
│  Modes & Interactive Views│  Persistent JSON Storage     │
│                           │                              │
└───────────────────────────┴──────────────────────────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
          Agent SDK / MCP       Local Workspaces
```

### Frontend

The frontend manages the interactive workspace, application state, and user-facing workflows.

- React 18 and TypeScript
- Redux Toolkit
- Material UI v7
- Framer Motion
- CodeMirror 6
- React Router v7
- Webpack 5

### Backend

The backend provides application APIs, agent lifecycle management, and integration services.

- FastAPI and Python
- Pydantic v2
- Anthropic SDK and `claude-agent-sdk`
- REST APIs and WebSockets
- HTTPX
- MCP discovery and configuration
- JSON-based persistence

### Desktop runtime

Electron provides the desktop application shell, with packaging and update support through the Electron ecosystem. The project also includes scripts for bundling a standalone Python runtime.

## Getting started

### Requirements

| Dependency | Minimum version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Git | Installed and available in `PATH` |

### 1. Clone the repository

```bash
git clone https://github.com/openswarm-ai/openswarm.git
cd openswarm
```

### 2. Launch the application

```bash
bash run.sh
```

The startup script launches the backend, frontend, and Electron shell together.

### 3. Access the services

| Service | Address |
|---|---|
| Backend API | `http://localhost:8324` |
| API documentation | `http://localhost:8324/docs` |
| Frontend | `http://localhost:3000` |

### 4. Configure credentials

Open the application and navigate to **Settings** to configure your Anthropic API key.

### Run services individually

Backend:

```bash
bash backend/run.sh
```

Frontend:

```bash
bash frontend/run.sh
```

### Desktop releases

macOS builds are documented as available through the project's [GitHub Releases](https://github.com/openswarm-ai/openswarm/releases). Windows and Linux desktop builds are planned but are not yet available according to the current documentation.

## Configuration

For normal application usage, configure the Anthropic API key through the in-app Settings page.

For advanced configuration, create a local environment file:

```bash
cp backend/.env.example backend/.env
```

| Variable | Purpose |
|---|---|
| `BACKEND_PORT` | Backend port; defaults to `8324` |
| `GOOGLE_OAUTH_CLIENT_ID` | Google Workspace OAuth integration |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google Workspace OAuth integration |
| `APPLE_ID` | macOS signing and notarization |
| `APPLE_APP_SPECIFIC_PASSWORD` | macOS notarization |
| `APPLE_TEAM_ID` | macOS code signing |
| `GH_TOKEN` | GitHub Releases publishing |

Apple signing and publishing variables are relevant to release workflows. Never commit API keys, OAuth secrets, or populated environment files.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `D` | Open Dashboard |
| `T` | Open Templates |
| `1`–`9` | Open an agent by position |
| `Shift + A` | Approve all pending requests |
| `Shift + D` | Deny all pending requests |
| `?` | Display keyboard shortcuts |

Enter `/` in the chat input to access prompt templates and skills through slash commands.

## Repository structure

```text
openswarm/
├── backend/
│   ├── apps/
│   │   ├── agents/
│   │   ├── dashboards/
│   │   ├── dashboard_layout/
│   │   ├── templates/
│   │   ├── skills/
│   │   ├── tools_lib/
│   │   ├── modes/
│   │   ├── outputs/
│   │   ├── settings/
│   │   ├── health/
│   │   ├── mcp_registry/
│   │   └── skill_registry/
│   ├── config/
│   └── data/
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── components/
│       │   └── pages/
│       └── shared/
│           ├── state/
│           ├── ws/
│           ├── hooks/
│           └── styles/
├── electron/
│   ├── main.js
│   └── scripts/
├── scripts/
├── assets/
├── LICENSE
└── README.md
```

| Directory | Responsibility |
|---|---|
| `backend/apps/agents/` | Agent lifecycle, streaming, and worktree management |
| `backend/apps/dashboards/` | Dashboard CRUD and persistence |
| `backend/apps/tools_lib/` | MCP tool configuration and discovery |
| `backend/apps/outputs/` | Interactive outputs and Python execution |
| `backend/data/` | Persistent JSON storage |
| `frontend/src/app/` | Application components and pages |
| `frontend/src/shared/` | State, WebSocket management, hooks, and styles |
| `electron/` | Desktop main process and packaging scripts |
| `scripts/` | Application and Python runtime build scripts |

## Contributing

Contributions that improve reliability, usability, performance, documentation, or extensibility are welcome.

### Development workflow

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Commit with a descriptive message.
5. Open a pull request explaining the motivation, implementation, and relevant testing.

```bash
git checkout -b feature/your-feature
git add .
git commit -m "feat: describe your change"
git push origin feature/your-feature
```

For substantial changes, open an issue first to discuss the proposed approach.

Useful starting points include documentation improvements, accessibility, test coverage, error handling, agent management, and developer onboarding.

- [Report an issue](https://github.com/openswarm-ai/openswarm/issues)
- [Review open pull requests](https://github.com/openswarm-ai/openswarm/pulls)
- [Explore the repository](https://github.com/openswarm-ai/openswarm)

## License

Open Swarm is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <strong>Open Swarm</strong><br />
  One workspace. Multiple agents. Greater control.
</p>
