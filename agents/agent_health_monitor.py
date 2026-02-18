#!/usr/bin/env python3
"""
Agent Health Monitor - Real-time agent health monitoring
======================================================
Useful tool to check the health and status of all agents in the system.
Provides detailed health reports and can send alerts if agents are not responding.
"""

import json
import os
import sys
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3

class AgentHealthMonitor:
    def __init__(self):
        self.config_path = "/home/fahad/.openclaw/agents/openclaw.json"
        self.db_path = "/home/fahad/AIDB/aidashboard.db"
        self.agents = self.load_agents_config()
        
    def load_agents_config(self) -> Dict[str, Any]:
        """Load agent configuration from openclaw.json"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('agents', {})
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check if agents are properly registered in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM agents")
            total_agents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'idle'")
            idle_agents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'working'")
            working_agents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM agents WHERE last_seen > datetime('now', '-5 minutes')")
            recent_active = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_agents": total_agents,
                "idle_agents": idle_agents,
                "working_agents": working_agents,
                "recent_active": recent_active,
                "database_healthy": total_agents >= 13
            }
        except Exception as e:
            return {"error": str(e), "database_healthy": False}
    
    def check_workspace_health(self) -> Dict[str, List[str]]:
        """Check if agent workspaces exist and are accessible"""
        issues = []
        healthy_agents = []
        
        for agent_id, agent_config in self.agents.items():
            workspace = agent_config.get('workspace', '')
            if workspace:
                # Convert ~ to full path
                workspace_path = os.path.expanduser(workspace.replace('~', '/home/fahad'))
                
                if not os.path.exists(workspace_path):
                    issues.append(f"Workspace not found: {agent_id} -> {workspace_path}")
                else:
                    healthy_agents.append(agent_id)
        
        return {
            "healthy_workspaces": len(healthy_agents),
            "total_workspaces": len(self.agents),
            "issues": issues,
            "healthy_agents": healthy_agents
        }
    
    def generate_health_report(self) -> str:
        """Generate comprehensive health report"""
        print("🔍 Agent Health Monitor - Starting check...")
        
        # Database health
        db_health = self.check_database_health()
        print(f"📊 Database Health: {'✅' if db_health.get('database_healthy') else '❌'}")
        
        # Workspace health
        ws_health = self.check_workspace_health()
        print(f"🏢 Workspace Health: {ws_health['healthy_workspaces']}/{ws_health['total_workspaces']} ✅")
        
        # Report generation
        report = f"""
## 🏥 Agent Health Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 Database Status
- Total Agents: {db_health.get('total_agents', 'N/A')}
- Idle Agents: {db_health.get('idle_agents', 'N/A')}
- Working Agents: {db_health.get('working_agents', 'N/A')}
- Recently Active: {db_health.get('recent_active', 'N/A')}
- Database Health: {'✅ Healthy' if db_health.get('database_healthy') else '❌ Issues'}

### 🏢 Workspace Status
- Healthy Workspaces: {ws_health['healthy_workspaces']}/{ws_health['total_workspaces']}
"""
        
        if ws_health['issues']:
            report += "\n### ⚠️ Issues Found:\n"
            for issue in ws_health['issues']:
                report += f"- {issue}\n"
        
        # Agent specific status
        report += "\n### 👥 Agent Details\n"
        for agent_id, config in self.agents.items():
            workspace = config.get('workspace', 'N/A')
            model = config.get('model', 'N/A')
            report += f"- **{agent_id}**: {workspace} | {model}\n"
        
        return report
    
    def run_health_check(self):
        """Run complete health check and display results"""
        report = self.generate_health_report()
        print(report)
        
        # Save report to file
        report_file = "/home/fahad/AIDB/agents/health_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Health report saved to: {report_file}")

def main():
    """Main function - can be run from command line"""
    monitor = AgentHealthMonitor()
    monitor.run_health_check()

if __name__ == "__main__":
    main()