# -*- coding: utf-8 -*-
"""
御龙军虚拟世界 - 实验执行引擎 v2.0 (virtual_world_v5)
功能：对接实验模板 → 真实引擎执行 → 报告生成

将 experiment_templates_v2 的 24 个模板与 DeepIntegrationEngine 和
SmartReportGenerator 真正串联起来。

移植自旧版，适配 virtual_world_v5 目录结构。
"""

import sys
import os
import json
import threading
import time
import random
from datetime import datetime
from typing import Dict, List, Optional

# 使用相对路径（基于当前文件所在目录）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_THIS_DIR, 'data')
REPORTS_PATH = os.path.join(DATA_DIR, 'reports')
EXPERIMENTS_PATH = os.path.join(DATA_DIR, 'experiments')

os.makedirs(REPORTS_PATH, exist_ok=True)
os.makedirs(EXPERIMENTS_PATH, exist_ok=True)

# 相对 import（同目录下的模块）
from deep_integration_engine import DeepIntegrationEngine, UnifiedAgent
from experiment_templates_v2 import ExperimentTemplateLibrary, ExperimentTemplate
from experiment_report_generator import ExperimentReportGenerator

# 商业模块（开源版本缺失不影响核心运行）
try:
    from report_generator_v2 import SmartReportGenerator
except ImportError:
    SmartReportGenerator = None


class ExperimentStatus:
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentRunner:
    """实验执行引擎 - 真正运行实验"""

    def __init__(self):
        self.template_library = ExperimentTemplateLibrary()
        if SmartReportGenerator:
            self.report_generator = SmartReportGenerator(output_path=REPORTS_PATH)
        else:
            self.report_generator = None
        self.experiments: Dict[str, dict] = {}  # experiment_id -> experiment state
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  模板查询
    # ------------------------------------------------------------------ #
    def list_templates(self, category: str = None) -> List[dict]:
        """列出所有模板（序列化为 dict）"""
        templates = self.template_library.list_templates(category)
        result = []
        for t in templates:
            result.append({
                "template_id": t.template_id,
                "name": t.name,
                "category": t.category,
                "description": t.description,
                "duration_months": t.duration_months,
                "agent_count": t.agent_count,
                "key_metrics": t.key_metrics,
                "setup_params": _serialize(t.setup_params),
                "success_criteria": _serialize(t.success_criteria),
            })
        return result

    def get_template(self, template_id: str) -> Optional[dict]:
        t = self.template_library.get_template(template_id)
        if not t:
            return None
        return {
            "template_id": t.template_id,
            "name": t.name,
            "category": t.category,
            "description": t.description,
            "duration_months": t.duration_months,
            "agent_count": t.agent_count,
            "key_metrics": t.key_metrics,
            "setup_params": _serialize(t.setup_params),
            "success_criteria": _serialize(t.success_criteria),
        }

    def get_template_stats(self) -> dict:
        return self.template_library.get_statistics()

    # ------------------------------------------------------------------ #
    #  实验生命周期
    # ------------------------------------------------------------------ #
    def create_experiment(self, template_id: str, config: dict = None) -> str:
        """创建并后台启动一个实验"""
        template = self.template_library.get_template(template_id)
        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        config = config or {}
        agent_count = config.get("agent_count", template.agent_count)
        duration_months = config.get("duration_months", min(template.duration_months, 360))
        speed = config.get("speed", 10)  # 默认 10x

        # 限制合理范围
        agent_count = max(100, min(agent_count, 50000))
        duration_months = max(1, min(duration_months, 600))

        experiment_id = f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        # 用户自定义上下文
        user_context = config.get("user_context", {})

        experiment = {
            "experiment_id": experiment_id,
            "template_id": template_id,
            "template_name": template.name,
            "category": template.category,
            "description": template.description,
            "key_metrics": template.key_metrics,
            "success_criteria": _serialize(template.success_criteria),
            "setup_params": _serialize(template.setup_params),
            # 用户配置
            "agent_count": agent_count,
            "duration_months": duration_months,
            "speed": speed,
            # 用户自定义
            "user_context": user_context,
            # 运行状态
            "status": ExperimentStatus.PENDING,
            "progress": 0,
            "current_month": 0,
            "stage": "等待启动",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            # 运行数据
            "snapshots": [],       # 每 N 月的统计快照
            "final_stats": None,
            "report_path": None,
            "report_content": None,
            "error": None,
        }

        with self._lock:
            self.experiments[experiment_id] = experiment

        # 后台线程执行
        t = threading.Thread(target=self._run_experiment, args=(experiment_id,), daemon=True)
        t.start()

        return experiment_id

    def get_experiment(self, experiment_id: str) -> Optional[dict]:
        with self._lock:
            exp = self.experiments.get(experiment_id)
            return dict(exp) if exp else None

    def list_experiments(self) -> List[dict]:
        with self._lock:
            return [dict(e) for e in self.experiments.values()]

    # ------------------------------------------------------------------ #
    #  实验执行（后台线程）
    # ------------------------------------------------------------------ #
    def _run_experiment(self, experiment_id: str):
        """在后台线程中执行完整实验"""
        try:
            exp = self.experiments[experiment_id]
            template_id = exp["template_id"]
            template = self.template_library.get_template(template_id)
            agent_count = exp["agent_count"]
            duration_months = exp["duration_months"]

            # ---- 阶段 1：初始化 ----
            self._update(experiment_id, status=ExperimentStatus.INITIALIZING,
                         stage="初始化引擎", progress=2)

            engine = DeepIntegrationEngine(template.setup_params)

            # ---- 阶段 2：创建 Agent ----
            self._update(experiment_id, stage=f"创建 {agent_count:,} 个 Agent", progress=5)

            batch = 500
            for i in range(0, agent_count, batch):
                count = min(batch, agent_count - i)
                for _ in range(count):
                    engine.create_agent()
                pct = 5 + int(15 * (i + count) / agent_count)
                self._update(experiment_id,
                             stage=f"已创建 {i + count:,}/{agent_count:,} Agent",
                             progress=pct)

            # ---- 阶段 3：演化 ----
            self._update(experiment_id, status=ExperimentStatus.RUNNING,
                         stage="开始演化", progress=20,
                         started_at=datetime.now().isoformat())

            snapshot_interval = max(1, duration_months // 20)  # 最多 20 个快照
            snapshots = []

            for month in range(1, duration_months + 1):
                result = engine.simulate_month()

                # 快照
                if month % snapshot_interval == 0 or month == duration_months:
                    stats = engine.get_world_statistics()
                    stats["month"] = month
                    stats["events_count"] = result.get("events_count", 0)
                    snapshots.append(stats)

                # 进度
                pct = 20 + int(60 * month / duration_months)
                self._update(experiment_id,
                             current_month=month,
                             stage=f"演化中 {month}/{duration_months} 月",
                             progress=pct)

            # ---- 阶段 4：汇总统计 ----
            self._update(experiment_id, stage="汇总统计数据", progress=82)
            final_stats = engine.get_world_statistics()
            final_stats["duration_months"] = duration_months
            final_stats["total_agents_final"] = len(engine.agents)
            final_stats["total_events"] = len(engine.events)

            # 为报告生成器准备数据
            report_data = self._prepare_report_data(engine, final_stats, snapshots)

            with self._lock:
                self.experiments[experiment_id]["snapshots"] = snapshots
                self.experiments[experiment_id]["final_stats"] = final_stats

            # ---- 阶段 5：生成报告 ----
            self._update(experiment_id, status=ExperimentStatus.GENERATING_REPORT,
                         stage="生成报告", progress=90)

            report_config = {
                "name": template.name,
                "metrics": template.key_metrics,
                "success_criteria": template.success_criteria,
                "events": [],
                "user_context": exp.get("user_context", {}),
            }

            # 商业版报告
            biz_report = self.report_generator.generate_experiment_report(
                experiment_id=experiment_id,
                experiment_data=report_data,
                template_config=report_config,
                report_type="business"
            )

            # 高管版报告
            exec_report = self.report_generator.generate_experiment_report(
                experiment_id=experiment_id,
                experiment_data=report_data,
                template_config=report_config,
                report_type="executive"
            )

            # 保存报告文件
            biz_path = self.report_generator.save_report(biz_report, experiment_id, "business")
            exec_path = self.report_generator.save_report(exec_report, experiment_id, "executive")

            combined_report = biz_report

            # ---- 阶段 6：生成用户实验报告（Excel+CSV+摘要）----
            self._update(experiment_id, stage="生成用户实验报告", progress=96)

            user_report_config = {
                "template_id": template.template_id,
                "template_name": template.name,
                "template_category": template.category,
                "key_metrics": template.key_metrics,
                "success_criteria": template.success_criteria,
                "description": template.description,
            }

            user_results = {
                "metrics": final_stats,
                "buyers": [],
                "non_buyers": [],
                "monthly_metrics": [],
                "discussion": "",
                "advice": "",
            }

            user_report_files = {}
            try:
                user_report_gen = ExperimentReportGenerator(REPORTS_PATH)
                user_report_files = user_report_gen.generate_full_report(
                    experiment_id, user_results, user_report_config
                )
            except Exception as report_err:
                print(f"[WARN] 用户报告生成失败（非致命）: {report_err}")

            with self._lock:
                self.experiments[experiment_id]["user_report_files"] = user_report_files

            # 保存完整实验数据 JSON
            exp_json_path = os.path.join(EXPERIMENTS_PATH, f"{experiment_id}.json")
            with open(exp_json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment_id": experiment_id,
                    "template": self.get_template(template_id),
                    "config": {"agent_count": agent_count, "duration_months": duration_months},
                    "final_stats": _serialize(final_stats),
                    "snapshots": [_serialize(s) for s in snapshots],
                    "report_business": biz_report,
                    "report_executive": exec_report,
                }, f, ensure_ascii=False, indent=2)

            # ---- 完成 ----
            self._update(experiment_id,
                         status=ExperimentStatus.COMPLETED,
                         stage="实验完成",
                         progress=100,
                         completed_at=datetime.now().isoformat(),
                         report_path=biz_path,
                         report_content=combined_report)

            print(f"[OK] 实验 {experiment_id} 完成！报告：{biz_path}")

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"[ERROR] 实验 {experiment_id} 失败：{error_msg}")
            self._update(experiment_id,
                         status=ExperimentStatus.FAILED,
                         stage=f"失败：{str(e)[:100]}",
                         error=error_msg)

    def _prepare_report_data(self, engine: DeepIntegrationEngine,
                             final_stats: dict, snapshots: list) -> dict:
        """将引擎数据转换为报告生成器需要的格式"""
        agents = list(engine.agents.values())
        alive = [a for a in agents if a.is_alive]

        initial_pop = final_stats.get("simulation", {}).get("total_agents", len(agents))
        # 简单估算初始人口（第一个快照或 agent_count）
        initial_pop_est = initial_pop
        if snapshots:
            first_snap = snapshots[0]
            if isinstance(first_snap, dict) and "simulation" in first_snap:
                initial_pop_est = first_snap["simulation"].get("total_agents", initial_pop)

        employed = sum(1 for a in alive if not a.is_unemployed)
        unemployed = sum(1 for a in alive if a.is_unemployed)

        return {
            "duration_days": final_stats.get("duration_months", 0) * 30,
            "initial_population": initial_pop_est,
            "final_population": len(alive),
            "total_births": max(0, len(agents) - initial_pop_est),
            "total_deaths": sum(1 for a in agents if not a.is_alive),
            "avg_satisfaction": sum(a.life_satisfaction for a in alive) / len(alive) if alive else 0,
            "avg_income": sum(a.income for a in alive) / len(alive) if alive else 0,
            "avg_health": sum(a.health_score for a in alive) / len(alive) if alive else 0,
            "avg_happiness": sum(a.happiness for a in alive) / len(alive) if alive else 0,
            "unemployment_rate": unemployed / (employed + unemployed) if (employed + unemployed) > 0 else 0,
            "occupation_stats": {
                "employed": employed,
                "unemployed": unemployed,
            },
            # 从 final_stats 复制关键数据
            "economy": final_stats.get("economy", {}),
            "demographics": final_stats.get("demographics", {}),
            "health": final_stats.get("health", {}),
            "social": final_stats.get("social", {}),
            "housing": final_stats.get("housing", {}),
        }

    def _update(self, experiment_id: str, **kwargs):
        """线程安全更新实验状态"""
        with self._lock:
            if experiment_id in self.experiments:
                self.experiments[experiment_id].update(kwargs)


def _serialize(obj):
    """安全序列化（处理 tuple 等不可 JSON 序列化的类型）"""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


# ============ 独立测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("实验执行引擎 v2.0 - 独立测试")
    print("=" * 60)

    runner = ExperimentRunner()

    # 列出模板
    templates = runner.list_templates()
    print(f"\n共 {len(templates)} 个模板：")
    for t in templates:
        print(f"  [{t['template_id']}] {t['name']} ({t['category']})")

    # 快速测试：用第一个模板，100 Agent，3 个月
    if templates:
        tid = templates[0]['template_id']
        print(f"\n创建测试实验（100 Agent, 3 月, 模板 {tid}）...")
        exp_id = runner.create_experiment(tid, {
            "agent_count": 100,
            "duration_months": 3,
        })
        print(f"实验 ID: {exp_id}")

        # 等待完成
        while True:
            exp = runner.get_experiment(exp_id)
            print(f"  [{exp['progress']}%] {exp['stage']}")
            if exp["status"] in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED):
                break
            time.sleep(1)

        if exp["status"] == ExperimentStatus.COMPLETED:
            print(f"\n✅ 实验完成！")
            print(f"报告路径：{exp['report_path']}")
            if exp.get("report_content"):
                print(f"\n--- 报告预览 ---")
                print(exp["report_content"][:500])
        else:
            print(f"\n❌ 实验失败：{(exp.get('error') or '')[:200]}")
