# SKILL Index — 模式索引与分类

## 按类别分类

### 🔁 Loop 循环类（3 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_251 | Loop Engineering 声明式循环 | Boris Cherny | N/A | 通用迭代任务 |
| pattern_062 | Edit-Test-Commit 原子闭环 | Aider | 32.5K | 代码修改任务 |
| pattern_111 | SWE-agent 自主修复循环 | Princeton | 16K | Bug 修复 |

**Skill 文件**：`skills/loop-engineering/SKILL.md`

---

### 🧠 上下文工程类（3 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_018 | 上下文工程技能化 | addyosmani/agent-skills | 73K | 上下文打包 |
| pattern_456 | 仓库地图 Token 预算 | Aider | 47.8K | 大项目上下文管理 |
| pattern_460 | LLMLingua Prompt 压缩 | Microsoft | 6.5K | 超长 prompt 压缩 |

**Skill 文件**：`skills/context-engineering/SKILL.md`

---

### 🛡️ 护栏验证类（2 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_029 | 护栏模式 | guardrails-ai | 4.2K | 输入输出安全 |
| pattern_033 | 可插拔 Agent 框架 | earendil-works/pi | 60K | 模块化架构 |

**Skill 文件**：`skills/harness-guardrails/SKILL.md`

---

### 💾 记忆系统类（3 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_237 | 记忆提取-更新-遗忘循环 | mem0ai/mem0 | 57K | 跨会话记忆 |
| pattern_238 | OS 风格虚拟上下文分页 | letta-ai/letta | N/A | 超长对话 |
| pattern_239 | 时序知识图谱记忆 | getzep/zep | N/A | 实体关系检索 |

**Skill 文件**：`skills/memory-system/SKILL.md`

---

### 👁️ 代码审查类（1 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_254 | 技能化代码审查 | GitHub Copilot | N/A | 团队规范审查 |

**Skill 文件**：`skills/code-review/SKILL.md`

---

### 🐛 调试修复类（3 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_065 | 语言反思自我纠错 | noahshinn/reflexion | 3.2K | 迭代式自我改进 |
| pattern_111 | Agent 自主修复循环 | SWE-agent | 16K | Bug 自动修复 |
| pattern_451 | OpenHands 自修复代码循环 | All-Hands-AI | 75K | 完整修复 pipeline |

**Skill 文件**：`skills/debugging/SKILL.md`

---

### 🏗️ 全栈开发类（2 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_070 | 主模型+小模型分工架构 | simular-ai/Agent-S | 11.7K | Planner-Grounder |
| pattern_083 | 确定性工作流编排 | google/adk-python | 15K | 结构化任务执行 |

**Skill 文件**：`skills/fullstack-dev/SKILL.md`

---

### 🤖 多 Agent 协作类（3 个核心模式）

| Pattern ID | 名称 | 来源 | Stars | 适用场景 |
|-----------|------|------|-------|---------|
| pattern_052 | 辩论式共识机制 | TauricResearch | 88K | 多视角决策 |
| pattern_090 | Supervisor-Worker 双层分工 | bytedance/DeerFlow | 25K | 规划+执行分离 |
| pattern_091 | Agent Handoff 优雅移交 | openai/openai-agents | 28K | 能力边界升级 |

**Skill 文件**：`skills/multi-agent/SKILL.md`

---

## 按平台适用性

| Skill | Agnes | Aider | LangGraph | OpenHands | DeerFlow |
|-------|:-----:|:-----:|:---------:|:---------:|:--------:|
| loop-engineering | ✅ | ✅ | ✅ | ✅ | ✅ |
| context-engineering | ✅ | ✅ | ✅ | ✅ | ✅ |
| harness-guardrails | ✅ | ✅ | ✅ | ✅ | ✅ |
| memory-system | ✅ | ✅ | ✅ | ✅ | ✅ |
| code-review | ✅ | ✅ | ✅ | ✅ | ✅ |
| debugging | ✅ | ✅ | ✅ | ✅ | ✅ |
| fullstack-dev | ✅ | ✅ | ✅ | ✅ | ✅ |
| multi-agent | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 按 RPM 敏感度

| Skill | RPM 消耗 | 优化建议 |
|-------|---------|---------|
| loop-engineering | 中（每轮 1 次调用） | 设 max_iterations=3 |
| context-engineering | 低（一次性打包） | 会话级复用 |
| harness-guardrails | 低（本地校验） | 无需 API 调用 |
| memory-system | 低（文件系统读写） | 批量检索 |
| code-review | 中（每次提交 1 次） | 增量审查 |
| debugging | 高（循环重试） | 模式库加速 |
| fullstack-dev | 高（多步骤） | 分层递进 |
| multi-agent | 高（并行调用） | 串行降级 |

---

## 进化追踪

每个 Skill 的失败模式记录在：
- `ERRORS.md`（全局）
- 各 Skill 目录下的 `FAILED_CASES.md`（局部）

成功模式记录在：
- `SUCCESS_PATTERNS.md`（全局）
- 各 Skill 目录下的 `SUCCESS_CASES.md`（局部）
