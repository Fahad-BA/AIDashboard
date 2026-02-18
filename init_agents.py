#!/usr/bin/env python3
"""
Initialize agents in AIDB database
"""

import sys
import os
sys.path.append('/home/fahad/AIDB')

from app import AIDatabase, AgentMonitor

def main():
    print("🔧 Initializing agents in AIDB database...")
    
    # Initialize database
    db = AIDatabase('/home/fahad/AIDB/aidashboard.db')
    
    # Initialize agent monitor
    monitor = AgentMonitor(db)
    
    # Check agents configuration
    agents_config = monitor.load_agents_config()
    agents_list = agents_config.get('agents', {}).get('list', [])
    
    print(f"📋 Found {len(agents_list)} agents in configuration")
    
    # If no agents in list format, try to get from agents dict
    if not agents_list:
        agents_dict = agents_config.get('agents', {})
        agents_list = []
        for agent_id, agent_config in agents_dict.items():
            if isinstance(agent_config, dict) and 'id' in agent_config:
                agents_list.append(agent_config)
            else:
                # Convert to expected format
                agent_config['id'] = agent_id
                agents_list.append(agent_config)
    
    print(f"🔄 Processing {len(agents_list)} agents...")
    
    # Manually create agents
    for i, agent_config in enumerate(agents_list):
        agent_id = agent_config.get('id')
        agent_name = agent_config.get('name', agent_id)
        model = agent_config.get('model', 'unknown')
        workspace = agent_config.get('workspace', '')
        
        print(f"  {i+1}. Creating agent: {agent_name} ({agent_id})")
        
        try:
            # Create agent in database
            monitor._create_agent_if_not_exists(agent_config)
            print(f"     ✅ Created successfully")
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    # Verify agents were created
    agents = db.get_agents()
    print(f"✅ Total agents in database: {len(agents)}")
    
    for agent in agents:
        print(f"   - {agent.name} ({agent.id}) - {agent.status}")

if __name__ == '__main__':
    main()