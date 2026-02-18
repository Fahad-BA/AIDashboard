#!/usr/bin/env python3
"""
Agent Task Distribution System
============================
Distributes tasks among agents and each agent manages their own work
Features:
- Each agent has their own task queue
- Agents work independently
- Task status tracking per agent
- Real-time updates in AIDashboard
"""

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import aiohttp
from pathlib import Path

# Configuration
class Config:
    DATABASE_PATH = "/home/fahad/AIDB/agent_tasks.db"
    AGENTS_CONFIG_PATH = "/home/fahad/.openclaw/agents/openclaw.json"
    WORKSPACE_BASE = "/home/fahad/.openclaw/agents"
    MAX_CONCURRENT_TASKS_PER_AGENT = 3
    TASK_TIMEOUT = 300  # 5 minutes
    REFRESH_INTERVAL = 2  # seconds

@dataclass
class AgentTask:
    id: str
    agent_id: str
    title: str
    description: str
    priority: int  # 1=High, 2=Medium, 3=Low
    status: str  # pending, assigned, working, completed, failed
    progress: float  # 0-100
    assigned_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    estimated_duration: int  # seconds
    actual_duration: Optional[int]
    dependencies: List[str]  # task IDs this task depends on
    result: Optional[str]
    error_message: Optional[str]
    created_by: str  # who created this task
    last_updated: str

@dataclass
class AgentWorkload:
    agent_id: str
    agent_name: str
    agent_nickname: str
    current_tasks: List[AgentTask]
    max_concurrent: int
    active_count: int
    completed_count: int
    failed_count: int
    total_task_time: int
    average_response_time: float
    status: str  # available, busy, overloaded, offline

class AgentTaskDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'pending',
                    progress REAL DEFAULT 0.0,
                    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    started_at TEXT,
                    completed_at TEXT,
                    estimated_duration INTEGER DEFAULT 300,
                    actual_duration INTEGER,
                    dependencies TEXT DEFAULT '[]',
                    result TEXT,
                    error_message TEXT,
                    created_by TEXT DEFAULT 'system',
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # Agents table (extends from AIDashboard)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    nickname TEXT,
                    title TEXT,
                    model TEXT,
                    status TEXT DEFAULT 'available',
                    max_concurrent_tasks INTEGER DEFAULT 3,
                    active_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    total_task_time INTEGER DEFAULT 0,
                    average_response_time REAL DEFAULT 0.0,
                    last_heartbeat TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Agent performance metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    task_id TEXT,
                    cpu_usage REAL,
                    memory_usage REAL,
                    response_time REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id),
                    FOREIGN KEY (task_id) REFERENCES agent_tasks (id)
                )
            ''')
            
            # Task dependencies
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    depends_on TEXT,
                    dependency_type TEXT DEFAULT 'completion',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES agent_tasks (id),
                    FOREIGN KEY (depends_on) REFERENCES agent_tasks (id)
                )
            ''')
            
            conn.commit()
            
    def add_agent(self, agent_config: Dict[str, Any]):
        """Add or update agent in database"""
        agent_id = agent_config.get('id')
        agent_name = agent_config.get('name', agent_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO agents 
                (id, name, nickname, title, model, max_concurrent_tasks)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                agent_id,
                agent_name,
                agent_config.get('nickname', ''),
                agent_config.get('title', ''),
                agent_config.get('model', ''),
                Config.MAX_CONCURRENT_TASKS_PER_AGENT
            ))
            conn.commit()
            
    def create_task(self, task: AgentTask) -> str:
        """Create a new task"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agent_tasks 
                (id, agent_id, title, description, priority, status, estimated_duration, 
                 dependencies, created_by, assigned_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.agent_id,
                task.title,
                task.description,
                task.priority,
                task.status,
                task.estimated_duration,
                json.dumps(task.dependencies),
                task.created_by,
                task.assigned_at,
                task.last_updated
            ))
            
            # Update agent heartbeat
            cursor.execute('''
                UPDATE agents 
                SET last_heartbeat = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (task.agent_id,))
            
            conn.commit()
            return task.id
            
    def get_agent_tasks(self, agent_id: str) -> List[AgentTask]:
        """Get all tasks for a specific agent"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, agent_id, title, description, priority, status, progress,
                       assigned_at, started_at, completed_at, estimated_duration, actual_duration,
                       dependencies, result, error_message, created_by, last_updated
                FROM agent_tasks 
                WHERE agent_id = ?
                ORDER BY priority, assigned_at
            ''', (agent_id,))
            
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
                tasks.append(task)
            
            return tasks
            
    def get_agent_workload(self, agent_id: str) -> AgentWorkload:
        """Get agent workload information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get agent info
            cursor.execute('''
                SELECT name, nickname, title, status, max_concurrent_tasks,
                       active_tasks, completed_tasks, failed_tasks, total_task_time,
                       average_response_time, last_heartbeat
                FROM agents WHERE id = ?
            ''', (agent_id,))
            
            agent_row = cursor.fetchone()
            if not agent_row:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get current tasks
            tasks = self.get_agent_tasks(agent_id)
            active_tasks = [task for task in tasks if task.status in ['assigned', 'working']]
            
            # Determine agent status
            if len(active_tasks) >= agent_row[4]:  # max_concurrent_tasks
                status = 'overloaded'
            elif len(active_tasks) > 0:
                status = 'busy'
            elif agent_row[10] and (datetime.now() - datetime.fromisoformat(agent_row[10])).seconds > 60:
                status = 'offline'
            else:
                status = 'available'
            
            return AgentWorkload(
                agent_id=agent_id,
                agent_name=agent_row[0],
                agent_nickname=agent_row[1] or agent_row[0],
                current_tasks=active_tasks,
                max_concurrent=agent_row[4],
                active_count=len(active_tasks),
                completed_count=agent_row[6] or 0,
                failed_count=agent_row[7] or 0,
                total_task_time=agent_row[8] or 0,
                average_response_time=agent_row[9] or 0.0,
                status=status
            )
            
    def update_task_status(self, task_id: str, status: str, progress: float = None, result: str = None):
        """Update task status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = ['status = ?', 'last_updated = CURRENT_TIMESTAMP']
            params = [status]
            
            if progress is not None:
                updates.append('progress = ?')
                params.append(progress)
                
            if result is not None:
                updates.append('result = ?')
                params.append(result)
                
            if status == 'working':
                updates.append('started_at = CURRENT_TIMESTAMP')
                
            if status in ['completed', 'failed']:
                updates.append('completed_at = CURRENT_TIMESTAMP')
                # Update actual duration
                cursor.execute('''
                    SELECT assigned_at FROM agent_tasks WHERE id = ?
                ''', (task_id,))
                assigned_at = cursor.fetchone()[0]
                duration = (datetime.now() - datetime.fromisoformat(assigned_at)).seconds
                updates.append('actual_duration = ?')
                params.append(duration)
                
                # Update agent stats
                cursor.execute('''
                    UPDATE agents 
                    SET {stats}_tasks = {stats}_tasks + 1,
                        total_task_time = total_task_time + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT agent_id FROM agent_tasks WHERE id = ?)
                '''.format(stats='completed' if status == 'completed' else 'failed'),
                (duration, task_id))
            
            params.append(task_id)
            
            cursor.execute(f'''
                UPDATE agent_tasks 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            
            conn.commit()
            
    def get_next_task(self, agent_id: str) -> Optional[AgentTask]:
        """Get the next task for an agent to work on"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get agent's current active tasks
            cursor.execute('''
                SELECT COUNT(*) FROM agent_tasks 
                WHERE agent_id = ? AND status IN ('assigned', 'working')
            ''', (agent_id,))
            active_count = cursor.fetchone()[0]
            
            # Get agent's max concurrent tasks
            cursor.execute('''
                SELECT max_concurrent_tasks FROM agents WHERE id = ?
            ''', (agent_id,))
            max_concurrent = cursor.fetchone()[0]
            
            if active_count >= max_concurrent:
                return None
                
            # Get highest priority pending task
            cursor.execute('''
                SELECT id, agent_id, title, description, priority, status, progress,
                       assigned_at, started_at, completed_at, estimated_duration, actual_duration,
                       dependencies, result, error_message, created_by, last_updated
                FROM agent_tasks 
                WHERE agent_id = ? AND status = 'pending'
                ORDER BY priority, assigned_at
                LIMIT 1
            ''', (agent_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Mark task as assigned
            task_id = row[0]
            cursor.execute('''
                UPDATE agent_tasks 
                SET status = 'assigned', last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (task_id,))
            
            # Update agent active tasks count
            cursor.execute('''
                UPDATE agents 
                SET active_tasks = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (active_count + 1, agent_id))
            
            conn.commit()
            
            return AgentTask(
                id=row[0], agent_id=row[1], title=row[2], description=row[3],
                priority=row[4], status='assigned', progress=row[5],
                assigned_at=row[6], started_at=row[7], completed_at=row[8],
                estimated_duration=row[9], actual_duration=row[10],
                dependencies=json.loads(row[11]) if row[11] else [],
                result=row[12], error_message=row[13], created_by=row[14],
                last_updated=row[15]
            )

class TaskDistributor:
    def __init__(self, database: AgentTaskDatabase):
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
                self.database.add_agent(agent_config)
                
    async def distribute_task(self, task_type: str, title: str, description: str, 
                            priority: int = 2, assigned_to: str = None) -> str:
        """Distribute a task to the most suitable agent"""
        
        # If agent specified, assign to that agent
        if assigned_to:
            agent_id = assigned_to
        else:
            # Find the best agent for this task type
            agent_id = await self.find_best_agent(task_type)
            
        if not agent_id:
            raise ValueError("No suitable agent found for this task")
            
        # Create the task
        task_id = str(uuid.uuid4())
        task = AgentTask(
            id=task_id,
            agent_id=agent_id,
            title=title,
            description=description,
            priority=priority,
            status='pending',
            progress=0.0,
            assigned_at=datetime.now().isoformat(),
            started_at=None,
            completed_at=None,
            estimated_duration=self.estimate_task_duration(task_type),
            actual_duration=None,
            dependencies=[],
            result=None,
            error_message=None,
            created_by='system',
            last_updated=datetime.now().isoformat()
        )
        
        # Add task to database
        self.database.create_task(task)
        
        # Notify the agent (in real implementation, this would trigger the agent)
        await self.notify_agent(agent_id, task_id)
        
        return task_id
        
    async def find_best_agent(self, task_type: str) -> Optional[str]:
        """Find the best agent for a specific task type"""
        
        # Task type to agent mapping
        task_mapping = {
            'system_design': ['cto-leader', 'sa-architect', 'softarch-lead'],
            'business_analysis': ['ba-strategist', 'uiux-researcher', 'cto-leader'],
            'development': ['leaddeveloper-tech', 'seniordeveloper-code', 'juniorddeveloper-learning'],
            'testing': ['qa-quality', 'seniordeveloper-code'],
            'infrastructure': ['sysadmin-infrastructure', 'devops-automation', 'dba-data'],
            'performance': ['dba-data', 'devops-automation', 'seniordeveloper-code'],
            'ui_ux': ['uiux-researcher', 'ba-strategist'],
            'general': ['team-coordinator']
        }
        
        suitable_agents = task_mapping.get(task_type, ['team-coordinator'])
        
        # Find the agent with least workload
        best_agent = None
        min_workload = float('inf')
        
        for agent_id in suitable_agents:
            try:
                workload = self.database.get_agent_workload(agent_id)
                
                # Check if agent can take more tasks
                if workload.active_count < workload.max_concurrent:
                    if workload.active_count < min_workload:
                        min_workload = workload.active_count
                        best_agent = agent_id
            except ValueError:
                continue
                
        return best_agent
        
    def estimate_task_duration(self, task_type: str) -> int:
        """Estimate task duration in seconds"""
        durations = {
            'system_design': 600,  # 10 minutes
            'business_analysis': 300,  # 5 minutes
            'development': 900,  # 15 minutes
            'testing': 180,  # 3 minutes
            'infrastructure': 240,  # 4 minutes
            'performance': 360,  # 6 minutes
            'ui_ux': 420,  # 7 minutes
            'general': 60  # 1 minute
        }
        
        return durations.get(task_type, 300)
        
    async def notify_agent(self, agent_id: str, task_id: str):
        """Notify agent about new task (in real implementation)"""
        # This would trigger the agent to start working on the task
        # For now, we'll just update the task status
        self.database.update_task_status(task_id, 'assigned')
        
    async def process_agent_heartbeat(self, agent_id: str):
        """Process agent heartbeat and assign next task"""
        try:
            # Update agent heartbeat
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE agents 
                    SET last_heartbeat = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (agent_id,))
                conn.commit()
            
            # Get next task for this agent
            next_task = self.database.get_next_task(agent_id)
            
            if next_task:
                # Start working on the task
                self.database.update_task_status(next_task.id, 'working', 10.0)
                
                # Simulate task processing (in real implementation, agent would work on it)
                asyncio.create_task(self.simulate_task_completion(next_task))
                
        except Exception as e:
            logging.error(f"Error processing agent heartbeat for {agent_id}: {e}")
            
    async def simulate_task_completion(self, task: AgentTask):
        """Simulate task completion (replace with real agent work)"""
        try:
            # Simulate work time based on estimated duration
            work_time = task.estimated_duration / 10  # Complete 10% per simulated cycle
            
            for progress in range(10, 101, 10):
                await asyncio.sleep(work_time / 10)
                self.database.update_task_status(task.id, 'working', progress)
                
            # Mark task as completed
            result = f"Task '{task.title}' completed successfully by agent {task.agent_id}"
            self.database.update_task_status(task.id, 'completed', 100.0, result)
            
            # Process next task for this agent
            await self.process_agent_heartbeat(task.agent_id)
            
        except Exception as e:
            error_msg = f"Task failed: {str(e)}"
            self.database.update_task_status(task.id, 'failed', None, error_msg)

class AgentTaskSystem:
    def __init__(self):
        self.database = AgentTaskDatabase(Config.DATABASE_PATH)
        self.distributor = TaskDistributor(self.database)
        
    async def start(self):
        """Start the task distribution system"""
        logging.info("🚀 Starting Agent Task Distribution System")
        
        # Start heartbeat processing for all agents
        while True:
            try:
                # Get all agents
                with sqlite3.connect(Config.DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM agents')
                    agent_ids = [row[0] for row in cursor.fetchall()]
                
                # Process heartbeat for each agent
                for agent_id in agent_ids:
                    await self.distributor.process_agent_heartbeat(agent_id)
                
                await asyncio.sleep(Config.REFRESH_INTERVAL)
                
            except Exception as e:
                logging.error(f"Error in task distribution system: {e}")
                await asyncio.sleep(Config.REFRESH_INTERVAL)

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        # Initialize database and agents
        db = AgentTaskDatabase(Config.DATABASE_PATH)
        distributor = TaskDistributor(db)
        print("✅ Agent Task System initialized")
        sys.exit(0)
    
    # Start the system
    system = AgentTaskSystem()
    
    print("🚀 Starting Agent Task Distribution System...")
    print("📊 Task distribution is now active")
    print("🔄 Each agent will work on their assigned tasks")
    
    asyncio.run(system.start())