#!/usr/bin/env python3
"""
harness/code.py — Code as Agent Harness

将 AGENTS.md 规则编译为可执行校验函数（Code as Harness 理念）。
来源：Code as Agent Harness (arXiv 2026-05-18)

设计原则：
  1. AGENTS.md 是"规范"，本模块是"编译器+运行时"
  2. 每个规则 → 一个独立的校验函数
  3. 校验结果 → 结构化报告（通过/失败/诊断）
  4. 可组合：多个校验函数串联为验证管道

用法：
  from harness.code import AgentHarness
  harness = AgentHarness()
  result = harness.validate_task(
      task="实现用户认证",
      output_code="def authenticate(...)",
      context_files=["@src/auth/jwt.py"]
  )
  print(result.report())
"""

import re
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class CheckResult:
    """单个检查项的结果"""
    name: str
    passed: bool
    severity: str  # critical | high | medium | low
    message: str = ""
    diagnosis: str = ""  # AgentDoG 风格诊断
    fix_suggestion: str = ""

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "diagnosis": self.diagnosis,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class ValidationReport:
    """完整验证报告"""
    task: str
    timestamp: str
    checks: list = field(default_factory=list)
    score: float = 0.0
    status: str = "unknown"  # pass | warning | fail

    def add_check(self, result: CheckResult):
        self.checks.append(result)

    def summary(self) -> dict:
        critical = [c for c in self.checks if c.severity == "critical" and not c.passed]
        high = [c for c in self.checks if c.severity == "high" and not c.passed]
        return {
            "task": self.task,
            "timestamp": self.timestamp,
            "total_checks": len(self.checks),
            "passed": sum(1 for c in self.checks if c.passed),
            "failed": sum(1 for c in self.checks if not c.passed),
            "critical_failures": len(critical),
            "high_failures": len(high),
            "score": self.score,
            "status": self.status,
            "details": [c.to_dict() for c in self.checks],
        }

    def report(self) -> str:
        s = self.summary()
        lines = [
            f"# Harness 验证报告",
            f"",
            f"**任务**: {s['task']}",
            f"**时间**: {s['timestamp']}",
            f"**状态**: {s['status'].upper()}",
            f"**得分**: {s['score']:.1f}/100",
            f"",
            f"| 指标 | 值 |",
            f"|-----|-----|",
            f"| 总检查项 | {s['total_checks']} |",
            f"| 通过 | {s['passed']} |",
            f"| 失败 | {s['failed']} |",
            f"| Critical | {s['critical_failures']} |",
            f"| High | {s['high_failures']} |",
            f"",
            f"## 详细结果",
            f"",
        ]
        for c in self.checks:
            icon = "✅" if c.passed else "❌"
            lines.append(f"### {icon} {c.name} [{c.severity}]")
            lines.append(f"")
            if c.message:
                lines.append(f"**输出**: {c.message}")
            if c.diagnosis:
                lines.append(f"**诊断**: {c.diagnosis}")
            if c.fix_suggestion:
                lines.append(f"**建议修复**: {c.fix_suggestion}")
            lines.append("")
        return "\n".join(lines)


# ============================================================================
# 检查函数（每个对应 AGENTS.md 中的一条规则）
# ============================================================================

def check_file_path_reference(task: str, output: str, context: dict) -> CheckResult:
    """检查 2.1 文件引用：必须使用完整路径"""
    # 查找可能的相对路径引用（不以下划线/点开头的路径）
    relative_patterns = re.findall(r'(?<![@])\b(src/|lib/|app/|tests/)[\w/.-]+', output)
    issues = []
    for p in relative_patterns:
        if p not in output.lower():
            continue
        # 检查是否已有完整路径
        if '@' + p.split('/')[0] not in output and 'E:/' not in output and '/' not in p[:3]:
            issues.append(p)

    if issues:
        return CheckResult(
            name="文件路径引用",
            passed=False,
            severity="high",
            message=f"发现 {len(issues)} 个相对路径引用: {issues[:3]}",
            diagnosis="Agent 使用了相对路径而非完整路径，导致上下文搜索成本增加",
            fix_suggestion="将所有文件引用改为完整路径格式：@E:/项目/xxx/yyy.ts",
        )
    return CheckResult(name="文件路径引用", passed=True, severity="high",
                       message="所有文件引用均使用完整路径")


def check_byte_truncation(task: str, output: str, context: dict) -> CheckResult:
    """检查 2.2 字节截断：大文件是否被截断"""
    # 检查是否有 head/tail 命令或截断标记
    has_truncation = 'head -c 4000' in output or 'tail -c 4000' in output or '[truncated]' in output
    # 检查是否有超大代码块（>2000字符的单行）
    long_lines = [l for l in output.split('\n') if len(l) > 2000]
    if long_lines and not has_truncation:
        return CheckResult(
            name="字节截断",
            passed=False,
            severity="medium",
            message=f"发现 {len(long_lines)} 行长代码（>2000字符），未检测到截断标记",
            diagnosis="大文件未截断可能导致上下文溢出或 Token 浪费",
            fix_suggestion="使用 head -c 4000 / tail -c 4000 截断大文件内容",
        )
    return CheckResult(name="字节截断", passed=has_truncation or len(long_lines) == 0,
                       severity="medium",
                       message="截断策略正确" if has_truncation else "无大文件需要截断")


def check_intent_completeness(task: str, output: str, context: dict) -> CheckResult:
    """检查 2.4 意图一次说完：目标+文件+期望+验收"""
    has_goal = any(k in output.lower() for k in ['目标', 'goal', '要完成', 'implement'])
    has_file = '@' in output or 'file' in output.lower() or '路径' in output
    has_acceptance = any(k in output.lower() for k in ['验收', 'accept', 'test', '验证', '通过'])
    has_format = any(k in output.lower() for k in ['格式', 'format', '输出', 'return'])

    missing = []
    if not has_goal: missing.append('目标')
    if not has_file: missing.append('文件')
    if not has_acceptance: missing.append('验收条件')
    if not has_format: missing.append('输出格式')

    if missing:
        return CheckResult(
            name="意图完整性",
            passed=False,
            severity="high",
            message=f"缺少: {', '.join(missing)}",
            diagnosis="意图描述不完整，可能导致 Agent 误解任务范围",
            fix_suggestion="按模板重写：目标→文件→期望→验收条件",
        )
    return CheckResult(name="意图完整性", passed=True, severity="high",
                       message="意图描述完整（目标+文件+验收+格式）")


def check_output_format(task: str, output: str, context: dict) -> CheckResult:
    """检查输出格式是否符合规范"""
    # 代码任务：不应有大段解释
    lines = output.split('\n')
    code_lines = sum(1 for l in lines if l.strip().startswith('```') or
                     l.strip().startswith('def ') or l.strip().startswith('class ') or
                     l.strip().startswith('import ') or l.strip().startswith('const ') or
                     l.strip().startswith('let ') or l.strip().startswith('func '))
    total_non_empty = sum(1 for l in lines if l.strip())

    if total_non_empty > 20 and code_lines / max(total_non_empty, 1) < 0.3:
        return CheckResult(
            name="输出格式",
            passed=False,
            severity="medium",
            message=f"代码占比仅 {code_lines}/{total_non_empty} ({code_lines/max(total_non_empty,1)*100:.0f}%)，解释过多",
            diagnosis="代码任务输出含过多解释，违反'只返回代码'规则",
            fix_suggestion="删除解释性文字，只保留代码",
        )
    return CheckResult(name="输出格式", passed=True, severity="medium",
                       message="输出格式正常")


def check_loop_constraints(task: str, output: str, context: dict) -> CheckResult:
    """检查 Loop 约束：是否有验证命令和重试限制"""
    has_verify = any(k in output for k in ['pytest', 'npm test', 'go test', 'npx vitest',
                                             '验收命令', '验证', 'lint', 'build'])
    has_limit = '最多' in output or 'max' in output.lower() or '上限' in output or '≤3' in output
    has_diagnostic = any(k in output for k in ['收敛', '多样性', '振荡', '分布', '诊断信号'])

    issues = []
    if not has_verify:
        issues.append("缺少验证命令")
    if not has_limit:
        issues.append("缺少重试上限")
    if not has_diagnostic:
        issues.append("缺少诊断信号")

    if issues:
        return CheckResult(
            name="Loop 约束",
            passed=False,
            severity="high",
            message=f"Loop 设计缺陷: {', '.join(issues)}",
            diagnosis="未遵循 loop-engineering Skill 的约束要求",
            fix_suggestion="添加验证命令、重试上限（≤3次）、诊断信号监控",
        )
    return CheckResult(name="Loop 约束", passed=True, severity="high",
                       message="Loop 约束设计完整")


def check_security_rules(task: str, output: str, context: dict) -> CheckResult:
    """检查 6.3 安全护栏：危险操作确认"""
    dangerous_ops = ['rm -rf', 'delete()', 'drop_table', 'format_disk', 'wipe', 'sudo rm']
    found = [op for op in dangerous_ops if op in output]
    if found:
        has_confirm = '人工确认' in output or 'confirm' in output.lower() or '单向门' in output
        if not has_confirm:
            return CheckResult(
                name="安全护栏",
                passed=False,
                severity="critical",
                message=f"发现危险操作但未确认: {found}",
                diagnosis="危险操作未经过人工确认，违反安全护栏规则",
                fix_suggestion="对危险操作添加人工确认步骤（单向门）",
            )
    return CheckResult(name="安全护栏", passed=True, severity="critical",
                       message="安全规则遵守" if not found else "危险操作已确认")


def check_error_feedback(task: str, output: str, context: dict) -> CheckResult:
    """检查错误回灌格式是否符合规范"""
    has_format = ('上次执行失败' in output or '错误信息' in output or
                  'file_path' in output or 'line_number' in output)
    if has_format:
        return CheckResult(name="错误回灌格式", passed=True, severity="medium",
                           message="错误回灌格式规范")
    # 检查是否有错误处理逻辑
    has_error_handling = 'except' in output or 'try:' in output or 'retry' in output.lower()
    if has_error_handling:
        return CheckResult(name="错误回灌格式", passed=True, severity="low",
                           message="有错误处理但格式非标准")
    return CheckResult(name="错误回灌格式", passed=False, severity="medium",
                       message="缺少结构化错误回灌",
                       diagnosis="错误信息未按规范格式回灌，降低修复效率",
                       fix_suggestion="使用标准格式：文件+行号+错误信息+类型")


# ============================================================================
# 主 Harness
# ============================================================================

CHECK_FUNCTIONS = [
    check_file_path_reference,
    check_intent_completeness,
    check_output_format,
    check_loop_constraints,
    check_security_rules,
    check_error_feedback,
    check_byte_truncation,
]

# 严重度权重（用于评分）
SEVERITY_WEIGHT = {"critical": 10, "high": 7, "medium": 4, "low": 1}


class AgentHarness:
    """可执行的 Agent Harness — 将 AGENTS.md 规则编译为校验函数"""

    def __init__(self):
        self.checks = CHECK_FUNCTIONS.copy()
        self.version = "3.3.0"
        self.last_report: Optional[ValidationReport] = None

    def validate_task(self, task: str, output: str, context: dict = None) -> ValidationReport:
        """运行所有检查，返回验证报告"""
        ctx = context or {}
        report = ValidationReport(task=task, timestamp=datetime.now().isoformat())

        total_weight = 0
        earned_weight = 0

        for check_fn in self.checks:
            try:
                result = check_fn(task, output, ctx)
            except Exception as e:
                result = CheckResult(
                    name=check_fn.__name__,
                    passed=False,
                    severity="high",
                    message=f"检查函数异常: {e}",
                    diagnosis="检查函数内部错误",
                )
            report.add_check(result)
            w = SEVERITY_WEIGHT.get(result.severity, 1)
            total_weight += w
            if result.passed:
                earned_weight += w

        report.score = round(earned_weight / max(total_weight, 1) * 100, 1)
        critical_fails = sum(1 for c in report.checks if c.severity == "critical" and not c.passed)
        high_fails = sum(1 for c in report.checks if c.severity == "high" and not c.passed)
        if critical_fails > 0:
            report.status = "fail"
        elif high_fails > 0:
            report.status = "warning"
        elif report.score >= 80:
            report.status = "pass"
        else:
            report.status = "warning"

        self.last_report = report
        return report

    def validate_code(self, code: str, language: str = "python") -> ValidationReport:
        """专门针对代码输出的验证"""
        return self.validate_task(
            task=f"代码生成 ({language})",
            output=code,
            context={"type": "code", "language": language},
        )

    def validate_document(self, text: str) -> ValidationReport:
        """针对文档输出的验证"""
        return self.validate_task(
            task="文档生成",
            output=text,
            context={"type": "document"},
        )

    def batch_validate(self, tasks: list) -> list:
        """批量验证多个任务"""
        return [self.validate_task(t.get("task", ""), t.get("output", ""), t.get("context"))
                for t in tasks]


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent Harness 校验器（Code as Harness）")
    parser.add_argument("--task", help="任务描述")
    parser.add_argument("--output", help="待验证的输出内容（文件或 stdin）")
    parser.add_argument("--file", help="从文件读取输出内容")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    harness = AgentHarness()

    if args.file:
        output = Path(args.file).read_text(encoding="utf-8")
    elif args.output:
        output = args.output
    else:
        # 从 stdin 读取
        output = sys.stdin.read()

    task = args.task or "未知任务"
    report = harness.validate_task(task, output)

    if args.json:
        print(json.dumps(report.summary(), ensure_ascii=False, indent=2))
    else:
        print(report.report())

    # 返回非零退出码如果有关键失败
    if report.status == "fail":
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
