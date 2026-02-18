# AIDatabase Schema Documentation

## Database: aidashboard.db

The AIDashboard uses SQLite with the following tables:

## Table: agents
Stores information about all OpenClaw agents.

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,              -- Agent ID (e.g., 'cto-leader')
    name TEXT NOT NULL,              -- Agent official name
    title TEXT,                      -- Professional title
    nickname TEXT,                   -- Custom friendly name
    model TEXT,                      -- AI model used
    status TEXT DEFAULT 'idle',      -- Current status: idle, working, error, offline
    current_task TEXT DEFAULT '',    -- Current task description
    workspace TEXT,                  -- Workspace path
    avatar TEXT,                     -- Avatar image URL
    last_seen TEXT,                  -- Last activity timestamp
    cpu_usage REAL DEFAULT 0.0,      -- CPU usage percentage
    memory_usage REAL DEFAULT 0.0,   -- Memory usage percentage  
    channel TEXT DEFAULT '',         -- Active communication channel
    response_time REAL DEFAULT 0.0,  -- Response time in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Table: server_metrics
Stores historical server performance metrics.

```sql
CREATE TABLE server_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpu_percent REAL,               -- CPU usage percentage
    memory_percent REAL,            -- Memory usage percentage
    disk_percent REAL,              -- Disk usage percentage
    load_average REAL,              -- System load average
    uptime TEXT,                    -- System uptime string
    processes INTEGER,              -- Number of running processes
    active_connections INTEGER,     -- Network connections count
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Table: tasks
Stores task information for each agent.

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,            -- Unique task ID
    agent_id TEXT,                  -- Associated agent ID
    task_name TEXT,                 -- Task description
    status TEXT,                    -- Task status: pending, running, completed, failed
    progress REAL,                  -- Progress percentage (0-100)
    started_at TIMESTAMP,           -- Task start time
    completed_at TIMESTAMP,         -- Task completion time
    channel TEXT,                   -- Communication channel
    FOREIGN KEY (agent_id) REFERENCES agents (id)
);
```

## Table: agent_customizations
Stores user-defined customizations for agents.

```sql
CREATE TABLE agent_customizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT UNIQUE,           -- Associated agent ID
    nickname TEXT,                   -- Custom nickname
    title TEXT,                     -- Custom title
    avatar_url TEXT,                -- Custom avatar URL
    custom_data TEXT,               -- JSON with additional custom data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents (id)
);
```

## Relationships

```
agents (1) -----> (N) tasks
  |
  +-----> (1) agent_customizations

server_metrics (independent table)
```

## Example Data

### agents table:
```
| id               | name              | title               | nickname   | model          | status   | current_task     | workspace                                |
|------------------|-------------------|---------------------|------------|----------------|----------|------------------|------------------------------------------|
| cto-leader       | CTO-Leader        | Chief Technology   | أبومساعد  | zai/glm-4-5   | idle     |                  | /home/fahad/.openclaw/agents/workspace-cto |
| ba-strategist    | BA-Strategist     | Business Analyst   | محلل      | zai/glm-4-air | working  | Analyzing market | /home/fahad/.openclaw/agents/workspace-ba  |
| seniordeveloper-code | SeniorDeveloper  | Senior Developer    | مساعد الصغير| zai/glm-4-air | idle     |                  | /home/fahad/.openclaw/agents/workspace-seniord |
```

### agent_customizations table:
```
| id | agent_id       | nickname   | title               | avatar_url                              |
|----|----------------|------------|---------------------|----------------------------------------|
| 1  | cto-leader     | أبومساعد  | كبير الوكلاء       | https://example.com/avatars/cto.png     |
| 2  | seniordeveloper-code | مساعد الصغير | خبير التطوير   | https://example.com/avatars/dev.png     |
```

## Database Optimization

### Indexes
The following indexes are automatically created:
- Primary keys on all tables
- Foreign key constraints where applicable
- Unique constraint on agent_customizations.agent_id

### Performance Considerations
- Use `LIMIT` for large result sets
- Consider archiving old server_metrics data
- Vacuum database periodically
- Use appropriate SQLite journaling mode

## Maintenance Queries

### Clean up old metrics (older than 30 days):
```sql
DELETE FROM server_metrics 
WHERE timestamp < datetime('now', '-30 days');
```

### Get active agents:
```sql
SELECT * FROM agents 
WHERE status = 'working' 
OR last_seen > datetime('now', '-5 minutes');
```

### Get agents with high resource usage:
```sql
SELECT id, nickname, cpu_usage, memory_usage 
FROM agents 
WHERE cpu_usage > 80 OR memory_usage > 80;
```

## Backup and Restore

### Backup:
```bash
sqlite3 aidashboard.db ".backup aidashboard_backup_$(date +%Y%m%d).db"
```

### Restore:
```bash
sqlite3 aidashboard.db < backup.sql
```

---

*Database schema is automatically created and maintained by the AIDashboard application.*