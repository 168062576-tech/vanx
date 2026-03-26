"""
storage.py - SQLite 持久化层
虚拟 Agent 世界 v3.0

功能：
1. Agent 数据持久化（存/取/批量）
2. 事件持久化 + 自动归档
3. 世界快照（存档/读档）
4. 自动备份

依赖：仅 Python 标准库（sqlite3, json, datetime, shutil）
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict


class SQLiteStore:
    """SQLite 持久化存储"""

    def __init__(self, db_path: str = "world.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")  # 写性能优化
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._create_tables()

    def _create_tables(self):
        """创建所有表"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                education_level TEXT,
                education_status TEXT,
                occupation TEXT,
                income REAL DEFAULT 0,
                net_worth REAL DEFAULT 0,
                health_score REAL DEFAULT 80,
                mental_health REAL DEFAULT 70,
                happiness REAL DEFAULT 50,
                marital_status TEXT DEFAULT 'single',
                spouse_id INTEGER DEFAULT -1,
                life_expectancy REAL DEFAULT 75,
                credit_score INTEGER DEFAULT 650,
                housing_status TEXT DEFAULT 'none',
                extended_data TEXT DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER,
                agent_id INTEGER,
                event_type TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_agent ON events(agent_id);
            CREATE INDEX IF NOT EXISTS idx_events_month ON events(month);

            CREATE TABLE IF NOT EXISTS world_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                month INTEGER,
                agent_count INTEGER,
                config TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self.conn.commit()

    # ── Agent 操作 ──

    def save_agent(self, agent) -> None:
        """保存单个 Agent"""
        ext = {}
        for attr in ['skills', 'talents', 'hobbies', 'diseases', 'children_ids',
                      'close_friends', 'personality_type']:
            if hasattr(agent, attr):
                val = getattr(agent, attr)
                if val is not None:
                    ext[attr] = val

        self.conn.execute("""
            INSERT OR REPLACE INTO agents 
            (id, age, gender, education_level, education_status, occupation,
             income, net_worth, health_score, mental_health, happiness,
             marital_status, spouse_id, life_expectancy, credit_score,
             housing_status, extended_data, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent.id, agent.age, agent.gender,
            getattr(agent, 'education_level', ''),
            getattr(agent, 'education_status', ''),
            getattr(agent, 'occupation', ''),
            getattr(agent, 'income', 0),
            getattr(agent, 'net_worth', 0),
            getattr(agent, 'health_score', 80),
            getattr(agent, 'mental_health', 70),
            getattr(agent, 'happiness', 50),
            getattr(agent, 'marital_status', 'single'),
            getattr(agent, 'spouse_id', -1),
            getattr(agent, 'life_expectancy', 75),
            getattr(agent, 'credit_score', 650),
            getattr(agent, 'housing_status', 'none'),
            json.dumps(ext, ensure_ascii=False),
            datetime.now().isoformat()
        ))

    def save_agents_batch(self, agents) -> int:
        """批量保存 Agent（事务内执行）"""
        count = 0
        with self.conn:
            for agent in agents:
                self.save_agent(agent)
                count += 1
        return count

    def load_agent_data(self, agent_id: int) -> Optional[Dict]:
        """加载单个 Agent 数据"""
        row = self.conn.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            return None
        return dict(row)

    def load_all_agent_data(self) -> List[Dict]:
        """加载所有 Agent 数据"""
        rows = self.conn.execute("SELECT * FROM agents ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def agent_count(self) -> int:
        """Agent 数量"""
        row = self.conn.execute("SELECT COUNT(*) FROM agents").fetchone()
        return row[0]

    # ── 事件操作 ──

    def save_events_batch(self, events, current_month: int = 0) -> int:
        """批量保存事件"""
        count = 0
        with self.conn:
            for evt in events:
                self.conn.execute(
                    "INSERT INTO events (month, agent_id, event_type, data) VALUES (?, ?, ?, ?)",
                    (current_month, evt.agent_id, evt.event_type,
                     json.dumps(evt.data, ensure_ascii=False) if evt.data else '{}')
                )
                count += 1
        return count

    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """获取最近事件"""
        rows = self.conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_events_by_type(self, event_type: str, limit: int = 50) -> List[Dict]:
        """按类型获取事件"""
        rows = self.conn.execute(
            "SELECT * FROM events WHERE event_type = ? ORDER BY id DESC LIMIT ?",
            (event_type, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_event_stats(self) -> Dict:
        """事件统计"""
        total = self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        types = self.conn.execute(
            "SELECT event_type, COUNT(*) as cnt FROM events GROUP BY event_type ORDER BY cnt DESC"
        ).fetchall()
        return {
            'total_events': total,
            'type_counts': {r['event_type']: r['cnt'] for r in types}
        }

    def event_count(self) -> int:
        """事件总数"""
        return self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    # ── 快照操作 ──

    def create_snapshot(self, name: str, month: int, agent_count: int, config: dict = None) -> int:
        """创建世界快照（只记录元数据，Agent 数据已在 agents 表中）"""
        cursor = self.conn.execute(
            "INSERT INTO world_snapshots (name, month, agent_count, config) VALUES (?, ?, ?, ?)",
            (name, month, agent_count, json.dumps(config or {}))
        )
        self.conn.commit()
        return cursor.lastrowid

    def list_snapshots(self) -> List[Dict]:
        """列出所有快照"""
        rows = self.conn.execute(
            "SELECT * FROM world_snapshots ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── 元数据 ──

    def set_meta(self, key: str, value: str) -> None:
        """设置元数据"""
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def get_meta(self, key: str, default: str = None) -> Optional[str]:
        """获取元数据"""
        row = self.conn.execute(
            "SELECT value FROM metadata WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    # ── 备份 ──

    def backup(self, backup_dir: str = "backups") -> str:
        """创建数据库备份"""
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"world_{timestamp}.db")
        
        # 使用 SQLite 的 backup API（安全，不会读到半写状态）
        backup_conn = sqlite3.connect(backup_path)
        self.conn.backup(backup_conn)
        backup_conn.close()
        
        return backup_path

    def close(self):
        """关闭连接"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
