#!/usr/bin/env python3
"""
Sync Agent Performance Data from JSON to Database
"""

import json
import sqlite3
import os
from datetime import datetime
import logging

# Configuration
DATABASE_PATH = "/home/fahad/AIDB/aidashboard.db"
PERFORMANCE_DATA_PATH = "/home/fahad/AIDB/agents/agent_performance.json"

def sync_performance_data():
    """Sync performance data from JSON file to database"""
    
    if not os.path.exists(PERFORMANCE_DATA_PATH):
        print(f"Performance data file not found: {PERFORMANCE_DATA_PATH}")
        return False
    
    # Load performance data
    with open(PERFORMANCE_DATA_PATH, 'r') as f:
        performance_data = json.load(f)
    
    if 'agents_performance' not in performance_data:
        print("No agents_performance data found in JSON file")
        return False
    
    agents_performance = performance_data['agents_performance']
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    synced_count = 0
    
    try:
        for agent_id, agent_data in agents_performance.items():
            # Check if agent exists in database
            cursor.execute('SELECT id FROM agents WHERE id = ?', (agent_id,))
            if not cursor.fetchone():
                print(f"Agent {agent_id} not found in database, skipping...")
                continue
            
            # Update agent with performance data
            cursor.execute('''
                UPDATE agents 
                SET cpu_usage = ?, memory_usage = ?, response_time = ?, last_seen = ?
                WHERE id = ?
            ''', (
                agent_data.get('cpu_usage', 0.0),
                agent_data.get('memory_usage', 0.0),
                agent_data.get('average_response_time', 0.0),
                agent_data.get('last_active', datetime.now().isoformat()),
                agent_id
            ))
            
            synced_count += 1
            print(f"Synced performance data for agent: {agent_id}")
        
        conn.commit()
        print(f"Successfully synced performance data for {synced_count} agents")
        return True
        
    except Exception as e:
        print(f"Error syncing performance data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Syncing agent performance data...")
    success = sync_performance_data()
    
    if success:
        print("Performance data sync completed successfully!")
    else:
        print("Performance data sync failed!")
    
    exit(0 if success else 1)