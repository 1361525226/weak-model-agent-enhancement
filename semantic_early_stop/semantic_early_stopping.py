#!/usr/bin/env python3
"""
semantic_early_stopping.py — 语义早停检测器

参考：Semantic Early-Stopping for Iterative LLM Agent Loops (arXiv 2026-06)
      LoopCoder-v2 四维诊断信号（收敛信号、方案多样性、振荡信号、分布偏移）

核心思想：不是等固定轮次，而是检测"语义是否已收敛"——当连续 N 轮的 diff 无实质变化时提前停止。
这解决了 LoopCoder-v2 发现的 R≥3 后性能骤降问题。
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional


def semantic_hash(text: str) -> str:
    """生成文本的语义哈希（忽略空白和标点）"""
    clean = re.sub(r'\s+', ' ', text.lower().strip())
    clean = re.sub(r'[^\w\u4e00-\u9fff]', '', clean)
    return hash(clean) & 0xFFFFFFFF


def compute_convergence_signal(
    prev_diff: Optional[str],
    curr_diff: str,
    window: int = 3,
) -> dict:
    """
    计算收敛信号。
    返回：{'converged': bool, 'signal': str, 'detail': str}
    """
    if not prev_diff:
        return {"converged": False, "signal": "no_baseline", "detail": "首轮，无基线"}

    # 1. 语义相似度
    prev_hash = semantic_hash(prev_diff)
    curr_hash = semantic_hash(curr_diff)

    # 2. 重叠 token 比例（简单版）
    prev_tokens = set(prev_diff.lower().split())
    curr_tokens = set(curr_diff.lower().split())
    overlap = len(prev_tokens & curr_tokens) / max(len(prev_tokens | curr_tokens), 1)

    # 3. 行数变化率
    prev_lines = len([l for l in prev_diff.split('\n') if l.strip()])
    curr_lines = len([l for l in curr_diff.split('\n') if l.strip()])
    line_change = abs(curr_lines - prev_lines) / max(prev_lines, 1)

    # 判定收敛
    if overlap > 0.85 and line_change < 0.05:
        return {
            "converged": True,
            "signal": "semantic_stable",
            "detail": f"语义稳定（重叠={overlap:.0%}, 行数变化={line_change:.0%}）",
        }
    elif overlap > 0.70:
        return {
            "converged": False,
            "signal": "diminishing_returns",
            "detail": f"边际收益递减（重叠={overlap:.0%}），建议考虑早停",
        }
    else:
        return {
            "converged": False,
            "signal": "progressing",
            "detail": f"仍在进展中（重叠={overlap:.0%}）",
        }


def detect_oscillation(history: list, window: int = 3) -> dict:
    """
    检测振荡信号：验证通过率是否增减交替。
    对应 LoopCoder-v2 信号③。
    """
    if len(history) < window * 2:
        return {"oscillating": False, "detail": "样本不足"}

    recent = history[-window*2:]
    passes = [1 if h.get("passed", False) else 0 for h in recent]

    # 检测交替模式
    alternations = sum(1 for i in range(1, len(passes)) if passes[i] != passes[i-1])
    alt_ratio = alternations / max(len(passes) - 1, 1)

    if alt_ratio > 0.6:
        return {
            "oscillating": True,
            "detail": f"振荡信号触发（交替率={alt_ratio:.0%}），建议早停",
        }
    return {"oscillating": False, "detail": f"无振荡（交替率={alt_ratio:.0%}）"}


def check_diversity(new_approaches: list, max_history: int = 5) -> dict:
    """
    检测方案多样性。
    对应 LoopCoder-v2 信号②。
    """
    if len(new_approaches) < 2:
        return {"diverse": False, "detail": "单一策略，无法判断多样性"}

    # 简单去重：策略描述的唯一性
    unique = len(set(new_approaches))
    total = len(new_approaches)
    diversity_ratio = unique / max(total, 1)

    if diversity_ratio < 0.3:
        return {
            "diverse": False,
            "detail": f"策略趋同（唯一率={diversity_ratio:.0%}），多样性退化",
        }
    return {
        "diverse": True,
        "detail": f"策略多样（唯一率={diversity_ratio:.0%}）",
    }


class SemanticEarlyStopper:
    """语义早停检测器"""

    def __init__(
        self,
        convergence_threshold: float = 0.85,
        oscillation_threshold: float = 0.6,
        diversity_min: float = 0.3,
        max_consecutive_stable: int = 2,
    ):
        self.convergence_threshold = convergence_threshold
        self.oscillation_threshold = oscillation_threshold
        self.diversity_min = diversity_min
        self.max_consecutive_stable = max_consecutive_stable
        self._history: list = []
        self._consecutive_stable = 0
        self._approaches: list = []

    def record(self, diff: str, passed: bool, approach: str = ""):
        """记录一轮结果"""
        self._history.append({"diff": diff, "passed": passed, "ts": __import__('datetime').datetime.now().isoformat()})
        if approach:
            self._approaches.append(approach)
        # 保持历史窗口
        if len(self._history) > 10:
            self._history = self._history[-10:]
        if len(self._approaches) > 10:
            self._approaches = self._approaches[-10:]

    def check(self) -> dict:
        """检查是否应早停"""
        if len(self._history) < 2:
            return {"should_stop": False, "reason": "样本不足", "signals": {}}

        # 1. 收敛信号
        prev = self._history[-2] if len(self._history) >= 2 else None
        curr = self._history[-1]
        convergence = compute_convergence_signal(
            prev["diff"] if prev else None,
            curr["diff"],
        )

        # 2. 振荡信号
        oscillation = detect_oscillation(self._history)

        # 3. 多样性
        diversity = check_diversity(self._approaches)

        # 4. 连续稳定计数
        if convergence["converged"]:
            self._consecutive_stable += 1
        else:
            self._consecutive_stable = 0

        # 判定
        signals = {
            "convergence": convergence,
            "oscillation": oscillation,
            "diversity": diversity,
            "consecutive_stable": self._consecutive_stable,
        }

        should_stop = False
        reason = ""

        if self._consecutive_stable >= self.max_consecutive_stable:
            should_stop = True
            reason = f"连续 {self._consecutive_stable} 轮语义稳定"
        elif oscillation["oscillating"]:
            should_stop = True
            reason = "振荡信号触发"
        elif not diversity["diverse"] and len(self._history) >= 4:
            should_stop = True
            reason = "策略多样性退化"

        return {
            "should_stop": should_stop,
            "reason": reason,
            "signals": signals,
            "rounds_so_far": len(self._history),
        }

    def reset(self):
        self._history = []
        self._consecutive_stable = 0
        self._approaches = []


def main():
    import argparse
    parser = argparse.ArgumentParser(description="语义早停检测器")
    parser.add_argument("--history", help="JSONL 格式的历史记录文件")
    parser.add_argument("--check", action="store_true", help="仅检查是否应早停")
    args = parser.parse_args()

    stopper = SemanticEarlyStopper()

    if args.history:
        for line in Path(args.history).read_text().splitlines():
            if line.strip():
                try:
                    entry = json.loads(line)
                    stopper.record(
                        diff=entry.get("diff", ""),
                        passed=entry.get("passed", False),
                        approach=entry.get("approach", ""),
                    )
                except json.JSONDecodeError:
                    pass

        result = stopper.check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
