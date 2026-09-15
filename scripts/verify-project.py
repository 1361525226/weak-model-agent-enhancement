#!/usr/bin/env python3
"""
verify-project.py — 项目落地验证脚本

验证：
1. 目录结构完整性
2. Skill 文件可读性
3. 工具脚本可执行性
4. 配置文件有效性
5. AGENTS.md 规则完整性
"""

import json
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
PASS = "✅"
FAIL = "❌"
WARN = "⚠️"

results = {"passed": 0, "failed": 0, "warnings": 0}


def check(description, condition, detail=""):
    if condition:
        print(f"  {PASS} {description}")
        results["passed"] += 1
        return True
    else:
        print(f"  {FAIL} {description}" + (f" — {detail}" if detail else ""))
        results["failed"] += 1
        return False


def warn(description, detail=""):
    print(f"  {WARN} {description}" + (f" — {detail}" if detail else ""))
    results["warnings"] += 1


def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def main():
    print(f"🔍 验证项目：{PROJECT_ROOT}")
    print(f"   工作目录：{os.getcwd()}")

    # ── 1. 目录结构 ──────────────────────────────────────
    section("1. 目录结构检查")

    required_dirs = [
        ".loop",
        ".learnings",
        "skills/loop-engineering",
        "skills/context-engineering",
        "skills/harness-guardrails",
        "skills/memory-system",
        "skills/code-review",
        "skills/debugging",
        "skills/fullstack-dev",
        "skills/multi-agent",
        "skills/skill-evolution",
        "agens-agent-patterns/skills",
        "scripts",
        "templates",
    ]
    for d in required_dirs:
        path = PROJECT_ROOT / d
        check(f"目录存在: {d}", path.is_dir(), f"请运行: mkdir -p {d}")

    # ── 2. 核心文件 ──────────────────────────────────────
    section("2. 核心文件检查")

    required_files = [
        "AGENTS.md",
        "project_config.json",
        "MEMORY.md",
        "USER.md",
        "MEMORY_GRAPH.md",
        ".learnings/LEARNINGS.md",
        ".learnings/ERRORS.md",
        ".learnings/FEATURE_REQUESTS.md",
        ".learnings/session-state.md",
        ".loop/state.md",
        ".loop/run-log.md",
        "context-kernel.py",
        "reflexion_accumulator.py",
        "落地执行手册.md",
        "weak-model-agent-enhancement-v2.1.md",
    ]
    for f in required_files:
        path = PROJECT_ROOT / f
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        check(
            f"文件存在: {f} ({size} bytes)",
            exists,
            f"大小: {size}",
        )

    # ── 3. Skill 文件 ──────────────────────────────────────
    section("3. Skill 文件检查")

    skill_files = list((PROJECT_ROOT / "skills").rglob("SKILL.md"))
    check(f"Skill 文件数量: {len(skill_files)}", len(skill_files) >= 8, f"找到 {len(skill_files)} 个")

    for sf in skill_files:
        content = sf.read_text(encoding="utf-8", errors="ignore")
        has_trigger = "## 触发条件" in content
        has_steps = "## 执行步骤" in content or "### Step" in content
        check(f"Skill 有效: {sf.parent.name}/SKILL.md", has_trigger and has_steps, "缺少触发条件或执行步骤")

    # ── 4. agens-agent-patterns ───────────────────────────
    section("4. agens-agent-patterns 检查")

    patterns_root = PROJECT_ROOT / "agens-agent-patterns"
    check("agens-agent-patterns 目录存在", patterns_root.is_dir())
    if patterns_root.is_dir():
        pattern_skills = list(patterns_root.rglob("SKILL.md"))
        check(f"Pattern Skills: {len(pattern_skills)} 个", len(pattern_skills) >= 8)
        check("README.md 存在", (patterns_root / "README.md").exists())
        check("SKILL_INDEX.md 存在", (patterns_root / "SKILL_INDEX.md").exists())

    # ── 5. 配置文件 ──────────────────────────────────────
    section("5. 配置文件检查")

    config_path = PROJECT_ROOT / "project_config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            check("project_config.json 有效 JSON", True)
            check("项目名正确", cfg.get("project_name") == "weak-model-agent-enhancement")
            check("RPM 限制配置", cfg.get("agents", {}).get("rpm_limit") == 20)
            check("Skill 进化已启用", cfg.get("skill_evolution", {}).get("enabled") is True)
        except json.JSONDecodeError as e:
            check("project_config.json 有效 JSON", False, str(e))
    else:
        check("project_config.json 存在", False)

    # ── 6. 工具脚本可执行性 ──────────────────────────────
    section("6. 工具脚本可执行性")

    scripts = [
        ("context-kernel.py", ["--help"]),
        ("reflexion_accumulator.py", ["--help"]),
    ]
    for script, args in scripts:
        path = PROJECT_ROOT / script
        if path.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(path)] + args,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                check(f"{script} 可执行", result.returncode == 0, result.stderr[:100] if result.stderr else "")
            except subprocess.TimeoutExpired:
                check(f"{script} 可执行", False, "超时")
            except Exception as e:
                check(f"{script} 可执行", False, str(e)[:100])
        else:
            check(f"{script} 存在", False)

    # ── 7. AGENTS.md 规则完整性 ──────────────────────────
    section("7. AGENTS.md 规则完整性")

    agents_md = PROJECT_ROOT / "AGENTS.md"
    if agents_md.exists():
        content = agents_md.read_text(encoding="utf-8")
        checks = [
            ("字节截断规则", "head -c 4000" in content),
            ("完整路径引用", "@src/" in content or "完整路径" in content),
            ("会话隔离规则", "/new" in content and "/compact" in content),
            ("三层验证", "Lint" in content and "Test" in content and "Build" in content),
            ("错误回灌格式", "错误回灌" in content or "上次执行失败" in content),
            ("安全护栏", "输入护栏" in content or "输出护栏" in content),
            ("RPM 预算分配", "RPM" in content or "预算" in content),
        ]
        for name, passed in checks:
            check(f"AGENTS.md: {name}", passed)
    else:
        check("AGENTS.md 存在", False)

    # ── 8. 知识库同步状态 ────────────────────────────────
    section("8. 知识库同步状态")

    kb_docs = [
        "weak-model-agent-enhancement-v2.md",
        "weak-model-agent-enhancement-v2.1.md",
        "AGENTS.md",
        "落地执行手册.md",
        "rpm-budget-strategy.md",
        "agens-agent-patterns/README.md",
    ]
    synced_count = 0
    for doc in kb_docs:
        # 简化检查：文件存在于项目目录即视为"已准备同步"
        if (PROJECT_ROOT / doc.replace("/", os.sep)).exists():
            synced_count += 1
    check(f"可同步文档: {synced_count}/{len(kb_docs)}", synced_count == len(kb_docs))

    # ── 总结 ─────────────────────────────────────────────
    section("验证总结")
    total = results["passed"] + results["failed"] + results["warnings"]
    print(f"  总计: {total} 项检查")
    print(f"  {PASS} 通过: {results['passed']}")
    print(f"  {FAIL} 失败: {results['failed']}")
    print(f"  {WARN} 警告: {results['warnings']}")

    if results["failed"] > 0:
        print(f"\n⛔ 验证未通过，请修复 {results['failed']} 个失败项后重试")
        return 1
    elif results["warnings"] > 0:
        print(f"\n⚠️ 验证通过但有 {results['warnings']} 个警告，建议检查")
        return 0
    else:
        print(f"\n✅ 项目验证通过，可以开始使用")
        return 0


if __name__ == "__main__":
    sys.exit(main())
