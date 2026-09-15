#!/usr/bin/env python3
"""
init-project.py — 项目初始化脚本

功能：
1. 创建所有必要目录和文件
2. 复制 Skill 模板到 skills/ 目录
3. 初始化 .loop/ 和 .learnings/ 状态
4. 运行验证
"""

import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ 目录: {path.relative_to(PROJECT_ROOT)}")


def ensure_file(path: Path, content: str = ""):
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        print(f"  ✅ 创建: {path.relative_to(PROJECT_ROOT)}")
    else:
        print(f"  ⏭️  跳过（已存在）: {path.relative_to(PROJECT_ROOT)}")


def main():
    print(f"🚀 初始化项目: {PROJECT_ROOT}\n")

    # 1. 创建目录
    print("📁 创建目录结构...")
    dirs = [
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
        "scripts",
        "templates",
    ]
    for d in dirs:
        ensure_dir(PROJECT_ROOT / d)

    # 2. 创建 L1 记忆文件（如不存在）
    print("\n📝 初始化记忆系统...")
    ensure_file(
        PROJECT_ROOT / "MEMORY.md",
        """# 项目记忆 (MEMORY.md)

> 类型：⚡ 情景记忆（Episodic）
> 容量监控：当前 0/2200 字符（0%）
> 最后更新：待填充
> 容器：[weak-model-agent-enhancement]

## 项目状态
（待填充）

## 关键文件
- AGENTS.md — 编码规则
- project_config.json — 项目配置
- context-kernel.py — 上下文投影
- reflexion_accumulator.py — 失败模式积累

## 进化日志
（待填充）
""",
    )
    ensure_file(
        PROJECT_ROOT / "USER.md",
        """# 用户画像 (USER.md)

> 类型：🔒 静态记忆（Static）
> 容量监控：当前 0/1375 字符（0%）
> 最后更新：待填充

## 偏好
[待填充]

## 技术背景
[待填充]

## 禁忌事项
- 不建议多账号聚合
- 不建议无验证的空转 Loop
""",
    )
    ensure_file(
        PROJECT_ROOT / "MEMORY_GRAPH.md",
        """# 记忆关系图谱 (MEMORY_GRAPH.md)

> 类型：🔗 关系层（Relational）
> 容量监控：当前 0/1500 字符（0%）
> 最后更新：待填充

## 关系列表
（暂无）

## 容器列表
- [weak-model-agent-enhancement]
""",
    )

    # 3. 创建 L5 日志文件
    print("\n📊 初始化学习日志...")
    ensure_file(PROJECT_ROOT / ".learnings/LEARNINGS.md", "# LEARNINGS.md\n\n---\n")
    ensure_file(PROJECT_ROOT / ".learnings/ERRORS.md", "# ERRORS.md\n\n---\n")
    ensure_file(PROJECT_ROOT / ".learnings/FEATURE_REQUESTS.md", "# FEATURE_REQUESTS.md\n\n---\n")
    ensure_file(
        PROJECT_ROOT / ".learnings/session-state.md",
        """# Session State

## current_objective
项目初始化

## last_decision
运行 init-project.py

## blocker
无

## next_move
运行 verify-project.py 验证
""",
    )

    # 4. 创建 .loop/ 状态文件
    print("\n🔄 初始化 Loop 状态...")
    import json
    from datetime import datetime

    state = {
        "project_name": "weak-model-agent-enhancement",
        "version": "2.1.0",
        "created_at": datetime.now().isoformat(),
        "current_phase": "initializing",
        "loop_count": 0,
        "skills_loaded": 0,
        "next_action": "run_verify",
    }
    state_file = PROJECT_ROOT / ".loop/state.md"
    if not state_file.exists():
        state_file.write_text(
            f"```json\n{json.dumps(state, ensure_ascii=False, indent=2)}\n```",
            encoding="utf-8",
        )
        print(f"  ✅ 创建: .loop/state.md")
    else:
        print(f"  ⏭️  跳过: .loop/state.md")

    ensure_file(
        PROJECT_ROOT / ".loop/run-log.md",
        "# Run Log\n\n---\n",
    )

    # 5. 复制 Skill 模板（从 agens-agent-patterns 同步）
    print("\n🔧 同步 Skill 模板...")
    patterns_dir = PROJECT_ROOT / "agens-agent-patterns/skills"
    if patterns_dir.exists():
        for skill_dir in patterns_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                target = PROJECT_ROOT / "skills" / skill_dir.name
                target.mkdir(parents=True, exist_ok=True)
                src_skill = skill_dir / "SKILL.md"
                dst_skill = target / "SKILL.md"
                if not dst_skill.exists():
                    shutil.copy2(src_skill, dst_skill)
                    print(f"  ✅ 复制: skills/{skill_dir.name}/SKILL.md")
                else:
                    print(f"  ⏭️  跳过: skills/{skill_dir.name}/SKILL.md（已存在）")
    else:
        print("  ⚠️  agens-agent-patterns/skills 目录不存在，跳过同步")

    # 6. 创建初始化完成标记
    print("\n✨ 初始化完成！")
    print(f"\n下一步：运行 python scripts/verify-project.py 验证项目")

    return 0


if __name__ == "__main__":
    sys.exit(main())
