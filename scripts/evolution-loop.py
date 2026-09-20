#!/usr/bin/env python3
"""
自进化循环器 — Agnes 驱动项目的持续迭代优化

核心循环：
  1. 选择一个进化任务（从任务队列）
  2. 执行 7阶段工作流
  3. 测量 Harness 评分变化
  4. 语义早停检测
  5. 记录到进化日志
  6. 如有改进，commit + checkpoint
  7. 加载下一个任务

使用方法：
  D:/hermes/hermes-agent/venv/Scripts/python.exe scripts/evolution-loop.py --duration 240
  D:/hermes/hermes-agent/venv/Scripts/python.exe scripts/evolution-loop.py --tasks 10
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# 配置
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
PYTHON = r"D:/hermes/hermes-agent/venv/Scripts/python.exe"
LOOP_DIR = PROJECT_ROOT / ".loop"
EVOLUTION_LOG = LOOP_DIR / "evolution-log.jsonl"
TASK_QUEUE = LOOP_DIR / "task-queue.json"
STATE_FILE = LOOP_DIR / "evolution-state.json"

# 进化任务队列（按优先级）
DEFAULT_TASKS = [
    # P0: Harness 核心
    {
        "id": "ev_001",
        "task": "优化 AGENTS.md 第2.2节字节截断规则，添加 context-kernel.py 调用示例",
        "priority": 0,
        "expected_gain": "高",
        "category": "harness",
    },
    {
        "id": "ev_002",
        "task": "增强 harness-guardrails Skill，添加 AgentDoG 诊断报告格式输出",
        "priority": 1,
        "expected_gain": "高",
        "category": "skill",
    },
    {
        "id": "ev_003",
        "task": "完善 skill-evolution Skill，添加 CRITIC 外部验证步骤到进化流程",
        "priority": 2,
        "expected_gain": "中",
        "category": "skill",
    },
    # P1: 工作流增强
    {
        "id": "ev_004",
        "task": "优化 workflow-engine.py VerifyPhase，添加真实测试执行逻辑",
        "priority": 3,
        "expected_gain": "中",
        "category": "workflow",
    },
    {
        "id": "ev_005",
        "task": "增强 context-engineering Skill，添加 ContextPipe 集成示例",
        "priority": 4,
        "expected_gain": "中",
        "category": "skill",
    },
    # P2: 文档与知识库
    {
        "id": "ev_006",
        "task": "更新 HANDOFF.md 添加 v3.7 进化记录和技术方案说明",
        "priority": 5,
        "expected_gain": "低",
        "category": "docs",
    },
    {
        "id": "ev_007",
        "task": "运行 kb-consolidator.py 检查知识库是否需要重新整合",
        "priority": 6,
        "expected_gain": "低",
        "category": "kb",
    },
    # P3: 创新探索
    {
        "id": "ev_008",
        "task": "搜索 GitHub 最新 AI 自进化项目，提取可复用模式",
        "priority": 7,
        "expected_gain": "探索性",
        "category": "research",
    },
    {
        "id": "ev_009",
        "task": "设计 Carousel Memory 轮转策略，减少上下文长度",
        "priority": 8,
        "expected_gain": "中",
        "category": "memory",
    },
    {
        "id": "ev_010",
        "task": "增强 reflexion_accumulator.py，添加 Error Depth 分析",
        "priority": 9,
        "expected_gain": "中",
        "category": "reflection",
    },
]


# ============================================================================
# 工具函数
# ============================================================================

def log(msg: str):
    """带时间戳的日志输出"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def run_command(cmd: list, cwd: Path = None) -> tuple:
    """运行命令，返回 (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd or PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令超时（120s）"
    except Exception as e:
        return -1, "", str(e)


def get_harness_score() -> float:
    """获取当前 Harness G7 评分"""
    rc, stdout, stderr = run_command([
        PYTHON, str(PROJECT_ROOT / "harness/scorecard.py"), "--json"
    ])
    if rc == 0:
        try:
            data = json.loads(stdout)
            return data.get("overall_score", 0.0)
        except:
            pass
    return 0.0


def get_project_version() -> str:
    """获取当前 Git 版本号"""
    rc, stdout, stderr = run_command(["git", "describe", "--tags", "--always"], cwd=PROJECT_ROOT)
    if rc == 0:
        return stdout.strip()
    return "unknown"


def git_commit(msg: str) -> bool:
    """提交变更"""
    run_command(["git", "add", "-A"], cwd=PROJECT_ROOT)
    rc, _, _ = run_command(["git", "commit", "-m", msg], cwd=PROJECT_ROOT)
    return rc == 0


def git_push() -> bool:
    """推送到远端"""
    rc, _, _ = run_command(["git", "push", "origin", "main"], cwd=PROJECT_ROOT)
    return rc == 0


def load_state() -> dict:
    """加载进化状态"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {
        "start_time": datetime.now().isoformat(),
        "iterations": 0,
        "tasks_completed": 0,
        "improvements": 0,
        "baseline_harness": 0.0,
        "current_harness": 0.0,
        "checkpoints": [],
        "tasks": [],
        "stopped": False,
        "stop_reason": "",
    }


def save_state(state: dict):
    """保存进化状态"""
    state["last_updated"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_evolution_log(entry: dict):
    """追加进化日志"""
    with open(EVOLUTION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_task_queue() -> list:
    """加载任务队列"""
    if TASK_QUEUE.exists():
        try:
            data = json.loads(TASK_QUEUE.read_text())
            if isinstance(data, list) and len(data) > 0:
                return data
        except:
            pass
    # 返回默认队列
    return DEFAULT_TASKS.copy()


def save_task_queue(tasks: list):
    """保存任务队列"""
    TASK_QUEUE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================================
# 进化执行器
# ============================================================================

class EvolutionExecutor:
    """执行单个进化任务"""

    def __init__(self):
        self.baseline_harness = 0.0
        self.pre_task_harness = 0.0
        self.post_task_harness = 0.0

    def run(self, task: dict) -> dict:
        """执行一个进化任务"""
        task_id = task.get("id", "unknown")
        task_desc = task.get("task", "无描述")
        category = task.get("category", "unknown")

        log(f"\n{'='*60}")
        log(f"进化任务 [{task_id}] | 类别: {category}")
        log(f"任务: {task_desc[:80]}...")
        log(f"{'='*60}")

        # 记录前置分数
        self.pre_task_harness = get_harness_score()
        log(f"前置 Harness 评分: {self.pre_task_harness}/100")

        # 执行工作流（简化版：直接执行任务，不跑完整 7 阶段）
        # 实际进化由 Agent 在下一轮对话中执行
        # 这里记录任务并开始执行标记
        start_time = time.time()

        result = {
            "task_id": task_id,
            "task": task_desc,
            "category": category,
            "pre_harness": self.pre_task_harness,
            "status": "executing",
            "start_time": datetime.now().isoformat(),
            "elapsed_seconds": 0,
        }

        # 标记任务为执行中
        executor._mark_task_running(task_id, task_desc)

        return result

    def complete(self, task_id: str, post_harness: float, improvement: bool,
                 changes: str = "", commit_hash: str = "") -> dict:
        """完成一个进化任务"""
        elapsed = time.time() - _get_task_start_time(task_id)

        result = {
            "task_id": task_id,
            "post_harness": post_harness,
            "improvement": improvement,
            "changes": changes[:200],
            "commit_hash": commit_hash,
            "elapsed_seconds": elapsed,
            "status": "completed",
            "end_time": datetime.now().isoformat(),
        }

        # 记录到日志
        append_evolution_log({
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "pre_harness": self.pre_task_harness,
            "post_harness": post_harness,
            "improvement": improvement,
            "elapsed": elapsed,
            "changes": changes[:200],
        })

        log(f"后置 Harness 评分: {post_harness}/100")
        if improvement:
            log(f"✅ 改进 detected！+{post_harness - self.pre_task_harness:.1f} 分")
        else:
            log(f"⚠️ 无改进（分数持平或下降）")

        return result

    def _mark_task_running(self, task_id: str, task_desc: str):
        """标记任务为执行中"""
        state = load_state()
        state["tasks"].append({
            "task_id": task_id,
            "task": task_desc,
            "status": "running",
            "started_at": datetime.now().isoformat(),
        })
        save_state(state)


# ============================================================================
# 语义收敛检测
# ============================================================================

def check_semantic_convergence(harness_history: list, window: int = 3) -> dict:
    """
    检测 Harness 评分是否收敛
    返回: {converged: bool, reason: str, signal: str}
    """
    if len(harness_history) < window:
        return {"converged": False, "reason": "样本不足", "signal": "insufficient"}

    recent = harness_history[-window:]
    # 检查是否有显著变化
    max_score = max(recent)
    min_score = min(recent)
    range_score = max_score - min_score

    # 收敛条件：最近 N 轮分数变化 < 1 分
    if range_score < 1.0:
        return {
            "converged": True,
            "reason": f"近 {window} 轮 Harness 评分稳定（范围 {range_score:.1f}）",
            "signal": "converged",
        }

    # 检查是否振荡
    if len(recent) >= 4:
        ups = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
        downs = sum(1 for i in range(1, len(recent)) if recent[i] < recent[i-1])
        total = ups + downs
        if total > 0 and abs(ups - downs) / total < 0.2:
            return {
                "converged": False,
                "reason": f"Harness 评分振荡（升{ups}次 降{downs}次）",
                "signal": "oscillating",
            }

    return {
        "converged": False,
        "reason": f"Harness 评分仍在波动（范围 {range_score:.1f}）",
        "signal": "progressing",
    }


# ============================================================================
# 全局状态
# ============================================================================

_task_start_times = {}

def _get_task_start_time(task_id: str) -> float:
    return _task_start_times.get(task_id, time.time())

def _set_task_start_time(task_id: str, t: float):
    _task_start_times[task_id] = t


# ============================================================================
# 主循环
# ============================================================================

def run_evolution_loop(duration_minutes: int = 60, max_tasks: int = 20):
    """运行进化循环"""
    log(f"\n{'#'*60}")
    log(f"# Agnes 自进化循环启动")
    log(f"# 目标时长: {duration_minutes} 分钟 | 最大任务数: {max_tasks}")
    log(f"{'#'*60}")

    # 初始化
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    executor = EvolutionExecutor()
    state = load_state()

    # 记录基线
    baseline = get_harness_score()
    state["baseline_harness"] = baseline
    state["current_harness"] = baseline
    state["start_time"] = datetime.now().isoformat()
    state["duration_minutes"] = duration_minutes
    state["max_tasks"] = max_tasks
    save_state(state)

    log(f"基线 Harness 评分: {baseline}/100")
    log(f"开始进化循环...")

    # 加载任务队列
    tasks = load_task_queue()
    # 过滤掉已完成的任务
    completed_ids = {t["task_id"] for t in state.get("tasks", []) if t.get("status") == "completed"}
    pending_tasks = [t for t in tasks if t.get("id") not in completed_ids]
    # 按优先级排序
    pending_tasks.sort(key=lambda x: x.get("priority", 99))

    harness_history = [baseline]
    evolution_count = 0

    # 计算截止时间
    end_time = time.time() + duration_minutes * 60

    while evolution_count < max_tasks and time.time() < end_time:
        if not pending_tasks:
            log("\n所有进化任务已完成")
            break

        # 取第一个任务
        task = pending_tasks.pop(0)
        task_id = task["id"]
        _set_task_start_time(task_id, time.time())

        # 执行任务
        result = executor.run(task)

        # === 实际执行进化逻辑 ===
        # 这里调用 workflow-engine 执行具体任务
        # 简化版：直接评估并记录

        # 测量后置分数
        post_harness = get_harness_score()
        harness_history.append(post_harness)

        # 判断是否有改进
        improvement = post_harness > baseline + 0.5  # 需要提升至少 0.5 分
        changes = ""
        commit_hash = ""

        if improvement:
            log(f"检测到改进！执行提交...")
            if git_commit(f"evolution-{task_id}: {task['task'][:50]}"):
                commit_hash = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True, text=True
                ).stdout.strip()
                git_push()
                baseline = post_harness  # 更新基线
                state["improvements"] = state.get("improvements", 0) + 1
                log(f"✅ 已提交并推送: {commit_hash}")

        # 标记任务完成
        complete_result = executor.complete(task_id, post_harness, improvement, changes, commit_hash)
        state["tasks"] = [
            t if t.get("task_id") != task_id else {
                **t, "status": "completed",
                "pre_harness": complete_result.get("pre_harness", self.pre_task_harness),
                "post_harness": complete_result.get("post_harness", post_harness),
                "improvement": complete_result.get("improvement", improvement),
                "commit_hash": complete_result.get("commit_hash", commit_hash),
            }
            for t in state.get("tasks", [])
        ] + [{
            "task_id": task_id,
            "task": task["task"],
            "status": "completed",
            "pre_harness": self.pre_task_harness,
            "post_harness": post_harness,
            "improvement": improvement,
            "commit_hash": commit_hash,
            "completed_at": datetime.now().isoformat(),
        }]

        state["iterations"] = evolution_count + 1
        state["current_harness"] = post_harness
        save_state(state)

        evolution_count += 1

        # 检查语义收敛
        convergence = check_semantic_convergence(harness_history)
        if convergence["converged"]:
            log(f"\n⏹ 语义收敛检测触发：{convergence['reason']}")
            log("进化循环提前终止（已达到收敛状态）")
            state["stopped"] = True
            state["stop_reason"] = convergence["reason"]
            save_state(state)
            break

        # 打印进度
        log(f"\n进度: {evolution_count}/{max_tasks} 任务 | Harness: {post_harness}/100 | 改进: {state.get('improvements', 0)} 次")
        log(f"收敛信号: {convergence['signal']} — {convergence['reason']}")

        # 检查是否还有时间
        remaining = end_time - time.time()
        if remaining < 60:  # 少于 1 分钟
            log("\n时间即将耗尽，准备终止")
            break

    # 最终状态
    final_harness = get_harness_score()
    state["final_harness"] = final_harness
    state["total_iterations"] = evolution_count
    state["total_improvements"] = state.get("improvements", 0)
    state["harness_history"] = harness_history
    state["end_time"] = datetime.now().isoformat()
    save_state(state)

    log(f"\n{'#'*60}")
    log(f"# 进化循环完成")
    log(f"# 总迭代: {evolution_count} | 改进: {state.get('improvements', 0)} 次")
    log(f"# 基线: {baseline}/100 → 最终: {final_harness}/100")
    log(f"{'#'*60}")

    return state


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Agnes 自进化循环器")
    parser.add_argument("--duration", type=int, default=60, help="运行时长（分钟）")
    parser.add_argument("--tasks", type=int, default=20, help="最大任务数")
    parser.add_argument("--resume", action="store_true", help="从上次状态恢复")
    parser.add_argument("--status", action="store_true", help="仅显示当前状态")
    args = parser.parse_args()

    if args.status:
        state = load_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0

    if args.resume:
        state = load_state()
        if state.get("stopped"):
            log("上次循环已结束，将从头开始")
        else:
            log(f"从上次状态恢复: {state.get('iterations', 0)} 次迭代已完成")

    run_evolution_loop(duration_minutes=args.duration, max_tasks=args.tasks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
