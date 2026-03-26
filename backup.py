"""
backup.py - 自动备份脚本
虚拟 Agent 世界 v3.0

用法：
  python backup.py                    # 立即备份
  python backup.py --cleanup 7        # 备份并清理 7 天前的旧备份
  python backup.py --list             # 列出所有备份
"""

import os
import sys
import glob
import argparse
from datetime import datetime, timedelta
from storage import SQLiteStore

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world.db")


def do_backup(db_path: str = DEFAULT_DB) -> str:
    """执行备份，返回备份文件路径"""
    if not os.path.exists(db_path):
        print(f"[SKIP] Database not found: {db_path}")
        return None

    store = SQLiteStore(db_path)
    backup_path = store.backup(BACKUP_DIR)
    agent_count = store.agent_count()
    event_count = store.event_count()
    store.close()

    size_kb = os.path.getsize(backup_path) / 1024
    print(f"[OK] Backup created: {os.path.basename(backup_path)}")
    print(f"     Agents: {agent_count}, Events: {event_count}, Size: {size_kb:.1f}KB")
    return backup_path


def list_backups():
    """列出所有备份"""
    if not os.path.exists(BACKUP_DIR):
        print("No backups found.")
        return

    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "world_*.db")))
    if not files:
        print("No backups found.")
        return

    total_size = 0
    print(f"{'File':<35} {'Size':>10} {'Date':>20}")
    print("-" * 70)
    for f in files:
        size = os.path.getsize(f)
        total_size += size
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        print(f"{os.path.basename(f):<35} {size/1024:>8.1f}KB {mtime.strftime('%Y-%m-%d %H:%M'):>20}")

    print("-" * 70)
    print(f"Total: {len(files)} backups, {total_size/1024:.1f}KB")


def cleanup_old(days: int = 7):
    """清理指定天数前的旧备份"""
    if not os.path.exists(BACKUP_DIR):
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    files = glob.glob(os.path.join(BACKUP_DIR, "world_*.db"))
    removed = 0
    for f in files:
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        if mtime < cutoff:
            os.remove(f)
            removed += 1
            print(f"[DEL] {os.path.basename(f)}")

    if removed:
        print(f"Cleaned {removed} old backups (older than {days} days)")
    else:
        print(f"No backups older than {days} days to clean")
    return removed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Virtual World Backup Tool")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--cleanup", type=int, metavar="DAYS", help="Clean backups older than N days")
    parser.add_argument("--db", default=DEFAULT_DB, help="Database path")
    args = parser.parse_args()

    if args.list:
        list_backups()
    else:
        do_backup(args.db)
        if args.cleanup:
            cleanup_old(args.cleanup)
