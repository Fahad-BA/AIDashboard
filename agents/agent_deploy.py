#!/usr/bin/env python3
"""
Agent Deployment Tool - Deploy and manage agents
================================================
This tool can:
- Deploy new agents to workspaces
- Update existing agent configurations
- Backup agent configurations
- Restore agents from backup
- Validate agent workspaces and configurations
"""

import json
import os
import shutil
import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys

class AgentDeployer:
    def __init__(self):
        self.config_path = "/home/fahad/.openclaw/agents/openclaw.json"
        self.base_workspace = "/home/fahad/.openclaw/agents"
        self.backup_dir = "/home/fahad/AIDB/agents/backups"
        self.templates_dir = "/home/fahad/AIDB/agents/templates"
        
        # Ensure directories exist
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
    def load_config(self) -> dict:
        """Load agent configuration"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_config(self, config: dict):
        """Save agent configuration"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Configuration saved")
    
    def create_workspace(self, agent_id: str, workspace_type: str = "standard") -> bool:
        """Create a new agent workspace"""
        workspace_path = os.path.join(self.base_workspace, f"workspace-{agent_id}")
        
        if os.path.exists(workspace_path):
            print(f"⚠️  Workspace already exists: {workspace_path}")
            return False
        
        os.makedirs(workspace_path, exist_ok=True)
        
        # Create basic workspace structure
        structure = [
            "SOUL.md",
            "TOOLS.md", 
            "memory/",
            "projects/",
            "logs/"
        ]
        
        for item in structure:
            path = os.path.join(workspace_path, item)
            if item.endswith('/'):
                os.makedirs(path, exist_ok=True)
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    if item == "SOUL.md":
                        f.write(f"# SOUL.md - {agent_id}\n\nWho are you?\n\n*Created on {datetime.now().strftime('%Y-%m-%d')}*\n")
                    elif item == "TOOLS.md":
                        f.write(f"# TOOLS.md - {agent_id}\n\nLocal configuration and tools\n")
        
        print(f"✅ Created workspace: {workspace_path}")
        return True
    
    def deploy_agent(self, agent_id: str, name: str, model: str, description: str, workspace: str = None):
        """Deploy a new agent"""
        config = self.load_config()
        
        # Create workspace if needed
        if workspace:
            workspace_name = workspace
        else:
            workspace_name = f"workspace-{agent_id}"
        
        workspace_path = os.path.join(self.base_workspace, workspace_name)
        
        # Create workspace directory
        self.create_workspace(agent_id)
        
        # Add agent to config
        agents = config.get('agents', {})
        agents[agent_id] = {
            "id": agent_id,
            "name": name,
            "model": model,
            "description": description,
            "workspace": f"~/.openclaw/agents/{workspace_name}"
        }
        
        # Update workspaces section
        workspaces = config.get('workspaces', {})
        workspaces[workspace_name] = {
            "path": f"~/.openclaw/agents/{workspace_name}",
            "description": f"{name} workspace"
        }
        
        config['agents'] = agents
        config['workspaces'] = workspaces
        
        self.save_config(config)
        print(f"🚀 Agent '{agent_id}' deployed successfully!")
    
    def backup_agents(self):
        """Create backup of all agent configurations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"agents_backup_{timestamp}.json")
        
        config = self.load_config()
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Backup created: {backup_file}")
        
        # Also backup workspace directories if they exist
        workspace_backup = os.path.join(self.backup_dir, f"workspaces_{timestamp}")
        if os.path.exists(self.base_workspace):
            shutil.copytree(self.base_workspace, workspace_backup)
            print(f"💾 Workspaces backup: {workspace_backup}")
    
    def restore_agents(self, backup_file: str):
        """Restore agents from backup"""
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Create backup of current config first
        self.backup_agents()
        
        # Restore configuration
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Agents restored from: {backup_file}")
    
    def validate_agents(self):
        """Validate all agent configurations and workspaces"""
        config = self.load_config()
        agents = config.get('agents', {})
        
        print("🔍 Validating agents...")
        
        issues = []
        valid_agents = []
        
        for agent_id, agent_config in agents.items():
            # Check workspace
            workspace = agent_config.get('workspace', '')
            if workspace:
                workspace_path = os.path.expanduser(workspace.replace('~', '/home/fahad'))
                if not os.path.exists(workspace_path):
                    issues.append(f"Missing workspace: {agent_id} -> {workspace_path}")
                else:
                    valid_agents.append(agent_id)
            
            # Check required fields
            required_fields = ['id', 'name', 'model']
            for field in required_fields:
                if field not in agent_config:
                    issues.append(f"Missing field '{field}' in agent: {agent_id}")
        
        print(f"✅ Valid agents: {len(valid_agents)}/{len(agents)}")
        if issues:
            print("⚠️  Issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("🎉 All agents are valid!")
    
    def list_agents(self):
        """List all agents with details"""
        config = self.load_config()
        agents = config.get('agents', {})
        
        print("📋 Agent List:")
        print("-" * 80)
        
        for agent_id, agent_config in agents.items():
            name = agent_config.get('name', 'N/A')
            model = agent_config.get('model', 'N/A')
            workspace = agent_config.get('workspace', 'N/A')
            description = agent_config.get('description', 'N/A')
            
            print(f"👤 {agent_id}")
            print(f"   Name: {name}")
            print(f"   Model: {model}")
            print(f"   Workspace: {workspace}")
            print(f"   Description: {description}")
            print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Agent Deployment Tool")
    parser.add_argument('action', choices=[
        'deploy', 'backup', 'restore', 'validate', 'list'
    ], help='Action to perform')
    
    parser.add_argument('--id', help='Agent ID (for deploy)')
    parser.add_argument('--name', help='Agent name (for deploy)')
    parser.add_argument('--model', help='Agent model (for deploy)')
    parser.add_argument('--description', help='Agent description (for deploy)')
    parser.add_argument('--workspace', help='Workspace name (for deploy)')
    parser.add_argument('--backup-file', help='Backup file to restore from (for restore)')
    
    args = parser.parse_args()
    
    deployer = AgentDeployer()
    
    if args.action == 'deploy':
        if not all([args.id, args.name, args.model]):
            print("❌ deploy action requires: --id, --name, --model")
            return
        deployer.deploy_agent(args.id, args.name, args.model, args.description, args.workspace)
    
    elif args.action == 'backup':
        deployer.backup_agents()
    
    elif args.action == 'restore':
        if not args.backup_file:
            print("❌ restore action requires: --backup-file")
            return
        deployer.restore_agents(args.backup_file)
    
    elif args.action == 'validate':
        deployer.validate_agents()
    
    elif args.action == 'list':
        deployer.list_agents()

if __name__ == "__main__":
    main()