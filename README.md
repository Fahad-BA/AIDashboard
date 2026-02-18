# 🤖 AIDashboard - Real-time Agent Monitoring System

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0-blue?style=for-the-badge&logo=github&logoColor=white" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11%2B-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge&logo=github&logoColor=white" alt="License">
  <img src="https://img.shields.io/badge/platform-linux-lightgrey?style=for-the-badge&logo=linux&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/vibe_coded-purple?style=for-the-badge&logo=sparkles&logoColor=white" alt="Vibe Coded">
</p>

<p align="center">
  <em>A comprehensive real-time monitoring system for all your OpenClaw agents with complete visibility and beautiful UI - Now vibe-coded!</em>
</p>

<p align="center">
  <a href="#-installation"><strong>🚀 Quick Start</strong></a> •
  <a href="#-features"><strong>✨ Features</strong></a> •
  <a href="#-dashboard-preview"><strong>📊 Dashboard</strong></a> •
  <a href="#-architecture"><strong>🏗️ Architecture</strong></a>
</p>

---

## 🎯 **About This Project**

**AIDashboard** is a sophisticated real-time monitoring system designed specifically for OpenClaw agents. It provides complete visibility into agent status, performance metrics, and system health through an intuitive and beautifully designed interface.

**🌟 Now Vibe-Coded:** This project has been meticulously crafted with attention to detail, modern aesthetics, and a focus on user experience - that's the essence of vibe-coding!

---

## ✨ Features

### 🤖 **Real-time Agent Monitoring**
- **Agent Status Tracking** 📊 - Idle, Working, Error, Offline states with beautiful indicators
- **Current Task Display** 🎯 - Real-time visibility into what each agent is working on
- **Performance Metrics** ⚡ - CPU, Memory, Response Time monitoring
- **Channel Communication** 💬 - Track which channels agents are communicating on
- **Agent Avatars** 👤 - Personal profile pictures for each agent

### 🖥️ **Server Performance Metrics**
- **CPU Usage Monitor** 📈 - Real-time processor utilization with charts
- **Memory Usage Tracking** 💾 - RAM consumption monitoring with alerts
- **Disk Usage Display** 💿 - Storage space monitoring and predictions
- **Load Average Indicators** ⚖️ - System load with historical trends
- **Active Connections** 🔗 - Network connections tracking and management

### 🎨 **Agent Customization**
- **Custom Nicknames** 🏷️ - Give agents friendly names (e.g., "أبومساعد", "مساعد الصغير")
- **Professional Titles** 👔 - Assign custom titles (e.g., "كبير الوكلاء", "خبير التطوير")
- **Avatar Upload** 🖼️ - Upload custom profile pictures for each agent
- **Real-time Updates** ⚡ - All changes appear immediately across all sessions

### 💻 **Interactive Interface**
- **Live WebSocket Updates** 🔄 - Real-time data streaming without page refresh
- **Beautiful Agent Cards** 🎴 - Modern card-based interface with animations
- **Color-coded Status Badges** 🎨 - Intuitive visual status indicators
- **Visual Progress Bars** 📊 - Performance metrics with smooth animations
- **Easy Edit Modal** ✏️ - Intuitive agent customization interface

---

## 📁 **Directory Structure**

```bash
~/AIDB/
├── app.py                 # Main Quart application (async web framework)
├── start_dashboard.sh     # Startup script (one-click deployment)
├── README.md              # This file (vibe-coded documentation)
├── static/                # Static assets
│   ├── img/              # Agent avatars & images
│   │   └── default-agent.png
│   └── css/               # Custom styling & themes
├── templates/             # HTML templates
│   └── dashboard.html     # Main dashboard interface
├── agents/                # Agent data & configurations
├── api/                   # REST API routes
├── utils/                 # Utility functions & helpers
└── aidashboard.db         # SQLite database (agent data)
```

---

## 🚀 **Quick Start**

### 📋 **Prerequisites**
```bash
# Python 3.11+ (required)
python3 --version

# Git (for cloning)
git --version

# System packages (Ubuntu/Debian)
sudo apt update
sudo apt install python3-pip
```

### 🛠️ **Installation**

1. **Navigate to the project directory**
```bash
cd /home/fahad/AIDB
```

2. **Start the dashboard**
```bash
./start_dashboard.sh
```

3. **Access the dashboard**
Open your browser and navigate to: `http://localhost:5000`

4. **Explore the features**
- 📊 View real-time agent status
- 🖥️ Monitor server performance  
- 🎨 Customize agent profiles
- 📈 Track agent activities

### 🔧 **Configuration**

The dashboard automatically detects agents from your OpenClaw configuration:

```bash
# Configuration file location
~/.openclaw/agents/openclaw.json

# Database file
~/AIDB/aidashboard.db
```

---

## 🎨 **Custom Agent Configuration**

### **Agent Personalization**
You can customize each agent with beautiful profiles:

- **🏷️ Nicknames**: Friendly names (e.g., "أبومساعد", "مساعد الصغير")
- **👔 Titles**: Professional titles (e.g., "كبير الوكلاء", "خبير التطوير")
- **🖼️ Avatars**: Custom profile picture URLs
- **📊 Real-time Updates**: All changes sync instantly

### **Database Management**
- **SQLite Storage**: Lightweight and fast database
- **Auto-backup**: Automatic data persistence
- **Migration Support**: Easy schema updates
- **Location**: `~/AIDB/aidashboard.db`

---

## 📊 **Agent Status Reference**

| Status | Color | Icon | Description |
|--------|-------|------|-------------|
| **Idle** | 🟢 Green | ✅ | Agent is available and ready for tasks |
| **Working** | 🟡 Yellow | ⚡ | Agent is actively processing a task |
| **Error** | 🔴 Red | ❌ | Agent has encountered an error |
| **Offline** | ⚫ Gray | 💤 | Agent is not responding or disconnected |

---

## 🎮 **Usage Examples**

### 📱 **Monitoring Agents**
1. **Open Dashboard**: Launch your browser and navigate to `http://localhost:5000`
2. **View Status**: See beautiful agent cards with real-time status indicators
3. **Customize Profiles**: Click "Edit" to personalize agent information
4. **Live Updates**: Watch as agent statuses change in real-time

### ✨ **Customizing Agent Profiles**
1. **Select Agent**: Click on any agent card to open customization options
2. **Enter Details**: Add friendly nicknames and professional titles
3. **Upload Avatar**: Add custom profile pictures for visual identification
4. **Save Changes**: All updates sync instantly across the interface

### 📈 **Server Performance Monitoring**
- **🖥️ Resource Usage**: Monitor CPU, Memory, and Disk utilization
- **📊 System Metrics**: Track load average and performance trends
- **🔗 Connection Tracking**: View active network connections
- **⚠️ Performance Alerts**: Identify bottlenecks before they become issues

---

## 🔄 **Real-time Technology**

### WebSocket Implementation**
The dashboard uses cutting-edge WebSocket technology for seamless real-time updates:

- **⚡ Lightning Fast**: 2-second refresh intervals for live data
- **🔄 Auto-reconnect**: Automatic connection recovery if network drops
- **📱 Cross-platform**: Works on all modern browsers and devices
- **🛡️ Fallback Support**: Graceful degradation to API calls when needed
- **📊 Efficient Updates**: Minimal bandwidth usage with delta updates

---

## 🏗️ **Architecture**

### **System Overview**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │────│   Quart Backend │────│   SQLite DB    │
│  (Bootstrap 5)  │    │   (Async API)   │    │ (aidashboard.db)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                │
                    ┌─────────────────┐
                    │  OpenClaw Agents│
                    │  (Monitoring)   │
                    └─────────────────┘
```

### **Backend Stack**
- **🚀 Quart Framework**: Async Flask for high-performance web applications
- **💾 SQLite Database**: Lightweight, fast, and reliable data storage
- **🔌 WebSocket**: Real-time bidirectional communication
- **📊 psutil Library**: Comprehensive system and process utilities
- **🛡️ Security**: Built-in authentication and authorization

### **Frontend Stack**
- **🎨 Bootstrap 5**: Modern, responsive UI framework
- **✨ Font Awesome**: Beautiful icons and visual elements
- **🌐 RTL Support**: Full Arabic language support
- **⚡ Vanilla JavaScript**: Fast, lightweight interactivity
- **📱 Responsive Design**: Works perfectly on all devices

### **📡 API Endpoints**
```bash
GET  /                 # Main dashboard interface
GET  /api/agents       # Retrieve all agents data
GET  /api/metrics      # Get server performance metrics
POST /api/agent/<id>/update  # Update agent profile
GET  /api/agent/<id>/status  # Get specific agent status
WS   /ws               # WebSocket for real-time updates
```

---

## 🚀 **Future Enhancements**

### **🎯 Planned Features**
- **📈 Historical Analytics**: Agent performance trends over time
- **🔔 Smart Alert System**: Intelligent notifications for agent issues
- **💬 Agent Chat Interface**: Direct communication with agents
- **📋 Visual Task Queue**: Beautiful task management interface
- **📊 Advanced Reports**: Detailed analytics and export capabilities
- **📱 Mobile Applications**: Native iOS and Android apps
- **🌙 Dark Mode**: Eye-friendly dark theme
- **👥 Multi-user System**: User authentication and role management
- **🎨 Custom Themes**: Personalized dashboard themes

### **🔌 Integration Roadmap**
- **🤖 OpenClaw Deep Integration**: Direct agent communication protocols
- **💬 Telegram Monitoring**: Enhanced chat monitoring capabilities
- **📊 System Metrics**: Advanced performance monitoring
- **🌐 API Gateway**: Centralized API management system
- **🔍 AI Insights**: Intelligent agent behavior analysis

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

#### **🚫 Dashboard Won't Start**
```bash
# Check Python version (3.11+ required)
python3 --version

# Install missing dependencies
pip3 install quart aiohttp psutil

# Check port availability
netstat -tulpn | grep :5000
```

#### **🤖 Agents Not Showing**
- **Check Configuration**: Verify `~/.openclaw/agents/openclaw.json`
- **Agent Status**: Ensure agents are running and accessible
- **Restart Dashboard**: `./start_dashboard.sh` to reload configurations
- **Check Logs**: View console output for error messages

#### **⚡ Real-time Updates Not Working**
- **WebSocket Check**: Open browser console (F12) for connection errors
- **Network Connectivity**: Verify your network connection is stable
- **Browser Compatibility**: Try Chrome/Firefox/Edge for best results
- **Refresh Page**: Sometimes a simple page refresh fixes the issue

#### **💾 Database Errors**
```bash
# Reset database (backup first if needed)
rm aidashboard.db

# Restart dashboard (auto-recreates database)
./start_dashboard.sh
```

---

## 🛠️ **Development**

### **🤝 Contributing**
We welcome contributions! Here's how to get started:

1. **Fork the Repository**
```bash
git clone <repository-url>
cd AIDB
```

2. **Create a Feature Branch**
```bash
git checkout -b feature/amazing-feature
```

3. **Make Your Changes**
4. **Test Thoroughly**
```bash
# Test the dashboard
./start_dashboard.sh

# Open http://localhost:5000
```

5. **Submit a Pull Request**

### **🐛 Debug Mode**
```bash
# Enable debug logging
export DEBUG=true

# Run with verbose output
python3 app.py --debug
```

---

## 📜 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **OpenClaw Team** for the amazing agent framework
- **Quart Framework** for the async web capabilities
- **Bootstrap 5** for the beautiful UI components
- **Font Awesome** for the stunning icons
- **psutil** for comprehensive system monitoring

---

## 📧 **Contact & Support**

**Developer**: Fahad Alhuqaili

- 🐦 **Twitter/X**: [@falhuqaili](https://twitter.com/falhuqaili)
- 💼 **LinkedIn**: [/in/fahad-alhuqaili](https://linkedin.com/in/fahad-alhuqaili)
- 📧 **Email**: [Fahad@Alhuqaili.com](mailto:Fahad@Alhuqaili.com)
- 🤖 **Telegram**: For direct support and inquiries

---

## ⭐ **Star This Project**

If you find this project useful, please consider giving it a star! Your support helps me continue developing and maintaining this tool.

[![Star History Chart](https://api.star-history.com/svg?repos=Fahad-BA/AIDashboard&type=Date)](https://star-history.com/#Fahad-BA/AIDashboard&Date)

---

<p align="center">
  <em>Made with ❤️ by Fahad Alhuqaili | Now Vibe-Coded ✨</em>
</p>