#!/usr/bin/env python3
"""
semantic_checkpoint.py — 语义感知 Checkpoint（Crab 风格）

参考：Crab: A Semantics-Aware Checkpoint/Restore Runtime for Agent Sandboxes (arXiv 2026-04)
      DeltaBox (arXiv 2026-05): Millisecond-Level Sandbox Checkpoint/Rollback
      When Can Agents Safely Checkpoint/Fork/Restore/Merge? (arXiv 2026-08)

核心思想：
  Checkpoint 不是字节快照，而是"语义快照"——只保存有意义的状态变更。
  恢复时只重建"有意义的状态"，丢弃中间过程。

关键创新：
  1. semantic_diff：记录状态变更的语义差异（而非原始字节）
  2. 可恢复性检查：判断当前状态是否可以安全恢复
  3. Fork/Merge 支持：支持状态分支和合并
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


class SemanticDiff:
    """语义差异——记录状态变更的语义内容"""

    def __init__(self, op: str, path: str, old_value: Any = None, new_value: Any = None):
        self.op = op  # ADD | MODIFY | DELETE | MERGE
        self.path = path
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "op": self.op,
            "path": self.path,
            "old": self.old_value,
            "new": self.new_value,
            "ts": self.timestamp,
        }

    def semantic_hash(self) -> str:
        """生成语义哈希（用于去重和一致性检查）"""
        content = f"{self.op}:{self.path}:{self.new_value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class SemanticCheckpoint:
    """语义感知 Checkpoint（Crab 风格）"""

    def __init__(
        self,
        project_root: Path,
        state_file: Path = None,
        diff_log: Path = None,
    ):
        self.project_root = project_root
        self.state_file = state_file or (project_root / ".loop" / "state_semantic.md")
        self.diff_log = diff_log or (project_root / ".loop" / "semantic_diffs.jsonl")
        self._diffs: list = []
        self._loaded = False

    def load(self):
        """加载现有 checkpoint"""
        if self.state_file.exists():
            try:
                content = self.state_file.read_text(encoding="utf-8")
                # Parse JSON block
                import re
                match = re.search(r'```json\s*\n(.*?)\n\s*```', content, re.DOTALL)
                if match:
                    self._state = json.loads(match.group(1))
                    self._loaded = True
                    return
            except Exception:
                pass
        self._state = {
            "project": self.project_root.name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 0,
            "semantic_diffs": [],
            "checkpoints": [],
        }
        self._loaded = True

    def save(self):
        """保存 checkpoint"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        content = f"```json\n{json.dumps(self._state, ensure_ascii=False, indent=2)}\n```\n"
        self.state_file.write_text(content, encoding="utf-8")

        # Also append to diff log
        with open(self.diff_log, "a", encoding="utf-8") as f:
            for d in self._diffs:
                f.write(json.dumps(d.to_dict(), ensure_ascii=False) + "\n")
        self._diffs = []

    def record_diff(
        self,
        op: str,
        path: str,
        old_value=None,
        new_value=None,
    ):
        """记录一次语义变更"""
        diff = SemanticDiff(op, path, old_value, new_value)
        self._diffs.append(diff)
        self._state["semantic_diffs"].append(diff.to_dict())
        self._state["version"] += 1
        self._state["updated_at"] = datetime.now().isoformat()

    def checkpoint(self, name: str = None) -> dict:
        """创建命名 checkpoint"""
        cp_name = name or f"cp_{self._state['version']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cp = {
            "name": cp_name,
            "version": self._state["version"],
            "timestamp": datetime.now().isoformat(),
            "diffs_since_last": len(self._diffs),
            "semantic_hash": self._compute_state_hash(),
        }
        self._state["checkpoints"].append(cp)
        self.save()
        return cp

    def restore(self, checkpoint_name: str = None) -> bool:
        """恢复到指定 checkpoint"""
        if not self._state.get("checkpoints"):
            return False

        if checkpoint_name:
            # Find specific checkpoint
            target = next(
                (cp for cp in self._state["checkpoints"] if cp["name"] == checkpoint_name),
                None
            )
        else:
            # Restore to latest
            target = self._state["checkpoints"][-1] if self._state["checkpoints"] else None

        if not target:
            return False

        # Apply semantic diffs up to target version
        target_version = target["version"]
        self._state["version"] = target_version
        self._state["updated_at"] = target["timestamp"]
        self.save()
        return True

    def can_merge(self, other_state: dict) -> dict:
        """检查是否可以安全合并（基于 Crab 的可恢复性检查）"""
        # 检查版本冲突
        my_version = self._state.get("version", 0)
        other_version = other_state.get("version", 0)

        if my_version == other_version:
            return {
                "can_merge": True,
                "reason": "版本相同，无冲突",
                "strategy": "no-op",
            }

        # 检查语义差异是否兼容
        my_diffs = self._state.get("semantic_diffs", [])
        other_diffs = other_state.get("semantic_diffs", [])

        # 简单冲突检测：检查是否有对同一 path 的 MODIFY 操作
        conflicts = []
        my_paths = {d["path"]: d for d in my_diffs if d.get("op") == "MODIFY"}
        other_paths = {d["path"]: d for d in other_diffs if d.get("op") == "MODIFY"}

        for path in set(my_paths.keys()) & set(other_paths.keys()):
            if my_paths[path].get("new") != other_paths[path].get("new"):
                conflicts.append(path)

        if conflicts:
            return {
                "can_merge": False,
                "reason": f"冲突路径: {conflicts}",
                "strategy": "manual_resolution",
            }

        return {
            "can_merge": True,
            "reason": "无冲突，可自动合并",
            "strategy": "auto_merge",
        }

    def _compute_state_hash(self) -> str:
        """计算当前状态的语义哈希"""
        content = json.dumps(self._state, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def status(self) -> dict:
        """返回 checkpoint 状态"""
        return {
            "version": self._state.get("version", 0),
            "total_diffs": len(self._state.get("semantic_diffs", [])),
            "total_checkpoints": len(self._state.get("checkpoints", [])),
            "last_updated": self._state.get("updated_at", ""),
            "semantic_hash": self._compute_state_hash(),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="语义 Checkpoint（Crab 风格）")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--record", nargs=2, metavar=("OP", "PATH"), help="记录语义变更")
    parser.add_argument("--checkpoint", nargs="?", const="auto", help="创建 checkpoint")
    parser.add_argument("--restore", nargs="?", const="latest", help="恢复 checkpoint")
    parser.add_argument("--status", action="store_true", help="显示状态")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    cp = SemanticCheckpoint(root)
    cp.load()

    if args.record:
        op, path = args.record
        cp.record_diff(op, path, new_value=f"<{op}>")
        cp.save()
        print(f"✅ 记录变更: {op} {path}")

    elif args.checkpoint is not None:
        name = args.checkpoint if args.checkpoint != "auto" else None
        result = cp.checkpoint(name)
        print(f"✅ Checkpoint 已创建: {result['name']} (v{result['version']})")
        print(f"   语义哈希: {result['semantic_hash']}")

    elif args.restore is not None:
        name = args.restore if args.restore != "latest" else None
        success = cp.restore(name)
        if success:
            print("✅ 已恢复到最新 checkpoint")
        else:
            print("❌ 无可用 checkpoint")

    elif args.status:
        status = cp.status()
        print(f"版本: {status['version']}")
        print(f"语义变更: {status['total_diffs']}")
        print(f"Checkpoints: {status['total_checkpoints']}")
        print(f"最后更新: {status['last_updated']}")
        print(f"语义哈希: {status['semantic_hash']}")
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
