#!/usr/bin/env python3
"""
tool_registry.py — 协议无关工具注册表（ToolRegistry 风格）

参考：ToolRegistry: A Protocol-Agnostic Tool Management Library for Function-Calling LLMs (arXiv 2025-07)

核心思想：
  统一管理所有 MCP/内置工具，提供：
  1. 工具注册/发现/版本管理
  2. 工具能力描述（schema）
  3. 工具调用统计和校准诊断（Calibration Bottleneck）
  4. 协议无关接口（MCP / 内置 / 自定义）
"""
import json
import time
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolRegistry:
    """工具注册表"""
    name: str
    version: str = "1.0.0"
    tools: dict = field(default_factory=dict)
    call_stats: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def register(
        self,
        name: str,
        description: str,
        schema: dict,
        handler: Callable = None,
        category: str = "general",
        tags: list = None,
    ):
        """注册工具"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": schema,
            "handler": handler,
            "category": category,
            "tags": tags or [],
            "registered_at": datetime.now().isoformat(),
            "call_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "avg_latency_ms": 0.0,
        }

    def call(self, tool_name: str, arguments: dict) -> dict:
        """调用工具并统计"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        tool = self.tools[tool_name]
        start = time.time()
        tool["call_count"] += 1

        try:
            if tool["handler"]:
                result = tool["handler"](**arguments)
                tool["success_count"] += 1
                latency = (time.time() - start) * 1000
                tool["avg_latency_ms"] = (
                    (tool["avg_latency_ms"] * (tool["success_count"] - 1) + latency)
                    / tool["success_count"]
                )
                return {"result": result, "latency_ms": round(latency, 1)}
            else:
                return {"error": f"No handler for tool: {tool_name}"}
        except Exception as e:
            tool["failure_count"] += 1
            return {"error": str(e), "tool": tool_name}

    def list_tools(self, category: str = None, tag: str = None) -> list:
        """列出工具（支持分类过滤）"""
        tools = list(self.tools.values())
        if category:
            tools = [t for t in tools if t["category"] == category]
        if tag:
            tools = [t for t in tools if tag in t.get("tags", [])]
        return [
            {
                "name": t["name"],
                "description": t["description"][:80],
                "category": t["category"],
                "call_count": t["call_count"],
                "success_rate": (
                    t["success_count"] / max(t["call_count"], 1) * 100
                ),
            }
            for t in tools
        ]

    def calibration_report(self) -> dict:
        """校准诊断报告（Calibration Bottleneck 风格）"""
        report = {
            "total_tools": len(self.tools),
            "total_calls": sum(t["call_count"] for t in self.tools.values()),
            "overall_success_rate": 0.0,
            "tools_by_category": {},
            "underutilized": [],
            "overused": [],
        }

        total_calls = 0
        total_success = 0

        for name, tool in self.tools.items():
            cats = tool["category"]
            if cats not in report["tools_by_category"]:
                report["tools_by_category"][cats] = {"count": 0, "calls": 0, "failures": 0}
            report["tools_by_category"][cats]["count"] += 1
            report["tools_by_category"][cats]["calls"] += tool["call_count"]
            report["tools_by_category"][cats]["failures"] += tool["failure_count"]

            total_calls += tool["call_count"]
            total_success += tool["success_count"]

            if tool["call_count"] == 0:
                report["underutilized"].append(name)
            elif tool["call_count"] > 100 and tool["failure_count"] / max(tool["call_count"], 1) > 0.3:
                report["overused"].append(name)

        report["overall_success_rate"] = round(
            total_success / max(total_calls, 1) * 100, 1
        )
        return report

    def to_schema(self) -> dict:
        """导出为 LLM 可用的工具 schema"""
        return {
            "name": self.name,
            "version": self.version,
            "tools": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"],
                    "category": t["category"],
                }
                for t in self.tools.values()
            ],
        }


# ============================================================================
# 预注册常用工具
# ============================================================================

def create_default_registry() -> ToolRegistry:
    """创建带有默认工具的注册表"""
    registry = ToolRegistry(name="default", version="1.0.0")

    # 文件系统工具
    registry.register(
        name="read_file",
        description="读取文件内容",
        schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "encoding": {"type": "string", "default": "utf-8"},
            },
            "required": ["path"],
        },
        category="filesystem",
        tags=["read", "file"],
    )

    registry.register(
        name="write_file",
        description="写入文件内容",
        schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"},
            },
            "required": ["path", "content"],
        },
        category="filesystem",
        tags=["write", "file"],
    )

    # 命令执行工具
    registry.register(
        name="run_command",
        description="执行 shell 命令",
        schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "命令"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["command"],
        },
        category="execution",
        tags=["shell", "command"],
    )

    # Git 工具
    registry.register(
        name="git_status",
        description="查看 git 状态",
        schema={"type": "object", "properties": {}},
        category="git",
        tags=["git", "status"],
    )

    registry.register(
        name="git_diff",
        description="查看 git diff",
        schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（可选）"},
            },
        },
        category="git",
        tags=["git", "diff"],
    )

    # Harness 工具
    registry.register(
        name="harness_validate",
        description="运行 Harness 校验",
        schema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "任务描述"},
                "output": {"type": "string", "description": "待验证输出"},
            },
            "required": ["task", "output"],
        },
        category="harness",
        tags=["harness", "validate"],
    )

    return registry


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ToolRegistry — 协议无关工具管理")
    parser.add_argument("--register", nargs=2, metavar=("NAME", "DESC"), help="注册工具")
    parser.add_argument("--list", nargs="?", const="", help="列出工具")
    parser.add_argument("--schema", action="store_true", help="导出 LLM schema")
    parser.add_argument("--report", action="store_true", help="校准诊断报告")
    args = parser.parse_args()

    registry = create_default_registry()

    if args.register:
        name, desc = args.register
        registry.register(name=name, description=desc, schema={"type": "object", "properties": {}})
        print(f"✅ 注册工具: {name}")

    elif args.list is not None:
        tools = registry.list_tools()
        print(f"工具列表 ({len(tools)} 个):")
        for t in tools:
            print(f"  [{t['category']}] {t['name']}: {t['description']} (调用 {t['call_count']} 次, 成功率 {t['success_rate']:.0f}%)")

    elif args.schema:
        print(json.dumps(registry.to_schema(), ensure_ascii=False, indent=2))

    elif args.report:
        report = registry.calibration_report()
        print(f"总工具数: {report['total_tools']}")
        print(f"总调用数: {report['total_calls']}")
        print(f"整体成功率: {report['overall_success_rate']}%")
        print(f"\n按分类:")
        for cat, info in report["tools_by_category"].items():
            print(f"  {cat}: {info['count']} 个工具, {info['calls']} 次调用, {info['failures']} 次失败")
        if report["underutilized"]:
            print(f"\n未使用工具: {', '.join(report['underutilized'])}")
        if report["overused"]:
            print(f"高失败工具: {', '.join(report['overused'])}")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
