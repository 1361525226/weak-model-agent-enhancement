#!/usr/bin/env python3
"""
context-kernel.py — 上下文投影工具

功能：根据当前任务自动投影高信号上下文，减少 Token 消耗。
用法：python context-kernel.py <task_description> [--project-root .] [--budget 4000]

从 Trae 知识库 pattern_018（上下文工程技能化）+ pattern_456（仓库地图 token 预算）
+ pattern_460（LLMLingua 压缩）提取并适配。
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ============================================================================
# 文件重要性评分（基于引用热度）
# ============================================================================

PRIORITY_FILES = {
    # 最高优先级（必须注入）
    "MUST_INJECT": [
        "AGENTS.md", "CONTEXT.md", "package.json", "pyproject.toml",
        "go.mod", "Cargo.toml", "Makefile", "docker-compose.yml",
        ".env.example", "README.md",
    ],
    # 高优先级（直接相关）
    "HIGH": [
        "config/", "src/", "lib/", "pkg/", "app/",
        "*.test.ts", "*.test.py", "*.spec.ts",
    ],
    # 中优先级（间接相关）
    "MEDIUM": [
        "types/", "interfaces/", "schemas/", "models/",
        "*.d.ts", "types.ts",
    ],
    # 低优先级（按需加载）
    "LOW": [
        "docs/", "examples/", "tests/",
    ],
}

# 文件类型权重
EXT_WEIGHT = {
    ".go": 1.0, ".ts": 1.0, ".tsx": 0.9, ".py": 0.9,
    ".js": 0.8, ".jsx": 0.7, ".rs": 1.0, ".java": 0.8,
    ".sql": 0.7, ".json": 0.5, ".yaml": 0.4, ".yml": 0.4,
    ".md": 0.3, ".txt": 0.2,
}


# ============================================================================
# 核心函数
# ============================================================================

def find_project_root(start: str) -> Path:
    """自动检测项目根目录"""
    current = Path(start).resolve()
    markers = [".git", "package.json", "go.mod", "Cargo.toml", "pyproject.toml"]
    while current != current.parent:
        if any((current / m).exists() for m in markers):
            return current
        current = current.parent
    return current


def calculate_file_score(
    filepath: Path,
    project_root: Path,
    task_keywords: list[str],
) -> tuple[int, str]:
    """
    计算文件重要性分数。
    返回 (score, priority_label)
    """
    score = 0
    rel_path = str(filepath.relative_to(project_root)).lower()
    name = filepath.name.lower()
    ext = filepath.suffix.lower()

    # 1. 文件名匹配（最高权重）
    for category, patterns in PRIORITY_FILES.items():
        for pattern in patterns:
            if pattern.startswith("*"):
                # 通配符匹配
                if name.endswith(pattern[1:]):
                    score += {"MUST_INJECT": 100, "HIGH": 80, "MEDIUM": 50, "LOW": 20}[category]
                    break
            elif pattern in rel_path:
                score += {"MUST_INJECT": 100, "HIGH": 80, "MEDIUM": 50, "LOW": 20}[category]
                break

    # 2. 扩展名权重
    score += int(EXT_WEIGHT.get(ext, 0.3) * 30)

    # 3. 任务关键词匹配
    for kw in task_keywords:
        if kw.lower() in rel_path or kw.lower() in name:
            score += 50
            break

    # 4. 距离项目根越近权重越高
    depth = len(filepath.relative_to(project_root).parts)
    score += max(0, 30 - depth * 5)

    # 5. 文件大小惩罚（过大文件降低优先级）
    try:
        size = filepath.stat().st_size
        if size > 50000:  # > 50KB
            score -= 20
        elif size > 200000:  # > 200KB
            score -= 50
    except OSError:
        pass

    # 确定优先级
    if score >= 80:
        priority = "MUST_INJECT"
    elif score >= 50:
        priority = "HIGH"
    elif score >= 30:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return score, priority


def scan_codebase(
    project_root: Path,
    extensions: list[str] = None,
    exclude_dirs: list[str] = None,
) -> list[Path]:
    """扫描项目源文件"""
    if extensions is None:
        extensions = [".go", ".ts", ".tsx", ".py", ".js", ".jsx", ".rs", ".java", ".sql"]
    if exclude_dirs is None:
        exclude_dirs = ["node_modules", ".git", "vendor", "__pycache__", ".venv", "dist", "build", ".next"]

    files = []
    for ext in extensions:
        files.extend(project_root.rglob(f"*{ext}"))

    # 过滤排除目录
    filtered = []
    for f in files:
        if not any(ex in str(f) for ex in exclude_dirs):
            filtered.append(f)
    return sorted(filtered, key=lambda x: x.stat().st_size if x.exists() else 0, reverse=True)


def truncate_content(content: str, max_bytes: int = 4000) -> str:
    """字节级截断，保留完整行"""
    if len(content.encode("utf-8")) <= max_bytes:
        return content

    # 尝试从 max_bytes 处向前找换行符
    encoded = content.encode("utf-8")
    cut_pos = min(max_bytes, len(encoded))

    # 向前找换行
    while cut_pos > 0 and encoded[cut_pos:cut_pos+1] != b"\n":
        cut_pos -= 1

    if cut_pos == 0:
        # 没有找到换行，硬截断
        return encoded[:max_bytes].decode("utf-8", errors="ignore") + "\n...[truncated]"

    result = encoded[:cut_pos].decode("utf-8")
    result += "\n...[truncated, " + str(len(encoded) - cut_pos) + " bytes omitted]"
    return result


def build_context_projection(
    task_description: str,
    project_root: Path,
    budget_tokens: int = 4000,
) -> dict:
    """
    构建上下文投影。
    返回 {
        "summary": str,           # 任务摘要
        "priority_files": [...],  # 高优先级文件列表
        "context_string": str,    # 可用于注入 prompt 的上下文字符串
        "token_estimate": int,    # 估计 token 数
        "skills_to_load": [...]   # 建议加载的 Skill
    }
    """
    # 1. 提取任务关键词
    task_keywords = task_description.lower().split()
    # 过滤短词
    task_keywords = [w for w in task_keywords if len(w) > 2]

    # 2. 扫描代码库
    all_files = scan_codebase(project_root)

    # 3. 评分排序
    scored_files = []
    for f in all_files[:200]:  # 最多评估 200 个文件
        score, priority = calculate_file_score(f, project_root, task_keywords)
        scored_files.append((score, priority, f))

    scored_files.sort(key=lambda x: -x[0])

    # 4. 选择文件（预算驱动）
    selected = []
    used_bytes = 0
    for score, priority, f in scored_files:
        if priority == "MUST_INJECT":
            selected.append(("MUST", f, score))
        elif priority == "HIGH" and used_bytes < budget_tokens * 3:
            selected.append(("HIGH", f, score))
        elif priority == "MEDIUM" and used_bytes < budget_tokens * 5:
            selected.append(("MED", f, score))

    # 5. 构建上下文字符串
    context_parts = []
    total_tokens = 0

    for label, f, score in selected:
        if not f.exists():
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # 字节截断
        truncated = truncate_content(content, max_bytes=budget_tokens * 3)
        file_tokens = len(truncated.encode("utf-8")) // 4  # 粗略估算：4 bytes ≈ 1 token

        if total_tokens + file_tokens > budget_tokens * 2:
            break

        rel_path = f.relative_to(project_root)
        context_parts.append(f"## {label} | @{rel_path} (score:{score})\n{truncated}")
        total_tokens += file_tokens

    context_string = "\n\n---\n\n".join(context_parts)

    # 6. 确定需要加载的 Skill
    skills_to_load = []
    task_lower = task_description.lower()
    if any(k in task_lower for k in ["test", "bug", "fix", "error", "debug"]):
        skills_to_load.append("debugging")
    if any(k in task_lower for k in ["api", "database", "db", "sql", "schema"]):
        skills_to_load.append("fullstack-dev")
    if any(k in task_lower for k in ["component", "ui", "frontend", "react", "vue"]):
        skills_to_load.append("fullstack-dev")
    if any(k in task_lower for k in ["review", "check", "lint"]):
        skills_to_load.append("code-review")
    if any(k in task_lower for k in ["prompt", "context", "token", "compress"]):
        skills_to_load.append("context-engineering")

    return {
        "summary": task_description,
        "priority_files": [str(f.relative_to(project_root)) for _, f, _ in selected],
        "context_string": context_string,
        "token_estimate": total_tokens,
        "skills_to_load": skills_to_load,
        "project_root": str(project_root),
    }


def main():
    parser = argparse.ArgumentParser(
        description="context-kernel: 上下文投影工具，根据任务自动选择高信号文件"
    )
    parser.add_argument("task", help="任务描述")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--budget", type=int, default=4000, help="Token 预算（默认 4000）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--print-context", action="store_true", help="打印上下文字符串（用于直接注入 prompt）")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root)

    projection = build_context_projection(args.task, project_root, args.budget)

    if args.json:
        # 移除 context_string 以保持 JSON 输出简洁
        output = {k: v for k, v in projection.items() if k != "context_string"}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"📍 项目根目录：{projection['project_root']}")
        print(f"🎯 任务：{projection['summary']}")
        print(f"💰 Token 估算：{projection['token_estimate']}")
        print(f"📦 建议加载 Skill：{', '.join(projection['skills_to_load']) or '无'}")
        print(f"\n📄 选中文件（{len(projection['priority_files'])} 个）：")
        for f in projection["priority_files"][:15]:
            print(f"  - {f}")
        if len(projection["priority_files"]) > 15:
            print(f"  ... 还有 {len(projection['priority_files']) - 15} 个文件")

        if args.print_context:
            print(f"\n{'='*60}")
            print("上下文字符串（可直接注入 prompt）：")
            print(projection["context_string"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
