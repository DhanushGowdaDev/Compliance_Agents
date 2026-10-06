<p align="center">
  <img src="assets/icon.png" alt="Open Swarm" width="128" height="128">
</p>

<h1 align="center">Open Swarm</h1>

<p align="center">
  <strong>An Army of AI Agents at Your Fingertips</strong>
  <br>
  A locally-running orchestrator for managing multiple AI agents in parallel.
  <br>
  Launch, monitor, and coordinate coding agents from a single interface.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="Platform"></a>
  <a href="https://github.com/openswarm-ai/openswarm/stargazers"><img src="https://img.shields.io/github/stars/openswarm-ai/openswarm?style=social" alt="GitHub Stars"></a>
  <a href="https://github.com/openswarm-ai/openswarm/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#contributing">Contributing</a>
</p>

<br>

<p align="center">
  <img src="assets/screenshot.png" alt="Open Swarm Dashboard" width="900">
</p>

---

## Why Open Swarm?

Running a single AI coding agent from a terminal is straightforward. The workflow becomes harder when several agents are working simultaneously across different tasks, branches, and repositories.

Open Swarm provides a single workspace for coordinating those agents.

- **Parallel agents, one workspace** — Run multiple agents simultaneously and organize them on a spatial dashboard.
- **Unified approvals** — Review tool-use requests from all agents from one interface.
- **Conversation control** — Edit messages, create branches, switch between conversations, and resume sessions.
- **Git isolation** — Each agent works in its own git worktree and branch.
- **Local-first** — Agents, conversations, configuration, and application data run locally on your machine.
- **Real-time monitoring** — Follow streaming responses, tool requests, status changes, and costs as they happen.

---

## Features

### Spatial Dashboard

An infinite canvas for organizing agent sessions, views, and browser cards.

- Drag and position cards freely
- Pan and zoom across the workspace
- Create multiple dashboards
- Organize agents by project or workflow

### Agent Chat

A real-time chat interface for interacting with coding agents.

- Streaming responses
- WebSocket communication
- Persistent conversation history
- Session cost tracking
- Resume previous sessions

### Human-in-the-Loop Approvals

Keep control over actions performed by agents.

- Approve or deny individual requests
- Batch-approve pending requests
- Configure permissions per tool
- Choose between always allow, ask, or deny

### Message Branching

Experiment with different approaches without losing the original conversation.

- Edit previous messages
- Create conversation branches
- Move between branches
- Resume previous paths

### Prompt Templates

Create reusable prompts for common workflows.

Templates can include structured input fields and can be invoked directly using `/` commands.

### Skills Library

Manage reusable agent skills from a dedicated interface.

Skills can be synchronized with:

```text
~/.claude/skills/
```

The library also provides access to available skills from the supported marketplace.

### Tools Library

Configure and manage MCP tools from one place.

Supported capabilities include:

- stdio MCP servers
- HTTP MCP servers
- SSE MCP servers
- Automatic tool discovery
- MCP registry browsing
- Google Workspace integration
- OAuth-based authentication

### Agent Modes

Open Swarm includes built-in modes for different workflows:

- Agent
- Ask
- Plan
- View Builder
- Skill Builder

Custom modes can also be created with configurable system prompts and tool permissions.

### Views & Outputs

Create interactive outputs using HTML, CSS, and JavaScript.

Supported workflows include:

- LLM-generated views
- Interactive HTML artifacts
- Python-backed outputs
- Automatically generated data
- Agent-driven data collection

### Git Worktree Isolation

Each agent can operate in an isolated git worktree and branch.

This allows multiple agents to work on different tasks without directly modifying the same working directory.

### Diff Viewer

Review changes made by agents directly from the application.

Inspect uncommitted work without switching between terminals or editors.

### Cost Tracking

Track estimated USD usage for individual agent sessions.

### Themes

Includes both dark and light themes using shared design tokens.

### Keyboard Shortcuts

Navigate the application and manage agent requests without relying entirely on the mouse.

---

## Quick Start

### Desktop App

Download the latest macOS release from:

[GitHub Releases](https://github.com/openswarm-ai/openswarm/releases)

> Windows and Linux builds are planned but are not currently available.

### Development Setup

#### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- macOS for the desktop application

Clone the repository:

```bash
git clone https://github.com/openswarm-ai/openswarm.git
cd openswarm
```

Start the application:

```bash
bash run.sh
```

This starts:

```text
Backend    → http://localhost:8324
Frontend   → http://localhost:3000
Electron   → Desktop shell
```

Once the application is running, configure your Anthropic API key through the in-app **Settings** page.

### Run Services Individually

Backend:

```bash
bash backend/run.sh
```

Frontend:

```bash
bash frontend/run.sh
```

Backend API documentation is available at:

```text
http://localhost:8324/docs
```

---

## Architecture

Open Swarm consists of an Electron desktop shell, a React frontend, and a FastAPI backend.

```text
┌─────────────────────────────────────────────────────────────┐
│                       Electron Shell                        │
│              Desktop wrapper + auto updater                 │
│                                                             │
│  ┌────────────────────────┐     ┌────────────────────────┐ │
│  │ Frontend               │     │ Backend                │ │
│  │ React / TypeScript     │◄───►│ FastAPI / Python       │ │
│  │                        │ WS  │                        │ │
│  │ Spatial Dashboard      │     │ REST API               │ │
│  │ Agent Chat             │     │ WebSocket              │ │
│  │ Templates              │     │ Agent Manager          │ │
│  │ Skills                 │     │ MCP Discovery          │ │
│  │ Tools                  │     │ Worktree Manager       │ │
│  │ Modes                  │     │ File Storage           │ │
│  │ Views                  │     │                        │ │
│  │ Settings               │     │ claude-agent-sdk       │ │
│  │                        │     │                        │ │
│  │ Redux Toolkit          │     │ JSON Storage            │ │
│  └────────────────────────┘     └────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Communication

The frontend communicates with the backend using:

- REST API for standard application operations
- WebSockets for streaming agent responses and real-time events

The backend manages agent sessions, worktrees, tools, skills, dashboards, and persistent application data.

---

## Configuration

The Anthropic API key can be configured through the application's **Settings** page.

For advanced configuration:

```bash
cp backend/.env.example backend/.env
```

| Variable | Purpose |
|---|---|
| `BACKEND_PORT` | Backend server port |
| `GOOGLE_OAUTH_CLIENT_ID` | Google Workspace integration |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google Workspace integration |
| `APPLE_ID` | macOS signing and notarization |
| `APPLE_APP_SPECIFIC_PASSWORD` | macOS notarization |
| `APPLE_TEAM_ID` | Apple code signing |
| `GH_TOKEN` | GitHub release publishing |

Release-related variables are only required when building and publishing desktop releases.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `D` | Open Dashboard |
| `T` | Open Templates |
| `1` – `9` | Open agent by position |
| `Shift + A` | Approve all pending requests |
| `Shift + D` | Deny all pending requests |
| `?` | Show keyboard shortcuts |

Use `/` in the chat input to access prompt templates and skills.

---

## Project Structure

```text
backend/
├── apps/
│   ├── agents/             Agent lifecycle and worktree management
│   ├── dashboards/         Dashboard CRUD
│   ├── dashboard_layout/   Canvas positions and layout state
│   ├── templates/          Prompt templates
│   ├── skills/             Skills management
│   ├── tools_lib/          MCP configuration and discovery
│   ├── modes/              Agent modes
│   ├── outputs/            Views, artifacts and Python execution
│   ├── settings/           Application settings
│   ├── health/             Health checks
│   ├── mcp_registry/       MCP registry integration
│   └── skill_registry/     Skills marketplace integration
│
├── config/                  FastAPI configuration
└── data/                    Persistent JSON storage

frontend/
└── src/
    ├── app/
    │   ├── components/      Shared application UI
    │   └── pages/
    │       ├── Dashboard/
    │       ├── AgentChat/
    │       ├── Templates/
    │       ├── Skills/
    │       ├── Tools/
    │       ├── Modes/
    │       ├── Views/
    │       ├── Commands/
    │       └── Settings/
    │
    └── shared/
        ├── state/           Redux state
        ├── ws/              WebSocket manager
        ├── hooks/           Custom hooks
        └── styles/          Theme and global styles

electron/
├── main.js                  Electron main process
└── scripts/                 Build and signing scripts

scripts/
├── build-app.sh             Desktop packaging
└── build-python-env.sh      Python runtime bundling
```

---

## Tech Stack

### Frontend

- React 18
- TypeScript
- Redux Toolkit
- Material UI
- CodeMirror 6
- Framer Motion
- React Router
- Webpack 5

### Backend

- FastAPI
- Python 3.11+
- Pydantic v2
- Claude Agent SDK
- Anthropic SDK
- WebSockets
- HTTPX

### Desktop

- Electron 33
- electron-builder
- electron-updater

### Runtime

Desktop releases bundle a standalone Python runtime so end users do not need to install Python separately.

---

## Security & Privacy

Open Swarm is designed around local execution.

Application data and agent sessions remain on the user's machine unless an external service is explicitly used by a configured tool or integration.

API credentials should never be committed to the repository.

For development, keep secrets in:

```text
backend/.env
```

and ensure that file remains excluded from version control.

---

## Troubleshooting

### Backend does not start

Check that the required Python version is installed:

```bash
python --version
```

Then verify that the backend dependencies are installed.

### Frontend does not start

Check the Node.js version:

```bash
node --version
```

Then reinstall dependencies if necessary.

### Port already in use

Check whether another process is using:

```text
8324
3000
```

Stop the conflicting process and restart Open Swarm.

### Agent authentication

Configure the Anthropic API key from:

```text
Settings → API / Provider Configuration
```

---

## Roadmap

### Current

- [x] Multi-agent dashboard
- [x] Agent streaming
- [x] Human-in-the-loop approvals
- [x] Git worktree isolation
- [x] Conversation branching
- [x] MCP tool support
- [x] Skills library
- [x] Prompt templates
- [x] Agent modes
- [x] Cost tracking
- [x] Desktop application

### Planned

- [ ] Windows support
- [ ] Linux support
- [ ] Additional agent providers
- [ ] Improved workspace management
- [ ] More MCP integrations
- [ ] Advanced agent analytics
- [ ] Expanded automation workflows

---

## Contributing

Contributions are welcome.

### Getting started

1. Fork the repository.
2. Clone your fork.
3. Create a feature branch.

```bash
git checkout -b feature/your-feature
```

4. Make your changes.
5. Test the affected functionality.
6. Commit your changes.
7. Push your branch.
8. Open a pull request.

For larger changes, open an issue first so the implementation can be discussed before development begins.

### Pull Requests

A good pull request should include:

- A clear description of the change
- The reason for the change
- Testing information
- Screenshots for UI changes when relevant
- Any known limitations

---

## License

Open Swarm is released under the MIT License.

See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Open Swarm</strong>
  <br>
  Run more agents. Keep control. Ship faster.
</p>
