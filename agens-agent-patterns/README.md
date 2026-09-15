# agens-agent-patterns — 弱模型 Agent 增强 Skill 标准库

> **版本**：v1.0.0
> **定位**：环境无关的弱模型 Agent 增强模式库，适用于 Agnes、Agno、LangGraph、Aider、OpenHands、DeerFlow 等任意平台。
> **来源**：从 Trae Work 弱模型增强知识库（484+34 个开源模式）中提取、适配、进化。

---

## 目录结构

```
agens-agent-patterns/
├── README.md                 # 本文件
├── SKILL_INDEX.md            # 模式索引
└── skills/
    ├── loop-engineering/     # Loop 循环模式（pattern_251, pattern_062）
    │   └── SKILL.md
    ├── context-engineering/  # 上下文工程模式（pattern_018, pattern_456, pattern_460）
    │   └── SKILL.md
    ├── harness-guardrails/   # 护栏验证模式（pattern_029, pattern_033）
    │   └── SKILL.md
    ├── memory-system/        # 记忆系统模式（pattern_237, pattern_238, pattern_239）
    │   └── SKILL.md
    ├── code-review/          # 代码审查模式（pattern_254）
    │   └── SKILL.md
    ├── debugging/            # 调试修复模式（pattern_065, pattern_111, pattern_451）
    │   └── SKILL.md
    ├── fullstack-dev/        # 全栈开发模式（pattern_070, pattern_083）
    │   └── SKILL.md
    └── multi-agent/          # 多 Agent 协作模式（pattern_052, pattern_090, pattern_091）
        └── SKILL.md
```

---

## 设计原则

1. **环境无关**：每个 Skill 标明在 Agnes/Aider/LangGraph/OpenHands/DeerFlow 中的对应实现
2. **可执行**：每个 Skill 包含具体步骤、模板代码、验证标准
3. **可进化**：失败模式写入 ERRORS.md，成功模式写入 SUCCESS_PATTERNS.md
4. **低 RPM 友好**：串行优先，避免并行采样消耗额度

---

## 使用方式

### Agnes Code
```bash
# 将 skills 目录复制到 Agnes Skill 路径
cp -r agens-agent-patterns/skills ~/.zcode/skills/

# 或使用 agnes-sync 同步
agnes-sync pull agens-agent-patterns
```

### Aider
```bash
# 将 skills 复制到 .aider.skills/
mkdir -p .aider.skills
cp -r agens-agent-patterns/skills/* .aider.skills/
```

### LangGraph
```python
# 将 Skill 实现为节点
from skills.loop_engineering import LoopNode
from skills.context_engineering import ContextNode

graph.add_node("loop", LoopNode().execute)
graph.add_node("context", ContextNode().execute)
```

---

## 模式来源索引

| Skill | 对应 Trae 知识库 Pattern ID | 来源项目 | Stars |
|-------|---------------------------|---------|-------|
| loop-engineering | pattern_251, pattern_062 | Loop Engineering, Aider | N/A, 32.5K |
| context-engineering | pattern_018, pattern_456, pattern_460 | agent-skills, Aider, LLMLingua | 73K, 47.8K, 6.5K |
| harness-guardrails | pattern_029, pattern_033 | guardrails-ai, pi | 4.2K, 60K |
| memory-system | pattern_237, pattern_238, pattern_239 | mem0, Letta, Zep | 57K, N/A, N/A |
| code-review | pattern_254 | GitHub Copilot Skills | N/A |
| debugging | pattern_065, pattern_111, pattern_451 | Reflexion, SWE-agent, OpenHands | 3.2K, 16K, 75K |
| fullstack-dev | pattern_070, pattern_083 | Agent-S, Google ADK | 11.7K, 15K |
| multi-agent | pattern_052, pattern_090, pattern_091 | TradingAgents, DeerFlow, OpenAI Agents | 88K, 25K, 28K |

---

## 进化日志

- **v1.0.0**（2026-09-15）：初始版本，从 Trae 知识库提取 8 个核心 Skill，适配多平台
