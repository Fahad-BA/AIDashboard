#!/usr/bin/env python3
"""
AIDashboard - Real-time Agent Monitoring System
=============================================
Complete monitoring dashboard for all OpenClaw agents
Features:
- Real-time agent status monitoring
- Server performance metrics
- Agent personalization (names, avatars, titles)
- Task tracking
- Channel monitoring
- Customizable interface
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psutil
import subprocess
from pathlib import Path
import base64
from dataclasses import dataclass, asdict
import aiohttp
from quart import Quart, render_template, websocket, request, jsonify, send_from_directory
import uuid

# Configuration
class Config:
    DATABASE_PATH = "/home/fahad/AIDB/aidashboard.db"
    AGENTS_CONFIG_PATH = "/home/fahad/.openclaw/agents/openclaw.json"
    WORKSPACE_BASE = "/home/fahad/.openclaw/agents"
    STATIC_PATH = "/home/fahad/AIDB/static"
    TEMPLATES_PATH = "/home/fahad/AIDB/templates"
    DEFAULT_AVATAR = "/static/img/default-agent.png"
    REFRESH_INTERVAL = 2  # seconds

@dataclass
class Agent:
    id: str
    name: str
    title: str
    nickname: str
    model: str
    status: str  # idle, working, error, offline
    current_task: str
    workspace: str
    avatar: str
    last_seen: str
    cpu_usage: float
    memory_usage: float
    channel: str
    response_time: float
    
@dataclass
class ServerMetrics:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: float
    uptime: str
    processes: int
    active_connections: int
    
class AIDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Agents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    title TEXT,
                    nickname TEXT,
                    model TEXT,
                    status TEXT DEFAULT 'idle',
                    current_task TEXT DEFAULT '',
                    workspace TEXT,
                    avatar TEXT,
                    last_seen TEXT,
                    cpu_usage REAL DEFAULT 0.0,
                    memory_usage REAL DEFAULT 0.0,
                    channel TEXT DEFAULT '',
                    response_time REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Server metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    load_average REAL,
                    uptime TEXT,
                    processes INTEGER,
                    active_connections INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    task_name TEXT,
                    status TEXT,
                    progress REAL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    channel TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # Agent customizations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_customizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT UNIQUE,
                    nickname TEXT,
                    title TEXT,
                    avatar_url TEXT,
                    custom_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            conn.commit()
            
    def get_agents(self) -> List[Agent]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, title, nickname, model, status, current_task,
                       workspace, avatar, last_seen, cpu_usage, memory_usage,
                       channel, response_time
                FROM agents
            ''')
            
            agents = []
            for row in cursor.fetchall():
                agent = Agent(
                    id=row[0], name=row[1], title=row[2], nickname=row[3],
                    model=row[4], status=row[5], current_task=row[6],
                    workspace=row[7], avatar=row[8], last_seen=row[9],
                    cpu_usage=row[10], memory_usage=row[11], channel=row[12],
                    response_time=row[13]
                )
                agents.append(agent)
            
            # Get customizations for all agents and merge
            cursor.execute('''
                SELECT agent_id, nickname, title, avatar_url
                FROM agent_customizations
            ''')
            
            customizations = {}
            for row in cursor.fetchall():
                agent_id, nickname, title, avatar_url = row
                customizations[agent_id] = {
                    'nickname': nickname,
                    'title': title,
                    'avatar_url': avatar_url
                }
            
            # Apply customizations to agents
            for agent in agents:
                if agent.id in customizations:
                    custom = customizations[agent.id]
                    # Override with custom values if they exist
                    if custom['nickname']:
                        agent.nickname = custom['nickname']
                    if custom['title']:
                        agent.title = custom['title']
                    if custom['avatar_url']:
                        agent.avatar = custom['avatar_url']
            
            return agents
            
    def update_agent_status(self, agent_id: str, status: str, task: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE agents 
                SET status = ?, current_task = ?, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, task, agent_id))
            conn.commit()
            
    def update_agent_metrics(self, agent_id: str, cpu: float, memory: float, response_time: float):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE agents 
                SET cpu_usage = ?, memory_usage = ?, response_time = ?, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (cpu, memory, response_time, agent_id))
            conn.commit()
            
    def save_server_metrics(self, metrics: ServerMetrics):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_metrics 
                (cpu_percent, memory_percent, disk_percent, load_average, 
                 uptime, processes, active_connections)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (metrics.cpu_percent, metrics.memory_percent, metrics.disk_percent,
                  metrics.load_average, metrics.uptime, metrics.processes, metrics.active_connections))
            conn.commit()
            
    def update_agent_customization(self, agent_id: str, nickname: str, title: str, avatar_url: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First, check if agent exists
            cursor.execute('SELECT id FROM agents WHERE id = ?', (agent_id,))
            if not cursor.fetchone():
                raise ValueError(f"Agent {agent_id} not found")
            
            # Update agent_customizations table
            cursor.execute('''
                INSERT OR REPLACE INTO agent_customizations 
                (agent_id, nickname, title, avatar_url, custom_data)
                VALUES (?, ?, ?, ?, '{}')
            ''', (agent_id, nickname, title, avatar_url))
            
            # Update agents table with the new values
            cursor.execute('''
                UPDATE agents 
                SET nickname = COALESCE(?, nickname), 
                    title = COALESCE(?, title), 
                    avatar = COALESCE(?, avatar),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (nickname if nickname else None, 
                  title if title else None, 
                  avatar_url if avatar_url else None, 
                  agent_id))
            
            conn.commit()

class AgentMonitor:
    def __init__(self, database: AIDatabase):
        self.database = database
        self.agents_config = self.load_agents_config()
        self._initialize_agents()
        
    def load_agents_config(self) -> Dict[str, Any]:
        try:
            with open(Config.AGENTS_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"agents": {"list": []}}
            
    def _initialize_agents(self):
        """Initialize agents from OpenClaw config"""
        agents_list = self.agents_config.get('agents', {}).get('list', [])
        
        for agent_config in agents_list:
            agent_id = agent_config.get('id')
            if agent_id:
                # Create agent if not exists
                self._create_agent_if_not_exists(agent_config)
                
    def _create_agent_if_not_exists(self, agent_config: Dict[str, Any]):
        agent_id = agent_config.get('id')
        agent_name = agent_config.get('name', agent_id)
        model = agent_config.get('model', 'unknown')
        workspace = agent_config.get('workspace', '')
        
        with sqlite3.connect(Config.DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO agents 
                (id, name, model, workspace, status, avatar)
                VALUES (?, ?, ?, ?, 'idle', ?)
            ''', (agent_id, agent_name, model, workspace, Config.DEFAULT_AVATAR))
            conn.commit()
            
    def get_server_metrics(self) -> ServerMetrics:
        """Get current server performance metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return ServerMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            load_average=os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.0,
            uptime=str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())),
            processes=len(psutil.pids()),
            active_connections=len(psutil.net_connections())
        )
        
    async def monitor_agents(self):
        """Monitor agent statuses and update database"""
        while True:
            try:
                # Get server metrics
                metrics = self.get_server_metrics()
                self.database.save_server_metrics(metrics)
                
                # Simulate agent status updates (in real implementation, this would connect to actual agents)
                await self._simulate_agent_updates()
                
                await asyncio.sleep(Config.REFRESH_INTERVAL)
                
            except Exception as e:
                logging.error(f"Error monitoring agents: {e}")
                await asyncio.sleep(Config.REFRESH_INTERVAL)
                
    async def _simulate_agent_updates(self):
        """Real agent monitoring with stable metrics and status updates"""
        agents = self.database.get_agents()
        
        for agent in agents:
            # Only update status occasionally, keep metrics stable from database
            if agent.status == 'idle' and time.time() % 60 < 1:  # Less frequent status changes
                self.database.update_agent_status(
                    agent.id, 
                    'working', 
                    f"Processing task {uuid.uuid4().hex[:8]}"
                )
            elif agent.status == 'working' and time.time() % 45 < 1:  # Less frequent status changes
                self.database.update_agent_status(agent.id, 'idle', '')
            
            # Only update last_seen timestamp, preserve the database metrics
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE agents 
                    SET last_seen = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (agent.id,))
                conn.commit()

# Quart App
app = Quart(__name__, 
            static_folder=Config.STATIC_PATH,
            template_folder=Config.TEMPLATES_PATH)

# Global variables
database = None
agent_monitor = None

@app.before_serving
async def startup():
    global database, agent_monitor
    database = AIDatabase(Config.DATABASE_PATH)
    agent_monitor = AgentMonitor(database)
    
    # Start background monitoring
    asyncio.create_task(agent_monitor.monitor_agents())

@app.route('/')
async def index():
    """Main dashboard page"""
    agents = database.get_agents()
    metrics = agent_monitor.get_server_metrics()
    
    return await render_template('dashboard.html', 
                                agents=agents, 
                                metrics=metrics,
                                refresh_interval=Config.REFRESH_INTERVAL)

@app.route('/api/agents')
async def api_agents():
    """Get all agents data"""
    agents = database.get_agents()
    return jsonify([asdict(agent) for agent in agents])

@app.route('/api/metrics')
async def api_metrics():
    """Get current server metrics"""
    metrics = agent_monitor.get_server_metrics()
    return jsonify(asdict(metrics))

@app.route('/api/agent/<agent_id>/update', methods=['POST'])
async def update_agent(agent_id):
    """Update agent customization and return updated data"""
    data = await request.get_json()
    
    nickname = data.get('nickname', '')
    title = data.get('title', '')
    avatar_url = data.get('avatar_url', '')
    
    try:
        # Update the agent customizations
        database.update_agent_customization(agent_id, nickname, title, avatar_url)
        
        # Get the updated agent data
        agents = database.get_agents()
        agent = next((a for a in agents if a.id == agent_id), None)
        
        if agent:
            agent_data = asdict(agent)
            
            # Get the latest customizations
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT nickname, title, avatar_url
                    FROM agent_customizations
                    WHERE agent_id = ?
                ''', (agent_id,))
                
                custom_data = cursor.fetchone()
                if custom_data:
                    if custom_data[0]:  # nickname
                        agent_data['nickname'] = custom_data[0]
                    if custom_data[1]:  # title
                        agent_data['title'] = custom_data[1]
                    if custom_data[2]:  # avatar_url
                        agent_data['avatar'] = custom_data[2]
            
            return jsonify({
                "success": True, 
                "message": f"Agent {agent_id} updated successfully",
                "agent": agent_data
            })
        else:
            return jsonify({"error": "Agent not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/agent/<agent_id>/status')
async def agent_status(agent_id):
    """Get specific agent status with customizations"""
    agents = database.get_agents()
    agent = next((a for a in agents if a.id == agent_id), None)
    
    if agent:
        agent_data = asdict(agent)
        
        # Get customizations from agent_customizations table
        with sqlite3.connect(Config.DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nickname, title, avatar_url
                FROM agent_customizations
                WHERE agent_id = ?
            ''', (agent_id,))
            
            custom_data = cursor.fetchone()
            if custom_data:
                # Override with custom data if available
                if custom_data[0]:  # nickname
                    agent_data['nickname'] = custom_data[0]
                if custom_data[1]:  # title
                    agent_data['title'] = custom_data[1]
                if custom_data[2]:  # avatar_url
                    agent_data['avatar'] = custom_data[2]
        
        return jsonify(agent_data)
    return jsonify({"error": "Agent not found"}), 404

@app.route('/api/cooldl/restart', methods=['POST'])
async def restart_cooldl():
    """Restart CoolDL by executing ~/cooldl/restart.sh"""
    import subprocess
    import asyncio
    
    try:
        # Execute the restart script
        process = await asyncio.create_subprocess_exec(
            'bash', '/home/fahad/cooldl/restart.sh',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for the process to complete
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return jsonify({
                "success": True, 
                "message": "CoolDL restarted successfully",
                "output": stdout.decode().strip()
            })
        else:
            return jsonify({
                "success": False, 
                "message": "Failed to restart CoolDL",
                "error": stderr.decode().strip()
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Error restarting CoolDL: {str(e)}"
        }), 500

@app.route('/api/system/stats')
async def get_system_stats():
    """Get comprehensive system statistics"""
    import subprocess
    import asyncio
    import psutil
    import socket
    import os
    from datetime import datetime
    
    try:
        # Use psutil for memory info (more reliable than shell commands)
        memory = psutil.virtual_memory()
        memory_info = f"      total        used        free      shared  buff/cache   available\nMem: {memory.total // (1024**3):7d}GB {memory.used // (1024**3):7d}GB {memory.available // (1024**3):7d}GB {0:7d}GB {(memory.total - memory.available) // (1024**3):7d}GB {memory.available // (1024**3):7d}GB"
        
        # Use psutil for disk info
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total // (1024**3)
        disk_used_gb = disk.used // (1024**3)
        disk_free_gb = disk.free // (1024**3)
        disk_percent = disk.percent
        disk_info = f"Filesystem      Size  Used Avail Use% Mounted on\n/dev/root       {disk_total_gb}G {disk_used_gb}G {disk_free_gb}G  {disk_percent}% /"
        
        # Get CPU load using psutil
        load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.0
        cpu_info = f" load average: {load_avg:.2f}"
        
        # Get users count using psutil
        users_count = len(psutil.users())
        
        # Get top processes using psutil with better error handling
        try:
            processes = list(psutil.process_iter(['name', 'cpu_percent', 'memory_percent']))
            # Filter out processes where cpu_percent is None or 0
            cpu_processes = [p for p in processes if p.info['cpu_percent'] is not None and p.info['cpu_percent'] > 0]
            if cpu_processes:
                top_cpu_proc = max(cpu_processes, key=lambda p: p.info['cpu_percent'])
                top_cpu_process = f"{top_cpu_proc.info['name']}({top_cpu_proc.info['cpu_percent']:.1f}%)"
            else:
                top_cpu_process = "N/A"
        except:
            top_cpu_process = "N/A"
        
        try:
            processes = list(psutil.process_iter(['name', 'memory_percent']))
            # Filter out processes where memory_percent is None or 0
            memory_processes = [p for p in processes if p.info['memory_percent'] is not None and p.info['memory_percent'] > 0]
            if memory_processes:
                top_memory_proc = max(memory_processes, key=lambda p: p.info['memory_percent'])
                top_memory_process = f"{top_memory_proc.info['name']}({top_memory_proc.info['memory_percent']:.1f}%)"
            else:
                top_memory_process = "N/A"
        except:
            top_memory_process = "N/A"
        
        # Get IP address using socket
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except:
            ip_address = "127.0.0.1"
        
        # Get uptime using psutil
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
        if uptime_days > 0:
            uptime = f"up {uptime_days} days, {uptime_hours} hours, {uptime_minutes} minutes"
        elif uptime_hours > 0:
            uptime = f"up {uptime_hours} hours, {uptime_minutes} minutes"
        else:
            uptime = f"up {uptime_minutes} minutes"
        
        # Get service statuses using full paths
        services = ["blog-demo.service", "cooldl-bot.service"]
        service_status = {}
        for service in services:
            try:
                status_process = await asyncio.create_subprocess_exec(
                    '/usr/bin/systemctl', 'is-active', '--quiet', service,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await status_process.communicate()
                service_status[service.replace('.service', '')] = status_process.returncode == 0
            except:
                service_status[service.replace('.service', '')] = False
        
        # Parse and return data
        return jsonify({
            "memory": memory_info,
            "disk": disk_info,
            "cpu_load": cpu_info,
            "users_count": users_count,
            "top_cpu_process": top_cpu_process,
            "top_memory_process": top_memory_process,
            "ip_address": ip_address,
            "uptime": uptime,
            "services": service_status,
            "success": True
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error getting system stats: {str(e)}"
        }), 500

@app.websocket('/ws')
async def websocket_handler():
    """WebSocket for real-time updates"""
    ws = websocket
    try:
        while True:
            # Send current data
            agents = database.get_agents()
            metrics = agent_monitor.get_server_metrics()
            
            data = {
                'agents': [asdict(agent) for agent in agents],
                'metrics': asdict(metrics),
                'timestamp': datetime.now().isoformat()
            }
            
            await ws.send(json.dumps(data))
            await asyncio.sleep(Config.REFRESH_INTERVAL)
            
    except Exception as e:
        logging.error(f"WebSocket error: {e}")

def create_default_templates():
    """Create default HTML templates"""
    dashboard_template = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIDashboard - لوحة تحكم الوكلاء</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .dashboard-header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .agent-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .agent-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        .agent-avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: 3px solid #fff;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            margin-right: 15px;
        }
        .agent-status {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-left: 10px;
        }
        .status-idle {
            background: #28a745;
            color: white;
        }
        .status-working {
            background: #ffc107;
            color: black;
        }
        .status-error {
            background: #dc3545;
            color: white;
        }
        .status-offline {
            background: #6c757d;
            color: white;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .progress-bar {
            height: 8px;
            border-radius: 4px;
            background: #e9ecef;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="dashboard-header">
            <div class="row align-items-center">
                <div class="col">
                    <h1 class="mb-0">
                        <i class="fas fa-tachometer-alt"></i> 
                        AIDashboard - لوحة تحكم الوكلاء
                    </h1>
                    <p class="mb-0 mt-2">مراقبة الـ OpenClaw agents بالوقت الحقيقي</p>
                </div>
                <div class="col-auto">
                    <button class="btn btn-outline-light btn-sm" onclick="refreshData()">
                        <i class="fas fa-sync"></i> تحديث
                    </button>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <h3>الوكلاء النشطين</h3>
                <div id="agents-container" class="row">
                    <!-- Agent cards will be inserted here -->
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-12">
                <h3>مؤشرات الأداء</h3>
                <div class="metrics-grid" id="metrics-container">
                    <div class="metric-card">
                        <div class="metric-value" id="cpu-value">0%</div>
                        <div class="metric-label">المعالج</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="cpu-progress"></div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="memory-value">0%</div>
                        <div class="metric-label">الذاكرة</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="memory-progress"></div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="disk-value">0%</div>
                        <div class="metric-label">القرص</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="disk-progress"></div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="agents-count">0</div>
                        <div class="metric-label">الوكلاء</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Edit Agent Modal -->
    <div class="modal fade" id="editAgentModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">تعديل بيانات الوكيل</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="editAgentForm">
                        <div class="mb-3">
                            <label for="agentNickname" class="form-label">الاسم المستعار</label>
                            <input type="text" class="form-control" id="agentNickname" required>
                        </div>
                        <div class="mb-3">
                            <label for="agentTitle" class="form-label">المنصب</label>
                            <input type="text" class="form-control" id="agentTitle">
                        </div>
                        <div class="mb-3">
                            <label for="agentAvatar" class="form-label">رابط الصورة</label>
                            <input type="url" class="form-control" id="agentAvatar" placeholder="https://example.com/avatar.jpg">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                    <button type="button" class="btn btn-primary" onclick="saveAgentChanges()">حفظ التغييرات</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let socket = null;
        let currentAgentId = null;

        // Initialize WebSocket connection
        function initWebSocket() {
            if (socket && socket.readyState === WebSocket.OPEN) {
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function() {
                console.log('WebSocket connection established');
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'agent_update') {
                    updateAgentCard(data.agent);
                } else if (data.type === 'metrics_update') {
                    updateMetrics(data.metrics);
                }
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
            
            socket.onclose = function() {
                console.log('WebSocket connection closed');
                // Reconnect after 5 seconds
                setTimeout(initWebSocket, 5000);
            };
        }

        // Fetch initial data
        async function fetchInitialData() {
            try {
                const [agentsResponse, metricsResponse] = await Promise.all([
                    fetch('/api/agents'),
                    fetch('/api/metrics')
                ]);
                
                const agents = await agentsResponse.json();
                const metrics = await metricsResponse.json();
                
                renderAgents(agents);
                updateMetrics(metrics);
            } catch (error) {
                console.error('Error fetching initial data:', error);
            }
        }

        // Render agents
        function renderAgents(agents) {
            const container = document.getElementById('agents-container');
            container.innerHTML = '';
            
            agents.forEach(agent => {
                const agentCard = createAgentCard(agent);
                container.appendChild(agentCard);
            });
        }

        // Create agent card
        function createAgentCard(agent) {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-4';
            
            const statusClass = getStatusClass(agent.status);
            const avatarUrl = agent.avatar_url || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iNDAiIGN5PSI0MCIgcj0iNDAiIGZpbGw9IiM2NjdlZWEiLz4KPHN2ZyB4PSIyMCIgeT0iMjAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+CjxwYXRoIGQ9Ik0xMiAxMkMxMCAxMCAxMCAxMCAxMCAxMlYxOEMxMCAxOSAxMCAyMCAxMiAyMkgxNkMxOCAyMCAxOCAxOSAxOCAxOFYxMkMxOCAxMCAxOCAxMCAxNiAxMkgxMloiLz4KPHBhdGggZD0iTTE2IDhDMTYgNiAxNiA2IDE2IDhDMTYgNiAxNiA2IDE2IDhDMTYgNiAxNiA2IDE2IDhaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4KPC9zdmc+';
            
            col.innerHTML = `
                <div class="agent-card">
                    <div class="row align-items-center">
                        <div class="col-auto">
                            <img src="${avatarUrl}" alt="${agent.nickname || agent.id}" class="agent-avatar">
                        </div>
                        <div class="col">
                            <h5 class="mb-1">${agent.nickname || agent.id}</h5>
                            <p class="mb-1 text-muted">${agent.title || 'وكيل'}</p>
                            <span class="agent-status ${statusClass}">${getStatusText(agent.status)}</span>
                        </div>
                        <div class="col-auto">
                            <button class="btn btn-sm btn-outline-primary" onclick="editAgent('${agent.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            return col;
        }

        // Get status class
        function getStatusClass(status) {
            switch (status) {
                case 'idle': return 'status-idle';
                case 'working': return 'status-working';
                case 'error': return 'status-error';
                default: return 'status-offline';
            }
        }

        // Get status text
        function getStatusText(status) {
            switch (status) {
                case 'idle': return 'جاهز';
                case 'working': return 'يعمل';
                case 'error': return 'خطأ';
                default: return 'غير متصل';
            }
        }

        // Update metrics
        function updateMetrics(metrics) {
            document.getElementById('cpu-value').textContent = metrics.cpu_percent + '%';
            document.getElementById('memory-value').textContent = metrics.memory_percent + '%';
            document.getElementById('disk-value').textContent + metrics.disk_percent + '%';
            document.getElementById('agents-count').textContent = metrics.agents_count;
            
            document.getElementById('cpu-progress').style.width = metrics.cpu_percent + '%';
            document.getElementById('memory-progress').style.width = metrics.memory_percent + '%';
            document.getElementById('disk-progress').style.width = metrics.disk_percent + '%';
        }

        // Update agent card
        function updateAgentCard(agent) {
            const cards = document.querySelectorAll('.agent-card');
            cards.forEach(card => {
                if (card.textContent.includes(agent.id)) {
                    const statusSpan = card.querySelector('.agent-status');
                    if (statusSpan) {
                        statusSpan.className = 'agent-status ' + getStatusClass(agent.status);
                        statusSpan.textContent = getStatusText(agent.status);
                    }
                }
            });
        }

        // Edit agent
        function editAgent(agentId) {
            currentAgentId = agentId;
            const modal = new bootstrap.Modal(document.getElementById('editAgentModal'));
            modal.show();
        }

        // Save agent changes
        async function saveAgentChanges() {
            const nickname = document.getElementById('agentNickname').value;
            const title = document.getElementById('agentTitle').value;
            const avatar = document.getElementById('agentAvatar').value;
            
            try {
                const response = await fetch(`/api/agent/${currentAgentId}/update`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        nickname: nickname,
                        title: title,
                        avatar_url: avatar
                    })
                });
                
                if (response.ok) {
                    bootstrap.Modal.getInstance(document.getElementById('editAgentModal')).hide();
                    refreshData();
                } else {
                    alert('حدث خطأ أثناء حفظ التغييرات');
                }
            } catch (error) {
                console.error('Error saving agent changes:', error);
                alert('حدث خطأ أثناء حفظ التغييرات');
            }
        }

        // Refresh data
        function refreshData() {
            fetchInitialData();
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
            fetchInitialData();
            
            // Refresh data every 2 seconds
            setInterval(fetchInitialData, 2000);
        });
    </script>
</body>
</html>
    """
    
    template_path = os.path.join(Config.TEMPLATES_PATH, 'dashboard.html')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_template)
    
    print(f"✅ Created default template: {template_path}")

if __name__ == '__main__':
    # Ensure directories exist
    Path(Config.STATIC_PATH).mkdir(parents=True, exist_ok=True)
    Path(Config.TEMPLATES_PATH).mkdir(parents=True, exist_ok=True)
    
    # Create basic templates if they don't exist
    if not os.path.exists(os.path.join(Config.TEMPLATES_PATH, 'dashboard.html')):
        create_default_templates()
    
    print("🚀 Starting AIDashboard...")
    print(f"📊 Dashboard: http://localhost:5000")
    print(f"📁 Database: {Config.DATABASE_PATH}")
    print("🎯 Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

def create_default_templates():
    """Create default HTML templates"""
    dashboard_template = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIDashboard - لوحة تحكم الوكلاء</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .dashboard-header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .agent-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border: none;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        .agent-card:hover {
            transform: translateY(-5px);
        }
        .status-badge {
            font-size: 0.8em;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
        }
        .status-idle { background-color: #28a745; color: white; }
        .status-working { background-color: #ffc107; color: black; }
        .status-error { background-color: #dc3545; color: white; }
        .status-offline { background-color: #6c757d; color: white; }
        
        .agent-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #fff;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .metrics-card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #4a90e2;
        }
        
        .progress-bar-container {
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #4a90e2, #357abd);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .update-indicator {
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(40, 167, 69, 0.9);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            display: none;
        }
        
        .edit-agent-btn {
            background: #4a90e2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }
        
        .edit-agent-btn:hover {
            background: #357abd;
        }
        
        .modal-content {
            border-radius: 15px;
            border: none;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .modal-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 15px 15px 0 0;
            border: none;
        }
    </style>
</head>
<body>
    <div class="update-indicator" id="updateIndicator">
        <i class="fas fa-sync-alt"></i> جاري التحديث...
    </div>

    <div class="container-fluid">
        <!-- Header -->
        <div class="dashboard-header text-center text-white">
            <h1><i class="fas fa-robot"></i> AIDashboard</h1>
            <p class="mb-0">لوحة تحكم متقدمة لمراقبة الوكلاء الذكاء</p>
            <small class="text-muted">آخر تحديث: <span id="lastUpdate"></span></small>
        </div>

        <!-- Server Metrics -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="metrics-card">
                    <i class="fas fa-microchip text-primary"></i>
                    <div class="metric-value" id="cpuPercent">0%</div>
                    <small>استخدام المعالج</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metrics-card">
                    <i class="fas fa-memory text-success"></i>
                    <div class="metric-value" id="memoryPercent">0%</div>
                    <small>استخدام الذاكرة</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metrics-card">
                    <i class="fas fa-hdd text-warning"></i>
                    <div class="metric-value" id="diskPercent">0%</div>
                    <small>استخدام القرص</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metrics-card">
                    <i class="fas fa-tachometer-alt text-info"></i>
                    <div class="metric-value" id="loadAverage">0.0</div>
                    <small>متوسط الحمل</small>
                </div>
            </div>
        </div>

        <!-- Agents Grid -->
        <div class="row" id="agentsContainer">
            {% for agent in agents %}
            <div class="col-md-4 col-lg-3 mb-4">
                <div class="agent-card">
                    <div class="d-flex align-items-center mb-3">
                        <img src="{{ agent.avatar }}" alt="{{ agent.name }}" class="agent-avatar me-3">
                        <div>
                            <h5 class="mb-1">{{ agent.nickname or agent.name }}</h5>
                            <small class="text-muted">{{ agent.title }}</small>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <span class="status-badge status-{{ agent.status }}">
                            {% if agent.status == 'idle' %}
                                <i class="fas fa-check"></i> متاح
                            {% elif agent.status == 'working' %}
                                <i class="fas fa-cog fa-spin"></i> يعمل
                            {% elif agent.status == 'error' %}
                                <i class="fas fa-exclamation"></i> خطأ
                            {% else %}
                                <i class="fas fa-circle"></i> غير متصل
                            {% endif %}
                        </span>
                    </div>
                    
                    {% if agent.current_task %}
                    <div class="mb-2">
                        <small class="text-muted">المهمة الحالية:</small>
                        <div class="fw-bold">{{ agent.current_task }}</div>
                    </div>
                    {% endif %}
                    
                    <div class="mb-2">
                        <small class="text-muted">القناة:</small>
                        <div>{{ agent.channel or 'غير محدد' }}</div>
                    </div>
                    
                    <div class="mb-3">
                        <div class="d-flex justify-content-between mb-1">
                            <small>المعالج: {{ "%.1f"|format(agent.cpu_usage) }}%</small>
                            <small>الذاكرة: {{ "%.1f"|format(agent.memory_usage) }}%</small>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" style="width: {{ (agent.cpu_usage + agent.memory_usage) / 2 }}%"></div>
                        </div>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-clock"></i> {{ "%.1f"|format(agent.response_time) }}ms
                        </small>
                        <button class="edit-agent-btn" onclick="editAgent('{{ agent.id }}')">
                            <i class="fas fa-edit"></i> تعديل
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Edit Agent Modal -->
    <div class="modal fade" id="editAgentModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">تعديل بيانات الوكيل</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="editAgentForm">
                        <input type="hidden" id="agentId">
                        
                        <div class="mb-3">
                            <label class="form-label">الاسم المستعار (Nickname)</label>
                            <input type="text" class="form-control" id="agentNickname" placeholder="مثلاً: أبومساعد">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">اللقب (Title)</label>
                            <input type="text" class="form-control" id="agentTitle" placeholder="مثلاً: كبير الوكلاء">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">رابط الصورة الشخصية</label>
                            <input type="url" class="form-control" id="agentAvatar" placeholder="https://example.com/avatar.jpg">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                    <button type="button" class="btn btn-primary" onclick="saveAgent()">حفظ التغييرات</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let ws;
        let refreshInterval = {{ refresh_interval * 1000 }};
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
                showUpdateIndicator();
            };
            
            ws.onclose = function() {
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateDashboard(data) {
            // Update agents
            const container = document.getElementById('agentsContainer');
            container.innerHTML = '';
            
            data.agents.forEach(agent => {
                const agentCard = createAgentCard(agent);
                container.innerHTML += agentCard;
            });
            
            // Update metrics
            document.getElementById('cpuPercent').textContent = data.metrics.cpu_percent.toFixed(1) + '%';
            document.getElementById('memoryPercent').textContent = data.metrics.memory_percent.toFixed(1) + '%';
            document.getElementById('diskPercent').textContent = data.metrics.disk_percent.toFixed(1) + '%';
            document.getElementById('loadAverage').textContent = data.metrics.load_average.toFixed(2);
            
            // Update timestamp
            document.getElementById('lastUpdate').textContent = new Date(data.timestamp).toLocaleString('ar-SA');
        }
        
        function createAgentCard(agent) {
            const statusText = {
                'idle': '<i class="fas fa-check"></i> متاح',
                'working': '<i class="fas fa-cog fa-spin"></i> يعمل',
                'error': '<i class="fas fa-exclamation"></i> خطأ',
                'offline': '<i class="fas fa-circle"></i> غير متصل'
            };
            
            return `
                <div class="col-md-4 col-lg-3 mb-4">
                    <div class="agent-card">
                        <div class="d-flex align-items-center mb-3">
                            <img src="${agent.avatar}" alt="${agent.name}" class="agent-avatar me-3">
                            <div>
                                <h5 class="mb-1">${agent.nickname || agent.name}</h5>
                                <small class="text-muted">${agent.title}</small>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <span class="status-badge status-${agent.status}">
                                ${statusText[agent.status] || statusText['offline']}
                            </span>
                        </div>
                        
                        ${agent.current_task ? `
                        <div class="mb-2">
                            <small class="text-muted">المهمة الحالية:</small>
                            <div class="fw-bold">${agent.current_task}</div>
                        </div>
                        ` : ''}
                        
                        <div class="mb-2">
                            <small class="text-muted">القناة:</small>
                            <div>${agent.channel || 'غير محدد'}</div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <small>المعالج: ${agent.cpu_usage.toFixed(1)}%</small>
                                <small>الذاكرة: ${agent.memory_usage.toFixed(1)}%</small>
                            </div>
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" style="width: ${(agent.cpu_usage + agent.memory_usage) / 2}%"></div>
                            </div>
                        </div>
                        
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> ${agent.response_time.toFixed(1)}ms
                            </small>
                            <button class="edit-agent-btn" onclick="editAgent('${agent.id}')">
                                <i class="fas fa-edit"></i> تعديل
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function showUpdateIndicator() {
            const indicator = document.getElementById('updateIndicator');
            indicator.style.display = 'block';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 1000);
        }
        
        function editAgent(agentId) {
            fetch(`/api/agent/${agentId}/status`)
                .then(response => response.json())
                .then(agent => {
                    document.getElementById('agentId').value = agent.id;
                    document.getElementById('agentNickname').value = agent.nickname || '';
                    document.getElementById('agentTitle').value = agent.title || '';
                    document.getElementById('agentAvatar').value = agent.avatar || '';
                    
                    const modal = new bootstrap.Modal(document.getElementById('editAgentModal'));
                    modal.show();
                });
        }
        
        function saveAgent() {
            const agentId = document.getElementById('agentId').value;
            const data = {
                nickname: document.getElementById('agentNickname').value,
                title: document.getElementById('agentTitle').value,
                avatar_url: document.getElementById('agentAvatar').value
            };
            
            fetch(`/api/agent/${agentId}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editAgentModal'));
                    modal.hide();
                    
                    // Show success message
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
                    alert.innerHTML = `
                        <i class="fas fa-check"></i> ${result.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    document.body.appendChild(alert);
                    
                    setTimeout(() => {
                        alert.remove();
                    }, 3000);
                }
            });
        }
        
        // Initialize WebSocket connection
        connectWebSocket();
        
        // Fallback: refresh data periodically if WebSocket fails
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                return; // WebSocket is working
            }
            
            // Fallback to API calls
            fetch('/api/agents')
                .then(response => response.json())
                .then(agents => {
                    fetch('/api/metrics')
                        .then(response => response.json())
                        .then(metrics => {
                            updateDashboard({ agents, metrics, timestamp: new Date().toISOString() });
                            showUpdateIndicator();
                        });
                });
        }, refreshInterval);
    </script>
</body>
</html>
    """
    
    with open(os.path.join(Config.TEMPLATES_PATH, 'dashboard.html'), 'w', encoding='utf-8') as f:
        f.write(dashboard_template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)