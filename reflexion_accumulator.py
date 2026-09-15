#!/usr/bin/env python3
"""
reflexion_accumulator.py — Reflexion 失败模式自动积累脚本

功能：
1. 监控 Agnes 任务执行结果（成功/失败）
2. 失败时自动提取错误模式和根因
3. 将成功/失败模式写入 SUCCESS_PATTERNS.md / ERRORS.md
4. 定期汇总生成 FAILURES_REPORT.md（供 Skill 迭代参考）

对应 Trae 知识库 pattern_065（Reflexion 语言反思）+ pattern_111（SWE-agent 自主修复）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================================
# 错误模式识别规则
# ============================================================================

ERROR_PATTERNS = {
    # TypeScript/JavaScript
    "TS_NULL_ERROR": {
        "regex": r"TypeError.*Cannot read properties of undefined|null",
        "category": "null_safety",
        "fix_template": "添加可选链操作符 ?. 或 null check",
    },
    "TS_TYPE_ERROR": {
        "regex": r"Type '.*' is not assignable to type '.*'",
        "category": "type_mismatch",
        "fix_template": "检查类型定义，添加类型断言或转换",
    },
    "TS_IMPORT_ERROR": {
        "regex": r"Cannot find module|import.*cannot be imported",
        "category": "import_error",
        "fix_template": "检查依赖是否安装，或修正导入路径",
    },
    # Python
    "PY_IMPORT_ERROR": {
        "regex": r"ModuleNotFoundError|ImportError.*No module named",
        "category": "import_error",
        "fix_template": "pip install 缺失的依赖包",
    },
    "PY_TYPE_ERROR": {
        "regex": r"TypeError.*unexpected type|is not iterable",
        "category": "type_error",
        "fix_template": "检查变量类型，添加类型转换或校验",
    },
    "PY_KEY_ERROR": {
        "regex": r"KeyError:",
        "category": "key_error",
        "fix_template": "使用 .get() 或 defaultdict 替代直接字典访问",
    },
    "PY_VALUE_ERROR": {
        "regex": r"ValueError:",
        "category": "value_error",
        "fix_template": "检查输入值的有效性，添加数据校验",
    },
    # SQL
    "SQL_SYNTAX_ERROR": {
        "regex": r"SQLSyntaxError|near .* at line",
        "category": "sql_syntax",
        "fix_template": "检查 SQL 语法，使用参数化查询",
    },
    "SQL_INJECTION_RISK": {
        "regex": r"psycopg2\.errors\.InsufficientPrivilege|sqlalchemy\..exc",
        "category": "security",
        "fix_template": "使用参数化查询，禁止字符串拼接 SQL",
    },
    # Build/CI
    "BUILD_ERROR": {
        "regex": r"build failed|npm ERR!|go build.*error",
        "category": "build",
        "fix_template": "检查构建配置和依赖版本",
    },
    "TEST_FAILURE": {
        "regex": r"FAILED|AssertionError|expected.*got",
        "category": "test",
        "fix_template": "检查测试用例，修复业务逻辑",
    },
    # Go
    "GO_COMPILE_ERROR": {
        "regex": r"go:.*cannot find main|undefined:",
        "category": "compile_error",
        "fix_template": "检查包引用和函数定义",
    },
}


# ============================================================================
# 核心函数
# ============================================================================

def detect_error_pattern(error_message: str) -> Optional[dict]:
    """识别错误模式"""
    for pattern_name, info in ERROR_PATTERNS.items():
        if re.search(info["regex"], error_message, re.IGNORECASE):
            return {
                "pattern": pattern_name,
                "category": info["category"],
                "fix_template": info["fix_template"],
                "raw_error": error_message[:200],
            }
    return None


def extract_reflection(
    task_description: str,
    error_message: str,
    attempted_fix: str,
    pattern_info: dict,
) -> dict:
    """
    生成 Reflexion 式反思记录。
    对应 pattern_065：让模型在失败后生成自然语言反思。
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "task": task_description,
        "error_pattern": pattern_info["pattern"],
        "error_category": pattern_info["category"],
        "raw_error": error_message[:500],
        "attempted_fix": attempted_fix[:300],
        "root_cause_analysis": generate_root_cause(task_description, error_message),
        "suggested_fix": pattern_info["fix_template"],
        "should_update_skill": should_update_skill(pattern_info["category"]),
    }


def generate_root_cause(task: str, error: str) -> str:
    """
    基于错误信息生成根因分析（简单规则版）。
    实际项目中可接入 LLM 进行深度分析。
    """
    error_lower = error.lower()
    task_lower = task.lower()

    if "undefined" in error_lower or "null" in error_lower:
        return "未处理 null/undefined 边界条件"
    if "type" in error_lower and "assign" in error_lower:
        return "类型定义不完整或不匹配"
    if "module" in error_lower and "not found" in error_lower:
        return "依赖缺失或未正确安装"
    if "sql" in error_lower or "query" in error_lower:
        return "SQL 语句构建有问题，可能缺少参数化"
    if "permission" in error_lower or "denied" in error_lower:
        return "权限不足，检查文件/数据库权限配置"
    if "timeout" in error_lower:
        return "操作超时，检查数据库连接或网络延迟"
    if "syntax" in error_lower:
        return "代码语法错误，检查最近修改的代码结构"

    return "需要人工分析根因"


def should_update_skill(category: str) -> bool:
    """判断是否需要更新 Skill"""
    # 高频错误模式值得抽象为 Skill
    high_frequency = {"null_safety", "import_error", "type_mismatch", "sql_syntax"}
    return category in high_frequency


def load_existing_records(filepath: Path) -> list[dict]:
    """加载已有的模式记录"""
    if not filepath.exists():
        return []
    try:
        content = filepath.read_text(encoding="utf-8")
        # 解析 markdown 中的 YAML frontmatter 或 JSON 块
        records = []
        in_json = False
        current = []
        for line in content.split("\n"):
            if line.strip() == "```json":
                in_json = True
                current = []
            elif line.strip() == "```":
                if in_json and current:
                    try:
                        records.append(json.loads("".join(current)))
                    except json.JSONDecodeError:
                        pass
                in_json = False
                current = []
            elif in_json:
                current.append(line + "\n")
        return records
    except Exception:
        return []


def append_record(filepath: Path, record: dict):
    """追加记录到文件"""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if filepath.exists():
        content = filepath.read_text(encoding="utf-8")
    else:
        content = ""

    # 添加新记录
    new_entry = f"\n\n### {record['timestamp'][:10]} — {record.get('error_pattern', 'UNKNOWN')}\n\n```json\n{json.dumps(record, ensure_ascii=False, indent=2)}\n```\n"
    content += new_entry
    filepath.write_text(content, encoding="utf-8")


def generate_summary_report(records: list[dict], output_path: Path):
    """生成失败模式汇总报告"""
    # 按类别统计
    stats = {}
    for r in records:
        cat = r.get("error_category", "unknown")
        if cat not in stats:
            stats[cat] = {"count": 0, "patterns": set()}
        stats[cat]["count"] += 1
        stats[cat]["patterns"].add(r.get("error_pattern", "unknown"))

    report = f"""# 失败模式汇总报告

> 生成时间：{datetime.now().isoformat()}
> 总失败次数：{len(records)}

## 按类别统计

| 类别 | 次数 | 常见模式 |
|-----|------|---------|
"""
    for cat, info in sorted(stats.items(), key=lambda x: -x[1]["count"]):
        patterns = ", ".join(list(info["patterns"])[:3])
        report += f"| {cat} | {info['count']} | {patterns} |\n"

    report += f"\n## 推荐 Skill 迭代\n\n"
    skills_to_add = set()
    for r in records:
        if r.get("should_update_skill"):
            skills_to_add.add(r.get("error_category", "unknown"))
    for skill in sorted(skills_to_add):
        report += f"- [ ] 在 `skills/{skill}/SKILL.md` 中添加处理规则\n"

    output_path.write_text(report, encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Reflexion 失败模式自动积累工具"
    )
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--error", required=True, help="错误信息")
    parser.add_argument("--fix-attempt", default="", help="已尝试的修复方案")
    parser.add_argument("--success", action="store_true", help="标记为成功（不记录错误）")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--output-dir", default=".loop", help="输出目录（默认 .loop）")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_dir = project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.success:
        # 成功模式记录
        success_file = output_dir / "SUCCESS_PATTERNS.jsonl"
        record = {
            "timestamp": datetime.now().isoformat(),
            "task": args.task,
            "status": "success",
        }
        with open(success_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"✅ 成功模式已记录到 {success_file}")
        return 0

    # 失败模式记录
    pattern_info = detect_error_pattern(args.error)
    if not pattern_info:
        pattern_info = {"pattern": "UNKNOWN", "category": "unknown", "fix_template": "需要人工分析"}

    reflection = extract_reflection(
        task_description=args.task,
        error_message=args.error,
        attempted_fix=args.fix_attempt,
        pattern_info=pattern_info,
    )

    # 写入 ERRORS.md
    errors_file = output_dir / "ERRORS.md"
    append_record(errors_file, reflection)
    print(f"❌ 失败模式已记录到 {errors_file}")

    # 生成 JSONL 便于程序处理
    jsonl_file = output_dir / "failures.jsonl"
    with open(jsonl_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(reflection, ensure_ascii=False) + "\n")

    # 生成汇总报告
    records = load_existing_records(errors_file)
    summary_file = output_dir / "FAILURES_REPORT.md"
    generate_summary_report(records, summary_file)
    print(f"📊 汇总报告已生成：{summary_file}")

    # 打印关键信息
    print(f"\n--- 失败分析 ---")
    print(f"错误模式：{pattern_info['pattern']}")
    print(f"推荐修复：{reflection['suggested_fix']}")
    print(f"根因分析：{reflection['root_cause_analysis']}")
    print(f"建议更新 Skill：{'是' if reflection['should_update_skill'] else '否'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
