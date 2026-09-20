#!/usr/bin/env python3
"""
harness/scorecard.py — Harness 质量评分卡

参考：HarnessRisk (arXiv 2026-08-18) 安全生命周期基准
      Code as Agent Harness (arXiv 2026-05-18)
      
评分维度（7 维，对应 G7 七维审查）：
  1. Security — 安全护栏完整性
  2. Correctness — 逻辑正确性验证
  3. Performance — Token/RPM 效率
  4. Maintainability — 规则可维护性
  5. Testing — 验证覆盖度
  6. Accessibility — Skill 可发现性
  7. Documentation — 文档完整性
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class DimensionScore:
    name: str
    weight: int  # 1-10
    score: float  # 0-100
    issues: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)

    @property
    def weighted_score(self):
        return self.score * self.weight / 10.0


@dataclass
class Scorecard:
    project: str
    version: str
    timestamp: str
    dimensions: list = field(default_factory=list)
    overall_score: float = 0.0
    grade: str = "F"

    def add_dimension(self, dim: DimensionScore):
        self.dimensions.append(dim)

    def compute_overall(self):
        if not self.dimensions:
            return 0.0
        total_weight = sum(d.weight for d in self.dimensions)
        weighted_sum = sum(d.weighted_score for d in self.dimensions)
        self.overall_score = round(weighted_sum / max(total_weight, 1) * 10, 1)
        # Grade mapping
        if self.overall_score >= 90:
            self.grade = "A"
        elif self.overall_score >= 80:
            self.grade = "B"
        elif self.overall_score >= 70:
            self.grade = "C"
        elif self.overall_score >= 60:
            self.grade = "D"
        else:
            self.grade = "F"
        return self.overall_score

    def to_dict(self):
        return {
            "project": self.project,
            "version": self.version,
            "timestamp": self.timestamp,
            "overall_score": self.overall_score,
            "grade": self.grade,
            "dimensions": [
                {
                    "name": d.name,
                    "weight": d.weight,
                    "score": d.score,
                    "weighted": d.weighted_score,
                    "issues": d.issues,
                    "suggestions": d.suggestions,
                }
                for d in self.dimensions
            ],
        }

    def report(self) -> str:
        lines = [
            "# Harness 质量评分卡",
            f"",
            f"**项目**: {self.project}",
            f"**版本**: {self.version}",
            f"**评分时间**: {self.timestamp}",
            f"**综合得分**: **{self.overall_score}/100** ({self.grade})",
            f"",
            f"| 维度 | 权重 | 得分 | 加权分 | 状态 |",
            f"|-----|-----|-----|-------|-----|",
        ]
        for d in self.dimensions:
            status = "✅" if d.score >= 70 else ("⚠️" if d.score >= 50 else "❌")
            lines.append(
                f"| {d.name} | {d.weight} | {d.score:.0f} | {d.weighted_score:.1f} | {status} |"
            )
            for issue in d.issues[:2]:
                lines.append(f"  - ⚠️ {issue}")
            for sug in d.suggestions[:1]:
                lines.append(f"  - 💡 {sug}")
        lines.append("")
        lines.append("## 改进建议")
        lines.append("")
        all_suggestions = []
        for d in self.dimensions:
            for s in d.suggestions:
                all_suggestions.append(f"- {d.name}: {s}")
        if all_suggestions:
            lines.extend(all_suggestions)
        else:
            lines.append("- 所有维度表现良好，无需改进")
        return "\n".join(lines)


def assess_harness(project_root: Path) -> Scorecard:
    """评估项目的 Harness 质量"""
    card = Scorecard(
        project=project_root.name,
        version="3.3.0",
        timestamp=datetime.now().isoformat(),
    )

    # 1. Security — 安全护栏完整性
    security_issues = []
    security_sugs = []
    agnts = (project_root / "AGENTS.md").read_text(encoding="utf-8") if (project_root / "AGENTS.md").exists() else ""
    if "危险操作白名单" not in agnts:
        security_issues.append("AGENTS.md 缺少危险操作白名单")
        security_sugs.append("添加 SAFE/RISKY/BLOCKED 操作分类")
    if "prompt injection" not in agnts.lower():
        security_issues.append("缺少 prompt injection 检测规则")
        security_sugs.append("添加输入护栏：检测注入攻击模式")
    security_score = max(0, 100 - len(security_issues) * 25)
    card.add_dimension(DimensionScore("Security", 10, security_score, security_issues, security_sugs))

    # 2. Correctness — 逻辑正确性验证
    correctness_issues = []
    correctness_sugs = []
    has_test = (project_root / "scripts" / "verify-project.py").exists()
    has_loop = (project_root / ".loop" / "state.md").exists()
    if not has_test:
        correctness_issues.append("缺少项目验证脚本")
        correctness_sugs.append("创建 verify-project.py 验证完整性")
    if not has_loop:
        correctness_issues.append("缺少 Loop 状态管理")
        correctness_sugs.append("初始化 .loop/ 目录和 state.md")
    correctness_score = max(0, 100 - len(correctness_issues) * 30)
    card.add_dimension(DimensionScore("Correctness", 9, correctness_score, correctness_issues, correctness_sugs))

    # 3. Performance — Token/RPM 效率
    perf_issues = []
    perf_sugs = []
    has_rpm = (project_root / "rpm-budget-strategy.md").exists()
    has_context = (project_root / "context-kernel.py").exists()
    if not has_rpm:
        perf_issues.append("缺少 RPM 预算策略")
        perf_sugs.append("创建 rpm-budget-strategy.md")
    if not has_context:
        perf_issues.append("缺少上下文优化工具")
        perf_sugs.append("集成 context-kernel.py")
    perf_score = max(0, 100 - len(perf_issues) * 25)
    card.add_dimension(DimensionScore("Performance", 8, perf_score, perf_issues, perf_sugs))

    # 4. Maintainability — 规则可维护性
    maint_issues = []
    maint_sugs = []
    skills_count = len(list((project_root / "skills").rglob("SKILL.md"))) if (project_root / "skills").exists() else 0
    if skills_count < 5:
        maint_issues.append(f"Skill 数量不足（{skills_count} < 5）")
        maint_sugs.append("扩展 Skill 库覆盖更多场景")
    agnts_size = len(agnts) if agnts else 0
    if agnts_size > 10000:
        maint_issues.append("AGENTS.md 过长（>10KB），维护成本高")
        maint_sugs.append("拆分 AGENTS.md 为多文件 + 主入口")
    maint_score = max(0, 100 - len(maint_issues) * 20)
    card.add_dimension(DimensionScore("Maintainability", 7, maint_score, maint_issues, maint_sugs))

    # 5. Testing — 验证覆盖度
    test_issues = []
    test_sugs = []
    has_workflow = (project_root / "scripts" / "workflow-engine.py").exists()
    has_kb_tool = (project_root / "scripts" / "kb-consolidator.py").exists()
    has_harness = (project_root / "harness" / "code.py").exists()
    if not has_workflow:
        test_issues.append("缺少工作流引擎")
        test_sugs.append("实现 scripts/workflow-engine.py")
    if not has_kb_tool:
        test_issues.append("缺少知识库整合工具")
        test_sugs.append("实现 scripts/kb-consolidator.py")
    if not has_harness:
        test_issues.append("缺少 Harness 校验器")
        test_sugs.append("实现 harness/code.py")
    test_score = max(0, 100 - len(test_issues) * 20)
    card.add_dimension(DimensionScore("Testing", 9, test_score, test_issues, test_sugs))

    # 6. Accessibility — Skill 可发现性
    acc_issues = []
    acc_sugs = []
    zcode_skills = Path.home() / ".zcode" / "skills"
    installed = sum(1 for d in (zcode_skills.glob("*") if zcode_skills.exists() else []) if (d / "SKILL.md").exists())
    if installed < 5:
        acc_issues.append(f"ZCode 安装的 Skill 不足（{installed} < 5）")
        acc_sugs.append("运行 cp -r skills/* ~/.zcode/skills/ 安装 Skill")
    acc_score = min(100, installed * 20)
    card.add_dimension(DimensionScore("Accessibility", 6, acc_score, acc_issues, acc_sugs))

    # 7. Documentation — 文档完整性
    doc_issues = []
    doc_sugs = []
    docs = ["AGENTS.md", "HANDOFF.md", "落地执行手册.md", "workflow-v3.md"]
    missing_docs = [d for d in docs if not (project_root / d).exists()]
    if missing_docs:
        doc_issues.append(f"缺少文档: {', '.join(missing_docs)}")
        doc_sugs.append("完善项目文档")
    doc_score = max(0, 100 - len(missing_docs) * 25)
    card.add_dimension(DimensionScore("Documentation", 5, doc_score, doc_issues, doc_sugs))

    card.compute_overall()
    return card


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Harness 质量评分卡")
    parser.add_argument("--project", default=".", help="项目根目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--output", help="保存到文件")
    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    card = assess_harness(project_root)

    if args.json:
        output = json.dumps(card.to_dict(), ensure_ascii=False, indent=2)
    else:
        output = card.report()

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"评分卡已保存到: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
