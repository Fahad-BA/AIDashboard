#!/usr/bin/env python3
"""
Download and Store Agent Avatar Images
"""

import json
import sqlite3
import os
import requests
import urllib.parse
from pathlib import Path

# Configuration
DATABASE_PATH = "/home/fahad/AIDB/aidashboard.db"
STATIC_IMG_PATH = "/home/fahad/AIDB/static/img"
DEFAULT_AVATARS = {
    "cto-leader": "https://ui-avatars.com/api/?name=CTO+Leader&background=667eea&color=fff&size=80",
    "ba-strategist": "https://ui-avatars.com/api/?name=BA+Strategist&background=764ba2&color=fff&size=80",
    "sa-architect": "https://ui-avatars.com/api/?name=SA+Architect&background=f093fb&color=fff&size=80",
    "sysadmin-infrastructure": "https://ui-avatars.com/api/?name=SysAdmin&background=4facfe&color=fff&size=80",
    "dba-data": "https://ui-avatars.com/api/?name=DBA+Data&background=43e97b&color=fff&size=80",
    "devops-automation": "https://ui-avatars.com/api/?name=DevOps&background=fa709a&color=fff&size=80",
    "softarch-lead": "https://ui-avatars.com/api/?name=Architect&background=fed330&color=fff&size=80",
    "leaddeveloper-tech": "https://ui-avatars.com/api/?name=Lead+Dev&background=30cfd0&color=fff&size=80",
    "seniordeveloper-code": "https://ui-avatars.com/api/?name=Senior+Dev&background=a8edea&color=fff&size=80",
    "juniorddeveloper-learning": "https://ui-avatars.com/api/?name=Junior+Dev&background=d299c2&color=fff&size=80",
    "qa-quality": "https://ui-avatars.com/api/?name=QA+Quality&background=89f7fe&color=fff&size=80",
    "uiux-researcher": "https://ui-avatars.com/api/?name=UIUX+Research&background=667eea&color=fff&size=80",
    "team-coordinator": "https://ui-avatars.com/api/?name=Team+Coord&background=764ba2&color=fff&size=80"
}

def download_avatar(agent_id, avatar_url):
    """Download avatar image and save to static folder"""
    try:
        # Create safe filename
        safe_filename = f"avatar_{agent_id.replace('-', '_')}.png"
        save_path = os.path.join(STATIC_IMG_PATH, safe_filename)
        
        # Skip if file already exists
        if os.path.exists(save_path):
            print(f"Avatar already exists for {agent_id}: {safe_filename}")
            return f"/static/img/{safe_filename}"
        
        # Download the image
        response = requests.get(avatar_url, timeout=10)
        response.raise_for_status()
        
        # Save the image
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded avatar for {agent_id}: {safe_filename}")
        return f"/static/img/{safe_filename}"
        
    except Exception as e:
        print(f"Error downloading avatar for {agent_id}: {e}")
        return "/static/img/default-agent.png"

def setup_agent_avatars():
    """Setup avatars for all agents"""
    
    # Ensure static/img directory exists
    os.makedirs(STATIC_IMG_PATH, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    updated_count = 0
    
    try:
        # Get all agents
        cursor.execute('SELECT id FROM agents')
        agents = cursor.fetchall()
        
        for agent_row in agents:
            agent_id = agent_row[0]
            
            # Get avatar URL from customizations or use default
            cursor.execute('''
                SELECT avatar_url FROM agent_customizations WHERE agent_id = ?
            ''', (agent_id,))
            
            custom_avatar = cursor.fetchone()
            
            if custom_avatar and custom_avatar[0]:
                # Use custom avatar URL if it exists
                avatar_url = custom_avatar[0]
            else:
                # Use default avatar URL
                avatar_url = DEFAULT_AVATARS.get(agent_id, DEFAULT_AVATARS['leaddeveloper-tech'])
            
            # Download or use existing avatar
            avatar_path = download_avatar(agent_id, avatar_url)
            
            # Update agent customization with local avatar path
            cursor.execute('''
                INSERT OR REPLACE INTO agent_customizations 
                (agent_id, nickname, title, avatar_url, custom_data)
                VALUES (?, ?, ?, ?, '{}')
            ''', (agent_id, None, None, avatar_path))
            
            # Also update the main agents table
            cursor.execute('''
                UPDATE agents SET avatar = ? WHERE id = ?
            ''', (avatar_path, agent_id))
            
            updated_count += 1
        
        conn.commit()
        print(f"Successfully updated avatars for {updated_count} agents")
        return True
        
    except Exception as e:
        print(f"Error setting up avatars: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Setting up agent avatars...")
    success = setup_agent_avatars()
    
    if success:
        print("Avatar setup completed successfully!")
    else:
        print("Avatar setup failed!")
    
    exit(0 if success else 1)