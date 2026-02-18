# AIDashboard - Real-time Agent Monitoring System

## 🎯 What is AIDashboard?

AIDashboard is a comprehensive real-time monitoring system for all your OpenClaw agents. It provides complete visibility into agent status, performance metrics, and system health.

## 🚀 Features

### **Real-time Agent Monitoring**
- **Agent Status**: Idle, Working, Error, Offline
- **Current Tasks**: What each agent is working on
- **Performance Metrics**: CPU, Memory, Response Time
- **Channel Information**: Which channels agents are communicating on
- **Agent Avatars**: Personal profile pictures for each agent

### **Server Performance Metrics**
- **CPU Usage**: Real-time processor utilization
- **Memory Usage**: RAM consumption monitoring
- **Disk Usage**: Storage space monitoring
- **Load Average**: System load indicators
- **Active Connections**: Network connections tracking

### **Agent Customization**
- **Nicknames**: Give agents custom names (e.g., "أبومساعد", "مساعد الصغير")
- **Titles**: Assign custom titles (e.g., "كبير الوكلاء", "خبير التطوير")
- **Avatars**: Upload custom profile pictures for each agent
- **Real-time Updates**: All changes appear immediately

### **Interactive Interface**
- **Live Updates**: Real-time WebSocket updates
- **Agent Cards**: Beautiful card-based interface
- **Status Indicators**: Color-coded status badges
- **Progress Bars**: Visual performance indicators
- **Edit Modal**: Easy agent customization

## 📁 Directory Structure

```
~/AIDB/
├── app.py                 # Main Quart application
├── start_dashboard.sh     # Startup script
├── README.md              # This file
├── static/                # Static files
│   ├── img/              # Agent avatars
│   │   └── default-agent.png
│   └── css/               # Custom CSS
├── templates/             # HTML templates
│   └── dashboard.html     # Main dashboard
├── agents/                # Agent data
├── api/                   # API routes
├── utils/                 # Utility functions
└── aidashboard.db         # SQLite database
```

## 🚀 Getting Started

### **1. Start the Dashboard**
```bash
cd /home/fahad/AIDB
./start_dashboard.sh
```

### **2. Access the Dashboard**
Open your browser and go to: `http://localhost:5000`

### **3. Explore the Features**
- View real-time agent status
- Monitor server performance
- Customize agent profiles
- Track agent activities

## 🔧 Configuration

### **Default Agent Setup**
The dashboard automatically detects agents from your OpenClaw configuration at `~/.openclaw/agents/openclaw.json`.

### **Custom Agent Names**
You can customize each agent with:
- **Nickname**: A friendly name (e.g., "أبومساعد")
- **Title**: Professional title (e.g., "كبير الوكلاء")
- **Avatar**: Custom profile picture URL

### **Database Configuration**
The dashboard uses SQLite for data storage. Database file is located at `~/AIDB/aidashboard.db`.

## 📊 Agent Status Meanings

| Status | Color | Description |
|--------|-------|-------------|
| **Idle** | 🟢 Green | Agent is available and ready |
| **Working** | 🟡 Yellow | Agent is processing a task |
| **Error** | 🔴 Red | Agent has an error |
| **Offline** | ⚫ Gray | Agent is not responding |

## 🎮 Usage Examples

### **Monitoring Agents**
1. Open the dashboard in your browser
2. View agent cards showing current status
3. Click "Edit" to customize agent profiles
4. Watch real-time updates as agents work

### **Customizing Agent Profiles**
1. Click the "Edit" button on any agent card
2. Enter the desired nickname and title
3. Add an avatar URL (optional)
4. Click "Save Changes"

### **Server Performance**
- Monitor CPU, Memory, and Disk usage
- Track system load average
- View active connections
- Identify performance bottlenecks

## 🔄 Real-time Updates

The dashboard uses WebSocket technology for real-time updates:
- **2-second refresh interval** by default
- **Automatic reconnection** if connection drops
- **Fallback to API calls** if WebSocket fails

## 🛠️ Technical Details

### **Backend**
- **Framework**: Quart (async Flask)
- **Database**: SQLite
- **Real-time**: WebSocket
- **Monitoring**: psutil library

### **Frontend**
- **Styling**: Bootstrap 5
- **Icons**: Font Awesome
- **Language**: Arabic (RTL support)
- **Updates**: Real-time JavaScript

### **API Endpoints**
- `GET /` - Main dashboard
- `GET /api/agents` - Get all agents data
- `GET /api/metrics` - Get server metrics
- `POST /api/agent/<id>/update` - Update agent profile
- `GET /api/agent/<id>/status` - Get specific agent status
- `WS /ws` - WebSocket for real-time updates

## 🎯 Future Enhancements

### **Planned Features**
- **Historical Data**: Agent performance over time
- **Alert System**: Notifications for agent issues
- **Agent Chat**: Direct communication with agents
- **Task Queue**: Visual task management
- **Performance Reports**: Detailed analytics
- **Mobile App**: iOS and Android support
- **Dark Mode**: UI theme switching
- **Export Data**: CSV/JSON export functionality
- **Multi-user**: User authentication and roles

### **Integration Options**
- **OpenClaw Integration**: Direct agent communication
- **Telegram Integration**: Chat monitoring
- **System Monitoring**: Enhanced metrics
- **API Gateway**: Centralized API management

## 🔍 Troubleshooting

### **Common Issues**

**Dashboard won't start**
```bash
# Check Python version
python3 --version

# Install missing dependencies
pip3 install quart aiohttp psutil

# Check port availability
netstat -tulpn | grep :5000
```

**Agents not showing**
- Check OpenClaw configuration at `~/.openclaw/agents/openclaw.json`
- Ensure agents are properly configured
- Restart the dashboard

**Real-time updates not working**
- Check WebSocket connection in browser console
- Verify network connectivity
- Refresh the page

**Database errors**
- Remove database file: `rm aidashboard.db`
- Restart dashboard (will recreate database)

## 📞 Support

For issues, feature requests, or contributions:
1. Check the troubleshooting section
2. Review the configuration
3. Test with different browsers
4. Check console for errors

---

**Built with ❤️ for OpenClaw Agent Management**
*Real-time monitoring for intelligent agents*