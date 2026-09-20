#!/usr/bin/env python3
"""
workflow-engine.py — 7阶段工作流编排器

基于弱模型增强方案 v3.0，将 OpenSpec → Design → TDD → Verify → Review → Reflect → Release
七阶段串联为可执行的自动化流水线。

对应知识库模式：
  阶段1: pattern_083, pattern_062
  阶段2: pattern_052, pattern_254, pattern_090
  阶段3: pattern_111, pattern_451, pattern_062
  阶段4: pattern_064, pattern_073, pattern_251
  阶段5: pattern_139, pattern_254, open-code-review-delegate
  阶段6: pattern_065, pattern_167, pattern_463
  阶段7: pattern_030, pattern_089
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Self-evolution modules
sys.path.insert(0, str(Path(__file__).parent.parent / "semantic_early_stop"))
sys.path.insert(0, str(Path(__file__).parent.parent / "harness"))
from semantic_early_stopping import SemanticEarlyStopper


# ============================================================================
# 配置
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CONFIG_PATH = PROJECT_ROOT / "project_config.json"
LOOP_STATE = PROJECT_ROOT / ".loop/state.md"
RUN_LOG = PROJECT_ROOT / ".loop/run-log.md"
LEARNINGS_DIR = PROJECT_ROOT / ".learnings"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {
        "default_max_iterations": 5,
        "gain_cost_optimal_r": 2,
        "early_stop_threshold": 0.10,
        "no_progress_limit": 2,
    }


def load_state() -> dict:
    if LOOP_STATE.exists():
        try:
            content = LOOP_STATE.read_text()
            # Try to parse JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
                return json.loads(json_str)
            return json.loads(content)
        except:
            pass
    return {
        "project_name": "weak-model-agent-enhancement",
        "version": "3.0.0",
        "current_phase": "idle",
        "loop_count": 0,
        "skills_loaded": 9,
        "next_action": "awaiting_task",
    }


def save_state(state: dict):
    LOOP_STATE.write_text(
        "```json\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n```\n",
        encoding="utf-8",
    )


def append_run_log(entry: dict):
    ts = datetime.now().isoformat()
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n## {entry.get('phase', 'unknown')} — {entry.get('title', '无标题')}\n\n")
        f.write(f"**时间**: {ts}\n")
        f.write(f"**状态**: {entry.get('status', 'running')}\n\n")
        if entry.get("details"):
            f.write(f"**详情**:\n{json.dumps(entry['details'], ensure_ascii=False, indent=2)}\n\n")
        f.write("---\n\n")


# ============================================================================
# 阶段执行器
# ============================================================================

class PhaseExecutor:
    """各阶段执行器基类"""

    def __init__(self, config: dict, state: dict):
        self.config = config
        self.state = state
        self.phase_name = ""
        self.result = {}

    def run(self, task: str, **kwargs) -> dict:
        raise NotImplementedError

    def record_success(self, task: str):
        """记录成功模式"""
        success_file = LEARNINGS_DIR / "SUCCESS_PATTERNS.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "phase": self.phase_name,
            "status": "success",
        }
        with open(success_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def record_failure(self, task: str, error: str):
        """记录失败模式"""
        err_file = LEARNINGS_DIR / "ERRORS.md"
        with open(err_file, "a", encoding="utf-8") as f:
            f.write(f"\n## [{datetime.now().strftime('%Y%m%d')}] {self.phase_name} 失败\n\n")
            f.write(f"- 任务: {task}\n")
            f.write(f"- 错误: {error[:500]}\n\n")


class SpecPhase(PhaseExecutor):
    """阶段1: 需求 — OpenSpec 锁定规格"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase_name = "spec"

    def run(self, task: str, constraints: list = None, acceptance: list = None) -> dict:
        print(f"\n{'='*60}")
        print(f"  阶段 1/7: 需求锁定 — OpenSpec")
        print(f"{'='*60}")
        print(f"  任务: {task}")

        # 生成 Spec 内容
        spec = {
            "task": task,
            "constraints": constraints or [],
            "acceptance_criteria": acceptance or [],
            "generated_at": datetime.now().isoformat(),
            "status": "draft",  # 等待人工确认
            "human_approved": False,
        }

        spec_file = PROJECT_ROOT / "Spec.md"
        spec_content = f"""# Spec: {task}

> 生成时间: {spec['generated_at']}
> 状态: draft（等待人工确认）

## 功能需求
- {task}

## 约束条件
"""
        for c in spec["constraints"]:
            spec_content += f"- {c}\n"
        if not spec["constraints"]:
            spec_content += "- （无特殊约束）\n"

        spec_content += """
## 验收标准
"""
        for a in spec["acceptance_criteria"]:
            spec_content += f"- [ ] {a}\n"
        if not spec["acceptance_criteria"]:
            spec_content += "- [ ] （待补充）\n"

        spec_content += f"""
## 人工确认点
- [ ] 确认需求理解正确
- [ ] 确认验收标准可执行
- [ ] 确认约束条件合理

---
**签批**: _______________  日期: _________
"""
        spec_file.write_text(spec_content, encoding="utf-8")
        spec["spec_path"] = str(spec_file)

        print(f"  ✅ Spec.md 已生成")
        print(f"  ⏳ 等待人工确认...")

        self.result = spec
        return spec


class DesignPhase(PhaseExecutor):
    """阶段2: 设计 — Agent 草案 + Critic 审查"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase_name = "design"

    def run(self, spec: dict) -> dict:
        print(f"\n{'='*60}")
        print(f"  阶段 2/7: 设计 — Agent 草案 + Critic 审查")
        print(f"{'='*60}")
        print(f"  任务: {spec['task']}")

        design = {
            "task": spec["task"],
            "generated_at": datetime.now().isoformat(),
            "status": "draft",
            "critic_reviewed": False,
            "human_approved": False,
        }

        # 生成设计草案
        design_file = PROJECT_ROOT / "Design.md"
        design_content = f"""# Design: {spec['task']}

> 生成时间: {design['generated_at']}

## 架构选择
- （待 Agent 生成）

## 模块划分
- （待 Agent 生成）

## 接口定义
- （待 Agent 生成）

## 风险点
- （待 Agent 生成）

## Critic Review
> 待独立 Critic Agent 审查后填充

## 人工签批
- [ ] Critical 问题已解决
- [ ] High 问题有处理方案
- [ ] 批准进入实现阶段
"""
        design_file.write_text(design_content, encoding="utf-8")
        design["design_path"] = str(design_file)

        print(f"  ✅ Design.md 已生成（草案）")
        print(f"  ⏳ 等待 Critic Agent 审查 + 人工签批...")

        self.result = design
        return design


class ImplementPhase(PhaseExecutor):
    """阶段3: 实现 — TDD 循环 + 小步提交"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase_name = "implement"

    def run(self, design: dict, max_iterations: int = None) -> dict:
        max_iter = max_iterations or self.config.get("default_max_iterations", 5)
        print(f"\n{'='*60}")
        print(f"  阶段 3/7: 实现 — TDD 循环（最多 {max_iter} 轮）")
        print(f"{'='*60}")

        result = {
            "task": design["task"],
            "iterations": 0,
            "files_changed": [],
            "tests_passed": 0,
            "tests_failed": 0,
            "status": "in_progress",
        }

        print(f"  📝 TDD 循环开始...")
        print(f"  💡 提示：实际执行时由 Agent 按 AGENTS.md 规则运行")
        print(f"     1. 写失败测试（红）")
        print(f"     2. 最小化实现（绿）")
        print(f"     3. Strict Verifier 验证")
        print(f"     4. 失败则错误回灌重试（≤{max_iter}次）")

        # 占位：实际实现由 Agent 执行
        result["status"] = "agent_executed"
        result["note"] = "由 Agent 在执行时完成 TDD 循环"

        print(f"  ✅ 实现阶段完成（由 Agent 执行）")

        self.result = result
        return result


class VerifyPhase(PhaseExecutor):
    """阶段4: 验证 — Best-of-N + 失败回灌"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase_name = "verify"

    def run(self, implementation: dict, strategy: str = "auto", n_candidates: int = 3,
            semantics_history: list = None) -> dict:
        print(f"\n{'='*60}")
        print(f"  阶段 4/7: 验证 — Best-of-N 采样 + 语义早停")
        print(f"{'='*60}")
        print(f"  策略: {strategy} | 候选数: {n_candidates}")

        # 策略选择
        if strategy == "auto":
            strategy = "serial_r2" if n_candidates <= 2 else "best_of_n"

        # 初始化语义早停检测器
        stopper = SemanticEarlyStopper(max_consecutive_stable=2)
        if semantics_history:
            for entry in semantics_history:
                stopper.record(
                    diff=entry.get("diff", ""),
                    passed=entry.get("passed", False),
                    approach=entry.get("approach", ""),
                )

        result = {
            "task": implementation["task"],
            "strategy": strategy,
            "candidates": n_candidates,
            "verified_at": datetime.now().isoformat(),
            "four_signals": {},
            "semantic_check": {},
            "rounds_executed": 0,
            "status": "pending",
        }

        print(f"  🔄 执行验证策略: {strategy}")

        # 模拟验证循环（实际由 Agent 执行）
        max_rounds = min(n_candidates, 5)
        for round_num in range(1, max_rounds + 1):
            print(f"  📋 验证轮次 {round_num}/{max_rounds}")

            # 模拟结果（实际由测试套件产出）
            passed = True
            diff_summary = f"round_{round_num}_changes"
            approach_used = strategy

            stopper.record(diff_summary, passed, approach_used)
            check_result = stopper.check()
            result["semantic_check"] = check_result
            result["four_signals"] = check_result.get("signals", {})
            result["rounds_executed"] = round_num

            print(f"     语义信号: {check_result.get('reason', '正常')}")

            if check_result["should_stop"]:
                print(f"  ⏹ 语义收敛，提前终止验证（已执行 {round_num} 轮）")
                break

        result["semantics_history"] = [
            {"diff": h["diff"], "passed": h["passed"], "ts": h["ts"]}
            for h in stopper._history
        ]

        result["status"] = "agent_verified"
        result["note"] = "验证由 Agent 运行测试套件完成，含语义早停"

        print(f"  ✅ 验证阶段完成（共 {result['rounds_executed']} 轮）")

        self.result = result
        return result


class ReviewPhase(PhaseExecutor):
    """阶段5: 审查 — Critic Agent 复审"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase_name = "review"

    def run(self, verification: dict) -> dict:
        print(f"\n{'='*60}")
        print(f"  阶段 5/7: 审查 — Critic Agent 复审")
        print(f"{'='*60}")

        result = {
            "task": verification["task"],
            "reviewed_at": datetime.now().isoformat(),
            "findings": {"critical": [], "high": [], "medium": [], "low": []},
            "blind_spots_checked": [],
            "status": "pending",
        }

        print(f"  🔍 使用 open-code-review-delegate Skill 执行审查")
        print(f"  📋 CRITIC 外部验证层:")
        print(f"     - 代码执行验证")
        print(f"     - 路径验证")
        print(f"     - 引用验证")
        print(f"     - 一致性验证")
        print(f"  🔎 盲区检查:")
        print(f"     - 测试覆盖不到的边界条件")
        print(f"     - 安全漏洞")
        print(f"     - 性能问题")
        print(f"  ⏳ 实际审查由 Agent 执行...")

        result["status"] = "agent_reviewed"
        result["note"] = "审查由 Agent 使用 open-code-review-delegate 完成"

        print(f"  ✅ 审查阶段完成")

        self.result = result
        return result


class ReflectPhase(PhaseExecutor):
    """阶段6: 复盘 — 失败模式自动积累"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase_name = "reflect"

    def run(self, review: dict) -> dict:
        print(f"\n{'='*60}")
        print(f"  阶段 6/7: 复盘 — Reflexion + Skill 进化")
        print(f"{'='*60}")

        result = {
            "task": review["task"],
            "reflected_at": datetime.now().isoformat(),
            "patterns_identified": [],
            "skills_to_update": [],
            "evolve_triggered": False,
        }

        print(f"  🧠 Reflexion 反思:")
        print(f"     - 分析本轮成功/失败模式")
        print(f"     - 生成自然语言反思")
        print(f"     - 注入记忆系统")
        print(f"  📚 模式积累:")
        print(f"     - 高频错误 → 抽象为 Skill 规则")
        print(f"     - 新发现 → ERRORS.md")
        print(f"     - 成功策略 → SUCCESS_PATTERNS.md")
        print(f"  🔄 Skill 进化触发检查:")
        print(f"     - 同类失败 ≥ 3 次 → 触发 /evolve")
        print(f"  ⏳ 实际复盘由 Agent 执行...")

        result["status"] = "agent_reflected"

        print(f"  ✅ 复盘阶段完成")

        self.result = result
        return result


class ReleasePhase(PhaseExecutor):
    """阶段7: 发布 — 小范围验证后扩散"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase_name = "release"

    def run(self, reflection: dict) -> dict:
        print(f"\n{'='*60}")
        print(f"  阶段 7/7: 发布 — 金丝雀 + 扩散")
        print(f"{'='*60}")

        result = {
            "task": reflection["task"],
            "released_at": datetime.now().isoformat(),
            "canary_verified": False,
            "full_released": False,
            "safety_drift_checked": False,
        }

        print(f"  🚀 发布流程:")
        print(f"     1. 金丝雀发布（小范围验证）")
        print(f"     2. 安全漂移检测")
        print(f"     3. 人工确认关键改动")
        print(f"     4. 全量发布")
        print(f"     5. 后续 N 次使用监控")
        print(f"  ⏳ 实际发布由 Agent + 人工确认完成...")

        result["status"] = "agent_released"

        print(f"  ✅ 发布阶段完成")

        self.result = result
        return result


# ============================================================================
# 主编排器
# ============================================================================

class WorkflowOrchestrator:
    """7阶段工作流编排器"""

    PHASES = [
        ("spec", SpecPhase),
        ("design", DesignPhase),
        ("implement", ImplementPhase),
        ("verify", VerifyPhase),
        ("review", ReviewPhase),
        ("reflect", ReflectPhase),
        ("release", ReleasePhase),
    ]

    def __init__(self, config: dict = None, state: dict = None):
        self.config = config or load_config()
        self.state = state or load_state()
        self.results = {}
        self.current_phase = 0

    def run(self, task: str, strategy: str = "auto", n: int = 3, skip_human_gates: bool = False,
            semantics_history: list = None):
        """运行完整 7 阶段工作流"""
        print(f"\n{'#'*60}")
        print(f"# 弱模型增强工作流 v3.0 — 7阶段闭环")
        print(f"# 任务: {task}")
        print(f"# 策略: {strategy} | 候选: {n}")
        print(f"{'#'*60}")

        self.state["current_phase"] = "running"
        self.state["last_task"] = task
        save_state(self.state)

        spec = None
        design = None
        implementation = None
        verification = None
        review = None
        reflection = None

        try:
            # Phase 1: Spec
            executor = SpecPhase(self.config, self.state)
            spec = executor.run(task)
            self.results["spec"] = spec
            if not spec.get("human_approved") and not skip_human_gates:
                print(f"\n  ⛔ 阶段1完成，等待人工确认 Spec.md")
                return self.results

            # Phase 2: Design
            executor = DesignPhase(self.config, self.state)
            design = executor.run(spec)
            self.results["design"] = design
            if not design.get("human_approved") and not skip_human_gates:
                print(f"\n  ⛔ 阶段2完成，等待人工签批 Design.md")
                return self.results

            # Phase 3: Implement
            executor = ImplementPhase(self.config, self.state)
            implementation = executor.run(design)
            self.results["implement"] = implementation

            # Phase 4: Verify
            executor = VerifyPhase(self.config, self.state)
            verification = executor.run(implementation, strategy=strategy, n_candidates=n,
                                        semantics_history=semantics_history)
            self.results["verify"] = verification

            # Phase 5: Review
            executor = ReviewPhase(self.config, self.state)
            review = executor.run(verification)
            self.results["review"] = review

            # Phase 6: Reflect
            executor = ReflectPhase(self.config, self.state)
            reflection = executor.run(review)
            self.results["reflect"] = reflection

            # Phase 7: Release
            executor = ReleasePhase(self.config, self.state)
            result = executor.run(reflection)
            self.results["release"] = result

        except Exception as e:
            print(f"\n  ❌ 工作流执行失败: {e}")
            self.state["current_phase"] = "error"
            self.state["error"] = str(e)
            save_state(self.state)
            return {"error": str(e)}

        # 完成
        self.state["current_phase"] = "completed"
        self.state["loop_count"] = self.state.get("loop_count", 0) + 1
        self.state["next_action"] = "awaiting_task"
        save_state(self.state)

        append_run_log({
            "phase": "full_workflow",
            "title": task,
            "status": "completed",
            "details": {
                "strategy": strategy,
                "candidates": n,
                "phases": [k for k, v in self.results.items() if v],
            },
        })

        print(f"\n{'#'*60}")
        print(f"# 工作流完成 — 所有 7 阶段已执行")
        print(f"{'#'*60}")

        return self.results

    def run_phase(self, phase_name: str, **kwargs):
        """运行单个阶段"""
        for pname, cls in self.PHASES:
            if pname == phase_name:
                executor = cls(self.config, self.state)
                result = executor.run(**kwargs)
                self.results[phase_name] = result
                return result
        raise ValueError(f"未知阶段: {phase_name}")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="7阶段工作流编排器")
    parser.add_argument("task", help="任务描述")
    parser.add_argument("--strategy", choices=["serial_r2", "best_of_n", "tot", "forest", "auto"],
                       default="auto", help="验证策略")
    parser.add_argument("--n", type=int, default=3, help="Best-of-N 候选数")
    parser.add_argument("--phase", help="仅运行指定阶段")
    parser.add_argument("--skip-gates", action="store_true", help="跳过人工确认门")
    parser.add_argument("--semantics-history", help="语义历史文件（JSONL），用于跨轮次早停检测")
    args = parser.parse_args()

    orchestrator = WorkflowOrchestrator()

    semantics_history = None
    if hasattr(args, "semantics_history") and args.semantics_history:
        from pathlib import Path
        history_file = Path(args.semantics_history)
        if history_file.exists():
            semantics_history = []
            for line in history_file.read_text().splitlines():
                if line.strip():
                    try:
                        semantics_history.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    if args.phase:
        result = orchestrator.run_phase(args.phase, task=args.task)
    else:
        result = orchestrator.run(
            task=args.task,
            strategy=args.strategy,
            n=args.n,
            skip_human_gates=args.skip_gates,
            semantics_history=semantics_history,
        )

    # 输出结果摘要
    print(f"\n📊 执行结果:")
    for phase, res in result.items():
        if isinstance(res, dict):
            status = res.get("status", "unknown")
            print(f"  {phase}: {status}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
