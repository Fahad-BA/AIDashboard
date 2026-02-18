#!/usr/bin/env python3
"""
Agent Backup & Restore System
============================
Complete backup and restore solution for agent configurations,
workspaces, and associated data.

Features:
- Full agent configuration backup
- Workspace directory backup
- Database backup
- Scheduled backups
- Restore from any backup
- Backup verification
"""

import json
import os
import shutil
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import tarfile
import hashlib

class AgentBackupSystem:
    def __init__(self):
        self.backup_root = "/home/fahad/AIDB/agents/backups"
        self.config_path = "/home/fahad/.openclaw/agents/openclaw.json"
        self.db_path = "/home/fahad/AIDB/aidashboard.db"
        self.workspaces_path = "/home/fahad/.openclaw/agents"
        
        # Create backup directory structure
        os.makedirs(self.backup_root, exist_ok=True)
        os.makedirs(os.path.join(self.backup_root, "config"), exist_ok=True)
        os.makedirs(os.path.join(self.backup_root, "workspaces"), exist_ok=True)
        os.makedirs(os.path.join(self.backup_root, "database"), exist_ok=True)
        os.makedirs(os.path.join(self.backup_root, "full"), exist_ok=True)
    
    def create_timestamp(self) -> str:
        """Create timestamp string for backup naming"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def backup_configuration(self, timestamp: str = None) -> str:
        """Backup agent configuration"""
        if timestamp is None:
            timestamp = self.create_timestamp()
        
        backup_file = os.path.join(self.backup_root, "config", f"agents_config_{timestamp}.json")
        
        # Copy configuration file
        shutil.copy2(self.config_path, backup_file)
        
        # Calculate hash for verification
        file_hash = self.calculate_file_hash(backup_file)
        
        # Create metadata
        metadata = {
            "backup_type": "configuration",
            "timestamp": timestamp,
            "original_file": self.config_path,
            "backup_file": backup_file,
            "file_hash": file_hash,
            "file_size": os.path.getsize(backup_file),
            "created_by": "agent_backup_system"
        }
        
        metadata_file = backup_file.replace(".json", "_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Configuration backup created: {backup_file}")
        return backup_file
    
    def backup_database(self, timestamp: str = None) -> str:
        """Backup AIDB database"""
        if timestamp is None:
            timestamp = self.create_timestamp()
        
        backup_file = os.path.join(self.backup_root, "database", f"aidashboard_{timestamp}.db")
        
        # Use sqlite3 backup command
        try:
            # Connect to the source database
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_file)
            
            # Create backup
            source.backup(backup)
            
            source.close()
            backup.close()
            
            file_hash = self.calculate_file_hash(backup_file)
            
            metadata = {
                "backup_type": "database",
                "timestamp": timestamp,
                "original_file": self.db_path,
                "backup_file": backup_file,
                "file_hash": file_hash,
                "file_size": os.path.getsize(backup_file),
                "created_by": "agent_backup_system"
            }
            
            metadata_file = backup_file.replace(".db", "_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Database backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ Database backup failed: {e}")
            return None
    
    def backup_workspaces(self, timestamp: str = None) -> str:
        """Backup agent workspaces"""
        if timestamp is None:
            timestamp = self.create_timestamp()
        
        backup_dir = os.path.join(self.backup_root, "workspaces", f"workspaces_{timestamp}")
        
        try:
            # Copy entire workspaces directory
            shutil.copytree(self.workspaces_path, backup_dir)
            
            # Create tar.gz archive
            archive_file = backup_dir + ".tar.gz"
            with tarfile.open(archive_file, "w:gz") as tar:
                tar.add(backup_dir, arcname=os.path.basename(backup_dir))
            
            # Remove the uncompressed directory
            shutil.rmtree(backup_dir)
            
            file_hash = self.calculate_file_hash(archive_file)
            
            metadata = {
                "backup_type": "workspaces",
                "timestamp": timestamp,
                "original_path": self.workspaces_path,
                "backup_file": archive_file,
                "file_hash": file_hash,
                "file_size": os.path.getsize(archive_file),
                "created_by": "agent_backup_system"
            }
            
            metadata_file = archive_file.replace(".tar.gz", "_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Workspaces backup created: {archive_file}")
            return archive_file
            
        except Exception as e:
            print(f"❌ Workspaces backup failed: {e}")
            return None
    
    def create_full_backup(self, timestamp: str = None) -> dict:
        """Create complete backup of everything"""
        if timestamp is None:
            timestamp = self.create_timestamp()
        
        print(f"🚀 Creating full backup: {timestamp}")
        
        results = {
            "timestamp": timestamp,
            "configuration": self.backup_configuration(timestamp),
            "database": self.backup_database(timestamp),
            "workspaces": self.backup_workspaces(timestamp)
        }
        
        # Create combined backup info file
        info_file = os.path.join(self.backup_root, "full", f"backup_info_{timestamp}.json")
        with open(info_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"🎉 Full backup completed: {info_file}")
        return results
    
    def restore_configuration(self, backup_file: str):
        """Restore agent configuration from backup"""
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        # Create backup of current config first
        current_timestamp = self.create_timestamp()
        self.backup_configuration(current_timestamp)
        
        try:
            # Restore configuration
            shutil.copy2(backup_file, self.config_path)
            print(f"✅ Configuration restored from: {backup_file}")
            return True
        except Exception as e:
            print(f"❌ Configuration restore failed: {e}")
            return False
    
    def restore_database(self, backup_file: str):
        """Restore database from backup"""
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        # Create backup of current database first
        current_timestamp = self.create_timestamp()
        self.backup_database(current_timestamp)
        
        try:
            # Stop dashboard service first
            subprocess.run(["sudo", "systemctl", "stop", "aidashboard"], check=True)
            
            # Replace database file
            shutil.copy2(backup_file, self.db_path)
            
            # Start dashboard service
            subprocess.run(["sudo", "systemctl", "start", "aidashboard"], check=True)
            
            print(f"✅ Database restored from: {backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ Database restore failed: {e}")
            return False
    
    def restore_workspaces(self, backup_file: str):
        """Restore workspaces from backup"""
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        try:
            # Extract backup
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=os.path.dirname(self.workspaces_path))
            
            print(f"✅ Workspaces restored from: {backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ Workspaces restore failed: {e}")
            return False
    
    def verify_backup(self, backup_file: str) -> bool:
        """Verify backup integrity"""
        metadata_file = backup_file.replace(
            os.path.splitext(backup_file)[1], 
            "_metadata.json"
        )
        
        if not os.path.exists(metadata_file):
            print(f"❌ Metadata file not found for: {backup_file}")
            return False
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Verify file hash
            current_hash = self.calculate_file_hash(backup_file)
            original_hash = metadata.get('file_hash')
            
            if current_hash != original_hash:
                print(f"❌ Backup verification failed: Hash mismatch")
                return False
            
            # Verify file exists and is readable
            if not os.path.exists(backup_file):
                print(f"❌ Backup file not accessible: {backup_file}")
                return False
            
            print(f"✅ Backup verified: {backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ Backup verification failed: {e}")
            return False
    
    def list_backups(self, backup_type: str = "all"):
        """List available backups"""
        backups = {
            "configuration": [],
            "database": [],
            "workspaces": [],
            "full": []
        }
        
        if backup_type == "all" or backup_type == "configuration":
            config_dir = os.path.join(self.backup_root, "config")
            if os.path.exists(config_dir):
                backups["configuration"] = [f for f in os.listdir(config_dir) if f.endswith("_metadata.json")]
        
        if backup_type == "all" or backup_type == "database":
            db_dir = os.path.join(self.backup_root, "database")
            if os.path.exists(db_dir):
                backups["database"] = [f for f in os.listdir(db_dir) if f.endswith("_metadata.json")]
        
        if backup_type == "all" or backup_type == "workspaces":
            ws_dir = os.path.join(self.backup_root, "workspaces")
            if os.path.exists(ws_dir):
                backups["workspaces"] = [f for f in os.listdir(ws_dir) if f.endswith("_metadata.json")]
        
        return backups

def main():
    parser = argparse.ArgumentParser(description="Agent Backup & Restore System")
    parser.add_argument('action', choices=[
        'backup', 'restore', 'verify', 'list'
    ], help='Action to perform')
    
    parser.add_argument('--type', choices=[
        'config', 'database', 'workspaces', 'full', 'all'
    ], default='full', help='Backup/restore type')
    
    parser.add_argument('--file', help='Backup file to restore/verify')
    parser.add_argument('--timestamp', help='Backup timestamp')
    
    args = parser.parse_args()
    
    backup_system = AgentBackupSystem()
    
    if args.action == 'backup':
        if args.type == 'full' or args.type == 'all':
            backup_system.create_full_backup(args.timestamp)
        elif args.type == 'config':
            backup_system.backup_configuration(args.timestamp)
        elif args.type == 'database':
            backup_system.backup_database(args.timestamp)
        elif args.type == 'workspaces':
            backup_system.backup_workspaces(args.timestamp)
    
    elif args.action == 'restore':
        if not args.file:
            print("❌ restore action requires --file")
            return
        
        if args.type == 'config':
            backup_system.restore_configuration(args.file)
        elif args.type == 'database':
            backup_system.restore_database(args.file)
        elif args.type == 'workspaces':
            backup_system.restore_workspaces(args.file)
    
    elif args.action == 'verify':
        if not args.file:
            print("❌ verify action requires --file")
            return
        
        backup_system.verify_backup(args.file)
    
    elif args.action == 'list':
        backups = backup_system.list_backups(args.type)
        
        for backup_type, files in backups.items():
            print(f"\n📁 {backup_type.upper()} Backups:")
            if files:
                for file in sorted(files, reverse=True):
                    print(f"   - {file}")
            else:
                print("   (No backups found)")

if __name__ == "__main__":
    main()