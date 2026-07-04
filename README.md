# 📊 AIDashboard — Real-Time AI Agent Monitoring System

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Quart](https://img.shields.io/badge/Quart-async-black?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey?logo=linux&logoColor=white)

A real-time monitoring dashboard for OpenClaw AI agents. Track agent status, server performance, task distribution, and workload — all from a single web interface with live WebSocket updates.

---

## ✨ Features

- 🤖 **Agent Monitoring** — Real-time status of every agent (idle, working, error, offline)
- 📈 **Server Metrics** — CPU, memory, disk, load average, uptime, and active connections
- 🎯 **Task Distribution** — Automatic task assignment with per-agent queues and priority levels
- ⚖️ **Workload Balancing** — Tracks concurrent tasks, max capacity, and overload prevention
- 🎨 **Agent Personalization** — Custom names, nicknames, titles, and avatars per agent
- 📡 **Live Updates** — WebSocket-based real-time refresh (2-second intervals)
- 🏥 **Health Monitoring** — Automated health reports and performance sync scripts
- 🗄️ **SQLite Backend** — Lightweight database with full schema for agents, tasks, and metrics

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3** | Core runtime |
| **Quart** | Async web framework (Flask-compatible) |
| **SQLite** | Agent, task, and metrics storage |
| **psutil** | System performance metrics |
| **aiohttp** | Async HTTP client for agent communication |
| **WebSocket** | Real-time dashboard updates |
| **systemd** | Production process management |

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- An [OpenClaw](https://github.com/openclaw) setup with configured agents

### Steps

```bash
# Clone the repo
git clone https://github.com/Fahad-BA/AIDashboard.git
cd AIDashboard

# Install dependencies
pip install quart aiohttp psutil

# Create required directories
mkdir -p /home/fahad/AIDB/static/img
mkdir -p /home/fahad/AIDB/templates

# Copy templates and static assets
cp templates/* /home/fahad/AIDB/templates/
cp -r static/* /home/fahad/AIDB/static/

# Run the dashboard
python3 app.py
```

The dashboard will be available at `http://localhost:5000`.

---

## 🚀 Usage

### Start the Dashboard

```bash
./start_dashboard.sh          # Basic dashboard (app.py)
./start_enhanced_dashboard.sh # Enhanced with task distribution
```

### Run as a systemd Service

```bash
sudo systemctl restart aidashboard
sudo systemctl status aidashboard
```

Use the included `restart.sh` script for quick restarts:

```bash
sudo ./restart.sh
```

### Task Distribution System

The enhanced dashboard (`enhanced_dashboard.py`) integrates with `agent_task_system.py` to provide:

- Per-agent task queues with configurable concurrency (default: 3)
- Priority-based assignment (High / Medium / Low)
- Dependency tracking between tasks
- Automatic timeout handling (5-minute default)
- Real-time progress tracking (0–100%)

---

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `agents` | Agent profiles: name, model, status, workspace, avatar, resource usage |
| `tasks` | Task records: agent assignment, progress, status, timestamps |
| `server_metrics` | Historical server performance snapshots |
| `agent_customizations` | User-defined nicknames, titles, and avatars |
| `agent_tasks` | Enhanced task queue with priority, dependencies, and results |

See [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) for full SQL definitions.

---

## 📁 Project Structure

```
AIDashboard/
├── app.py                     # Main dashboard application (Quart)
├── enhanced_dashboard.py      # Extended dashboard with task distribution
├── agent_task_system.py       # Task queue & workload management engine
├── init_agents.py             # Initialize agent records
├── setup_avatars.py           # Download / configure agent avatars
├── sync_performance_data.py   # Sync metrics from OpenClaw agents
├── monitor_dashboard.sh       # Process monitoring script
├── start_dashboard.sh         # Startup script (basic)
├── start_enhanced_dashboard.sh# Startup script (enhanced)
├── restart.sh                 # systemd restart helper
├── templates/                 # Jinja2 HTML templates
│   ├── dashboard.html
│   └── enhanced_dashboard.html
├── static/                    # Static assets (CSS, JS, images)
├── agents/                    # Agent backup & health scripts
├── DATABASE_SCHEMA.md         # Full SQL schema documentation
└── .gitignore
```

---

## 📝 License

This project is licensed under the MIT License.
