#!/usr/bin/env python3
"""
Enhanced AIDashboard with Agent Task Distribution
=============================================
Extends the original AIDashboard to include:
- Individual agent task management
- Real-time task distribution
- Agent workload monitoring
- Task assignment and tracking
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from quart import Quart, render_template, websocket, request, jsonify, send_from_directory
import aiohttp

# Import the task distribution system
from agent_task_system import (
    AgentTaskDatabase, TaskDistributor, AgentTask, 
    AgentWorkload, AgentTaskSystem, Config as TaskConfig
)

# Import the original dashboard components
import psutil

# Extend the configuration
class Config:
    # Original config
    DATABASE_PATH = "/home/fahad/AIDB/aidashboard.db"
    AGENTS_CONFIG_PATH = "/home/fahad/.openclaw/agents/openclaw.json"
    WORKSPACE_BASE = "/home/fahad/.openclaw/agents"
    STATIC_PATH = "/home/fahad/AIDB/static"
    TEMPLATES_PATH = "/home/fahad/AIDB/templates"
    DEFAULT_AVATAR = "/static/img/default-agent.png"
    REFRESH_INTERVAL = 2  # seconds
    
    # Task system config
    TASK_DATABASE_PATH = "/home/fahad/AIDB/agent_tasks.db"
    MAX_CONCURRENT_TASKS_PER_AGENT = 3

# Enhanced Quart App
app = Quart(__name__, 
            static_folder=Config.STATIC_PATH,
            template_folder=Config.TEMPLATES_PATH)

# Global variables
database = None
task_database = None
task_system = None
task_distributor = None

@app.before_serving
async def startup():
    global database, task_database, task_system, task_distributor
    
    # Initialize original dashboard database
    from app import AIDatabase
    database = AIDatabase(Config.DATABASE_PATH)
    
    # Initialize task system
    task_database = AgentTaskDatabase(Config.TASK_DATABASE_PATH)
    task_distributor = TaskDistributor(task_database)
    task_system = AgentTaskSystem()
    
    # Start task distribution system
    asyncio.create_task(task_system.start())

# Import the original routes and extend them
from app import app as original_app

# Extend the index route to include task information
@app.route('/')
async def index():
    """Enhanced main dashboard page with task distribution"""
    # Get original data
    agents = database.get_agents()
    metrics = original_app.agent_monitor.get_server_metrics()
    
    # Get task information for each agent
    agent_workloads = {}
    for agent in agents:
        try:
            workload = task_database.get_agent_workload(agent.id)
            agent_workloads[agent.id] = workload
        except:
            # Agent not in task database yet
            agent_workloads[agent.id] = AgentWorkload(
                agent_id=agent.id,
                agent_name=agent.name,
                agent_nickname=agent.nickname or agent.name,
                current_tasks=[],
                max_concurrent=Config.MAX_CONCURRENT_TASKS_PER_AGENT,
                active_count=0,
                completed_count=0,
                failed_count=0,
                total_task_time=0,
                average_response_time=0.0,
                status='available'
            )
    
    return await render_template('enhanced_dashboard.html', 
                                agents=agents, 
                                metrics=metrics,
                                agent_workloads=agent_workloads,
                                refresh_interval=Config.REFRESH_INTERVAL)

# New API routes for task management
@app.route('/api/tasks')
async def api_tasks():
    """Get all tasks"""
    with sqlite3.connect(Config.TASK_DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, agent_id, title, description, priority, status, progress,
                   assigned_at, started_at, completed_at, estimated_duration, actual_duration,
                   dependencies, result, error_message, created_by, last_updated
            FROM agent_tasks
            ORDER BY priority, assigned_at
        ''')
        
        tasks = []
        for row in cursor.fetchall():
            task = AgentTask(
                id=row[0], agent_id=row[1], title=row[2], description=row[3],
                priority=row[4], status=row[5], progress=row[6],
                assigned_at=row[7], started_at=row[8], completed_at=row[9],
                estimated_duration=row[10], actual_duration=row[11],
                dependencies=json.loads(row[12]) if row[12] else [],
                result=row[13], error_message=row[14], created_by=row[15],
                last_updated=row[16]
            )
            tasks.append(asdict(task))
        
        return jsonify(tasks)

@app.route('/api/agent/<agent_id>/tasks')
async def api_agent_tasks(agent_id):
    """Get tasks for a specific agent"""
    tasks = task_database.get_agent_workload(agent_id)
    return jsonify(asdict(tasks))

@app.route('/api/agent/<agent_id>/workload')
async def api_agent_workload(agent_id):
    """Get agent workload information"""
    workload = task_database.get_agent_workload(agent_id)
    return jsonify(asdict(workload))

@app.route('/api/task/<task_id>/status', methods=['GET', 'POST'])
async def api_task_status(task_id):
    """Get or update task status"""
    if request.method == 'GET':
        with sqlite3.connect(Config.TASK_DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM agent_tasks WHERE id = ?
            ''', (task_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Task not found"}), 404
                
            task = AgentTask(
                id=row[0], agent_id=row[1], title=row[2], description=row[3],
                priority=row[4], status=row[5], progress=row[6],
                assigned_at=row[7], started_at=row[8], completed_at=row[9],
                estimated_duration=row[10], actual_duration=row[11],
                dependencies=json.loads(row[12]) if row[12] else [],
                result=row[13], error_message=row[14], created_by=row[15],
                last_updated=row[16]
            )
            
            return jsonify(asdict(task))
    else:
        # Update task status
        data = await request.get_json()
        status = data.get('status')
        progress = data.get('progress')
        result = data.get('result')
        
        if status:
            task_database.update_task_status(task_id, status, progress, result)
            return jsonify({"success": True, "message": f"Task {task_id} updated"})
        else:
            return jsonify({"error": "Status is required"}), 400

@app.route('/api/create_task', methods=['POST'])
async def api_create_task():
    """Create a new task"""
    data = await request.get_json()
    
    task_type = data.get('task_type', 'general')
    title = data.get('title')
    description = data.get('description', '')
    priority = data.get('priority', 2)
    assigned_to = data.get('assigned_to')
    
    if not title:
        return jsonify({"error": "Title is required"}), 400
    
    try:
        task_id = await task_distributor.distribute_task(
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to
        )
        
        return jsonify({
            "success": True, 
            "task_id": task_id,
            "message": f"Task '{title}' created and assigned"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/task_distribution')
async def api_task_distribution():
    """Get current task distribution statistics"""
    with sqlite3.connect(Config.TASK_DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Get agent workload summary
        cursor.execute('''
            SELECT id, name, nickname, status, active_tasks, completed_tasks, failed_tasks
            FROM agents
        ''')
        
        agents_summary = []
        for row in cursor.fetchall():
            agents_summary.append({
                "id": row[0],
                "name": row[1],
                "nickname": row[2] or row[1],
                "status": row[3],
                "active_tasks": row[4] or 0,
                "completed_tasks": row[5] or 0,
                "failed_tasks": row[6] or 0
            })
        
        # Get task counts by status
        cursor.execute('''
            SELECT status, COUNT(*) FROM agent_tasks GROUP BY status
        ''')
        task_counts = dict(cursor.fetchall())
        
        return jsonify({
            "agents": agents_summary,
            "task_counts": task_counts,
            "total_tasks": sum(task_counts.values())
        })

# Enhanced WebSocket for real-time updates
@app.websocket('/ws')
async def enhanced_websocket_handler():
    """Enhanced WebSocket with task distribution updates"""
    ws = websocket
    try:
        while True:
            # Get original data
            agents = database.get_agents()
            metrics = original_app.agent_monitor.get_server_metrics()
            
            # Get task information
            agent_workloads = {}
            for agent in agents:
                try:
                    workload = task_database.get_agent_workload(agent.id)
                    agent_workloads[agent.id] = asdict(workload)
                except:
                    continue
            
            # Get recent tasks
            with sqlite3.connect(Config.TASK_DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, agent_id, title, status, progress, last_updated
                    FROM agent_tasks 
                    WHERE status IN ('pending', 'assigned', 'working')
                    ORDER BY last_updated DESC
                    LIMIT 10
                ''')
                
                recent_tasks = []
                for row in cursor.fetchall():
                    recent_tasks.append({
                        "id": row[0],
                        "agent_id": row[1],
                        "title": row[2],
                        "status": row[3],
                        "progress": row[4],
                        "last_updated": row[5]
                    })
            
            data = {
                'agents': [asdict(agent) for agent in agents],
                'metrics': asdict(metrics),
                'agent_workloads': agent_workloads,
                'recent_tasks': recent_tasks,
                'timestamp': datetime.now().isoformat()
            }
            
            await ws.send(json.dumps(data))
            await asyncio.sleep(Config.REFRESH_INTERVAL)
            
    except Exception as e:
        logging.error(f"Enhanced WebSocket error: {e}")

# Create enhanced dashboard template
def create_enhanced_dashboard_template():
    template_content = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIDashboard - نظام توزيع المهام بين الوكلاء</title>
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
            position: relative;
        }
        .agent-card:hover {
            transform: translateY(-5px);
        }
        .agent-status {
            position: absolute;
            top: 15px;
            left: 15px;
            font-size: 0.8em;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
        }
        .status-available { background-color: #28a745; color: white; }
        .status-busy { background-color: #ffc107; color: black; }
        .status-overloaded { background-color: #dc3545; color: white; }
        .status-offline { background-color: #6c757d; color: white; }
        
        .task-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            border-left: 4px solid #4a90e2;
            transition: all 0.3s ease;
        }
        .task-item:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        
        .progress-ring {
            width: 60px;
            height: 60px;
            margin: 0 auto 10px;
        }
        
        .progress-ring-circle {
            stroke: #4a90e2;
            stroke-width: 4;
            fill: transparent;
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
        }
        
        .agent-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
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
        
        .task-queue {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            max-height: 400px;
            overflow-y: auto;
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
            z-index: 1000;
        }
        
        .create-task-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #4a90e2;
            color: white;
            border: none;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .create-task-btn:hover {
            transform: scale(1.1);
            background: #357abd;
        }
        
        .workload-bar {
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .workload-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #ffc107, #dc3545);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        
        .working {
            animation: pulse 2s infinite;
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
            <h1><i class="fas fa-robot"></i> AIDashboard - نظام توزيع المهام</h1>
            <p class="mb-0">لوحة تحكم متقدمة لتوزيع المهام بين الوكلاء الذكاء</p>
            <small class="text-muted">كل وكيل ياخذ شغله الخاص ويعرضه هنا</small>
        </div>

        <!-- Task Queue -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="task-queue">
                    <h5><i class="fas fa-tasks"></i> طابور المهام الحالي</h5>
                    <div id="taskQueue">
                        <!-- Tasks will be populated here -->
                    </div>
                </div>
            </div>
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
            <!-- Agent cards will be populated here -->
        </div>
    </div>

    <!-- Create Task Button -->
    <button class="create-task-btn" data-bs-toggle="modal" data-bs-target="#createTaskModal" title="إنشاء مهمة جديدة">
        <i class="fas fa-plus"></i>
    </button>

    <!-- Create Task Modal -->
    <div class="modal fade" id="createTaskModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title"><i class="fas fa-plus"></i> إنشاء مهمة جديدة</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="createTaskForm">
                        <div class="mb-3">
                            <label class="form-label">نوع المهمة</label>
                            <select class="form-select" id="taskType">
                                <option value="general">عامة</option>
                                <option value="system_design">تصميم نظام</option>
                                <option value="business_analysis">تحليل تجاري</option>
                                <option value="development">تطوير</option>
                                <option value="testing">اختبار</option>
                                <option value="infrastructure">بنية تحتية</option>
                                <option value="performance">أداء</option>
                                <option value="ui_ux">واجهة المستخدم</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">عنوان المهمة</label>
                            <input type="text" class="form-control" id="taskTitle" placeholder="أدخل عنوان المهمة" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">وصف المهمة</label>
                            <textarea class="form-control" id="taskDescription" rows="3" placeholder="وصف المهمة (اختياري)"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">الأولوية</label>
                            <select class="form-select" id="taskPriority">
                                <option value="1">عالية (1)</option>
                                <option value="2" selected>متوسطة (2)</option>
                                <option value="3">منخفضة (3)</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">تكليف وكيل محدد (اختياري)</label>
                            <select class="form-select" id="assignedAgent">
                                <option value="">تلقائي</option>
                                <!-- Agents will be populated here -->
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                    <button type="button" class="btn btn-primary" onclick="createTask()">إنشاء المهمة</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let ws;
        let refreshInterval = {{ refresh_interval * 1000 }};
        let agentsData = [];
        
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
            // Update task queue
            updateTaskQueue(data.recent_tasks || []);
            
            // Update agents
            const container = document.getElementById('agentsContainer');
            container.innerHTML = '';
            
            agentsData = data.agents;
            data.agents.forEach(agent => {
                const workload = data.agent_workloads[agent.id] || {
                    current_tasks: [],
                    active_count: 0,
                    completed_count: 0,
                    failed_count: 0,
                    status: 'available'
                };
                
                const agentCard = createAgentCard(agent, workload);
                container.innerHTML += agentCard;
            });
            
            // Update metrics
            if (data.metrics) {
                document.getElementById('cpuPercent').textContent = data.metrics.cpu_percent.toFixed(1) + '%';
                document.getElementById('memoryPercent').textContent = data.metrics.memory_percent.toFixed(1) + '%';
                document.getElementById('diskPercent').textContent = data.metrics.disk_percent.toFixed(1) + '%';
                document.getElementById('loadAverage').textContent = data.metrics.load_average.toFixed(2);
            }
        }
        
        function createAgentCard(agent, workload) {
            const statusColors = {
                'available': 'status-available',
                'busy': 'status-busy',
                'overloaded': 'status-overloaded',
                'offline': 'status-offline'
            };
            
            const statusTexts = {
                'available': 'متاح',
                'busy': 'مشغول',
                'overloaded': 'محمل',
                'offline': 'غير متصل'
            };
            
            const taskItems = workload.current_tasks.map(task => `
                <div class="task-item ${task.status === 'working' ? 'working' : ''}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${task.title}</strong>
                            <small class="text-muted d-block">${task.agent_id}</small>
                        </div>
                        <div>
                            <span class="badge bg-primary">${task.progress.toFixed(0)}%</span>
                        </div>
                    </div>
                </div>
            `).join('');
            
            const workloadPercentage = Math.min(100, (workload.active_count / workload.max_concurrent) * 100);
            
            return `
                <div class="col-md-4 col-lg-3 mb-4">
                    <div class="agent-card">
                        <span class="agent-status ${statusColors[workload.status]}">
                            ${statusTexts[workload.status]}
                        </span>
                        
                        <div class="d-flex align-items-center mb-3">
                            <img src="${agent.avatar}" alt="${agent.name}" class="agent-avatar me-3">
                            <div>
                                <h5 class="mb-1">${agent.nickname || agent.name}</h5>
                                <small class="text-muted">${agent.title}</small>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <small>المهام النشطة: ${workload.active_count}/${workload.max_concurrent}</small>
                                <small>مكتملة: ${workload.completed_count}</small>
                            </div>
                            <div class="workload-bar">
                                <div class="workload-fill" style="width: ${workloadPercentage}%"></div>
                            </div>
                        </div>
                        
                        ${taskItems ? `
                        <div class="mb-3">
                            <h6 class="mb-2">المهام الحالية:</h6>
                            ${taskItems}
                        </div>
                        ` : ''}
                        
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> ${agent.response_time.toFixed(1)}ms
                            </small>
                            <small class="text-muted">
                                <i class="fas fa-check"></i> ${workload.completed_count}
                                ${workload.failed_count > 0 ? `<i class="fas fa-times text-danger"></i> ${workload.failed_count}` : ''}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function updateTaskQueue(tasks) {
            const queueContainer = document.getElementById('taskQueue');
            
            if (tasks.length === 0) {
                queueContainer.innerHTML = '<p class="text-muted text-center">لا توجد مهام في الطابور</p>';
                return;
            }
            
            const taskItems = tasks.map(task => {
                const statusColor = {
                    'pending': 'secondary',
                    'assigned': 'primary',
                    'working': 'warning',
                    'completed': 'success',
                    'failed': 'danger'
                };
                
                return `
                    <div class="task-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${task.title}</strong>
                                <small class="text-muted d-block">
                                    <i class="fas fa-user"></i> ${task.agent_id} - 
                                    <span class="badge bg-${statusColor[task.status]}">${task.status}</span>
                                </small>
                            </div>
                            <div>
                                <span class="badge bg-primary">${task.progress.toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            queueContainer.innerHTML = taskItems;
        }
        
        function showUpdateIndicator() {
            const indicator = document.getElementById('updateIndicator');
            indicator.style.display = 'block';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 1000);
        }
        
        async function createTask() {
            const taskType = document.getElementById('taskType').value;
            const title = document.getElementById('taskTitle').value;
            const description = document.getElementById('taskDescription').value;
            const priority = document.getElementById('taskPriority').value;
            const assignedAgent = document.getElementById('assignedAgent').value;
            
            if (!title) {
                alert('الرجاء إدخال عنوان المهمة');
                return;
            }
            
            try {
                const response = await fetch('/api/create_task', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        task_type: taskType,
                        title: title,
                        description: description,
                        priority: parseInt(priority),
                        assigned_to: assignedAgent
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('createTaskModal'));
                    modal.hide();
                    
                    // Reset form
                    document.getElementById('createTaskForm').reset();
                    
                    // Show success message
                    showAlert('✅ تم إنشاء المهمة بنجاح', 'success');
                } else {
                    showAlert('❌ ' + result.error, 'danger');
                }
            } catch (error) {
                showAlert('❌ حدث خطأ: ' + error.message, 'danger');
            }
        }
        
        function showAlert(message, type) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
            alert.style.zIndex = '9999';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(alert);
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
        
        // Initialize agent select dropdown
        async function initializeAgentSelect() {
            try {
                const response = await fetch('/api/agents');
                const agents = await response.json();
                
                const select = document.getElementById('assignedAgent');
                agents.forEach(agent => {
                    const option = document.createElement('option');
                    option.value = agent.id;
                    option.textContent = agent.nickname || agent.name;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading agents:', error);
            }
        }
        
        // Initialize WebSocket connection
        connectWebSocket();
        
        // Initialize agent dropdown
        initializeAgentSelect();
        
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
                            fetch('/api/task_distribution')
                                .then(response => response.json())
                                .then(taskDist => {
                                    // Create mock data structure
                                    const data = {
                                        agents: agents,
                                        metrics: metrics,
                                        agent_workloads: {},
                                        recent_tasks: [],
                                        timestamp: new Date().toISOString()
                                    };
                                    
                                    // Get workloads for each agent
                                    Promise.all(agents.map(agent => 
                                        fetch(`/api/agent/${agent.id}/workload`)
                                            .then(response => response.json())
                                            .then(workload => {
                                                data.agent_workloads[agent.id] = workload;
                                            })
                                    )).then(() => {
                                        updateDashboard(data);
                                        showUpdateIndicator();
                                    });
                                });
                        });
                });
        }, refreshInterval);
    </script>
</body>
</html>
    """
    
    with open(os.path.join(Config.TEMPLATES_PATH, 'enhanced_dashboard.html'), 'w', encoding='utf-8') as f:
        f.write(template_content)

if __name__ == '__main__':
    # Ensure templates exist
    create_enhanced_dashboard_template()
    
    print("🚀 Starting Enhanced AIDashboard with Task Distribution...")
    print("📊 URL: http://localhost:5000")
    print("🔄 Real-time task distribution enabled")
    print("👥 Each agent works on their assigned tasks")
    print("⏹️  Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True)