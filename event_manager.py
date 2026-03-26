"""
事件管理器 - 所有子系统间通信的中枢
支持：事件发布/订阅、事件归档、事件索引、上限控制

作者：御龙军执行司
日期：2026-03-25
版本：v1.0
"""
import time
import json
import threading
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Event:
    event_type: str
    agent_id: Optional[int]
    data: Dict[str, Any]
    source: str
    timestamp: float = field(default_factory=time.time)
    month: int = 0


class EventManager:
    """事件总线 + 归档 + 索引"""
    
    MAX_HOT_EVENTS = 50000  # 内存中保留的最大事件数
    ARCHIVE_BATCH = 10000   # 每次归档的数量
    
    def __init__(self, archive_dir: str = "./event_archive"):
        self.hot_events: List[Event] = []
        self.handlers: Dict[str, List[Callable]] = {}  # event_type -> [handler]
        self.global_handlers: List[Callable] = []  # 监听所有事件
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.archived_count = 0
        self.type_counts: Dict[str, int] = {}  # 事件类型计数
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅特定类型事件"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def subscribe_all(self, handler: Callable):
        """订阅所有事件"""
        self.global_handlers.append(handler)
    
    def emit(self, event_type: str, agent_id: Optional[int], data: Dict, source: str, month: int = 0) -> Event:
        """发布事件"""
        event = Event(event_type=event_type, agent_id=agent_id, data=data, source=source, month=month)
        
        with self._lock:
            self.hot_events.append(event)
            self.type_counts[event_type] = self.type_counts.get(event_type, 0) + 1
            
            # 超过上限时归档
            if len(self.hot_events) > self.MAX_HOT_EVENTS:
                self._archive_oldest()
        
        # 通知订阅者（非阻塞）
        for handler in self.handlers.get(event_type, []):
            try:
                handler(event)
            except Exception:
                pass
        for handler in self.global_handlers:
            try:
                handler(event)
            except Exception:
                pass
        
        return event
    
    def query(self, event_type: str = None, agent_id: int = None, 
              source: str = None, limit: int = 50) -> List[Event]:
        """查询事件"""
        with self._lock:
            events = list(self.hot_events)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if agent_id is not None:
            events = [e for e in events if e.agent_id == agent_id]
        if source:
            events = [e for e in events if e.source == source]
        return events[-limit:]
    
    def get_statistics(self) -> Dict:
        """事件统计"""
        return {
            'hot_count': len(self.hot_events),
            'archived_count': self.archived_count,
            'total_count': len(self.hot_events) + self.archived_count,
            'type_counts': dict(self.type_counts),
            'sources': list(set(e.source for e in self.hot_events[-1000:])),
        }
    
    def _archive_oldest(self):
        """归档最早的一半事件到磁盘"""
        half = len(self.hot_events) // 2
        to_archive = self.hot_events[:half]
        self.hot_events = self.hot_events[half:]
        
        filepath = self.archive_dir / f"events_{self.archived_count}_{self.archived_count + len(to_archive)}.jsonl"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for event in to_archive:
                    f.write(json.dumps({
                        'type': event.event_type,
                        'agent_id': event.agent_id,
                        'data': event.data,
                        'source': event.source,
                        'timestamp': event.timestamp,
                        'month': event.month
                    }, ensure_ascii=False) + '\n')
        except Exception:
            pass
        
        self.archived_count += len(to_archive)
    
    def get_recent_by_type(self, limit_per_type: int = 5) -> Dict[str, List]:
        """按类型获取最近事件（用于前端展示）"""
        result = {}
        for event in reversed(self.hot_events):
            t = event.event_type
            if t not in result:
                result[t] = []
            if len(result[t]) < limit_per_type:
                result[t].append({
                    'agent_id': event.agent_id,
                    'data': event.data,
                    'source': event.source,
                    'month': event.month
                })
            if all(len(v) >= limit_per_type for v in result.values()):
                break
        return result
