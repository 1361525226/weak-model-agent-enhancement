# 论文整合报告 v3.3

> 生成时间：2026-09-18
> 方法论来源：arXiv 搜索 + GitHub 趋势分析

## 一、关键论文发现（2025-2026）

### A. Agent Harness 安全与评估

| 论文 | 日期 | 核心贡献 | 本项目吸收方向 |
|-----|------|---------|--------------|
| **HarnessRisk** (arXiv 待查) | 2026-08-18 | 首个 Agent Harness 安全生命周期基准测试 | 安全漂移检测 + 护栏评估 |
| **Code as Agent Harness** | 2026-05-18 | 用代码定义 Harness 而非配置 | AGENTS.md → 可执行代码化 |
| **AutoHarness** | 2026-02-10 | 自动综合 Code Harness | Skill 自动生成 |
| **AgentDoG** | 2026-01-26 | 诊断性护栏框架（Agent Diagnostic Guardrail） | 诊断式 Loop 监控 |
| **PSG-Agent** | 2025-09-28 | 人格感知安全护栏 | Skill 个性化 |

### B. Agent 记忆系统

| 论文 | 日期 | 核心贡献 | 本项目吸收方向 |
|-----|------|---------|--------------|
| **Oracle Agent Memory** | 2026-07-14 | 企业级记忆基础架构，支持长期 Agent | 双层内存架构升级 |
| **Survey of Agent Memory** | 2026-01-14 | 面向自进化和长时程的记忆系统综述 | 记忆系统 v2 设计 |
| **MemSkill** (arXiv:2602.02474) | 2026-02-02 | Controller/Executor/Designer 三组件闭环 | skill-evolution Skill |
| **Carousel Memory** | 2021-03-18 | 轮转式情景记忆设计 | 记忆分层轮换策略 |

### C. 测试时计算（Test-Time Compute）

| 论文 | 日期 | 核心贡献 | 本项目吸收方向 |
|-----|------|---------|--------------|
| **Scaling Test-time Compute for LLM Agents** | 2025-06-15 | Agent 场景下测试时计算扩展定律 | Best-of-N/ToT/Forest 理论支撑 |
| **Sleep-time Compute** | 2025-04-17 | 推理时之外的计算机会（离线巩固） | SkillOpt-Sleep 模式 |
| **LoopCoder-v2** (arXiv:2606.18023) | 2026-06 | R=2 最优 + CLP并行 + G-SWA上下文复用 | loop-engineering v3.5 |

### D. 自进化 Agent 综述

| 论文 | 日期 | 核心贡献 | 本项目吸收方向 |
|-----|------|---------|--------------|
| **Survey of Self-Evolving Agents** (arXiv:2507.21046) | 2025-07-28 | What/When/How/Where 四维分类 | META_DOMAINS 元域划分 |
| **Self-Improvements in Modern Agentic Systems** | 2026-07-14 | 现代 Agent 系统自我改进全面调查 | Skill 进化路线 |
| **Adaptive Data Flywheel (MAPE)** | 2025-10-30 | MAPE 控制循环应用于 Agent 改进 | 七步进化循环强化 |
| **SEVerA** | 2026-03-26 | 验证型自进化 Agent 综合合成 | G7 七维审查理论支撑 |

### E. 长时程 Agent

| 论文 | 日期 | 核心贡献 | 本项目吸收方向 |
|-----|------|---------|--------------|
| **When Can Agents Safely Checkpoint/Fork/Restore/Merge?** | 2026-08-24 | 精确检查 Agent 安全恢复条件 | .loop/state.md 恢复协议 |
| **Crab** | 2026-04-30 | 语义感知 Agent 沙箱 Checkpoint/Restore | Durable Execution 强化 |

---

## 二、新增吸收方向

### 1. Harness 代码化（Code as Harness）
**来源**：Code as Agent Harness (2026-05-18)
**核心思想**：Harness 不应是配置文件，而应是可执行代码。
**落地**：
- AGENTS.md 中的规则 → 转换为 Python 校验函数
- 创建 `harness/code.py`：将 AGENTS.md 规则编译为可执行检查器

### 2. 诊断式护栏（Diagnostic Guardrails）
**来源**：AgentDoG (2026-01-26)
**核心思想**：护栏不仅是拦截，还要诊断和报告根因。
**落地**：
- harness-guardrails/SKILL.md 增加诊断报告输出
- 每次拦截记录：错误类型、根因推测、修复建议

### 3. 语义感知 Checkpoint
**来源**：Crab (2026-04-30) + Checkpoint 理论 (2026-08-24)
**核心思想**：Checkpoint 不是字节快照，而是语义快照——只保存有意义的状态变更。
**落地**：
- .loop/state.md 增加语义变更记录（semantic_diff）
- 恢复时只重建"有意义的状态"，丢弃中间过程

### 4. 离线巩固（Sleep-time Compute）
**来源**：Sleep-time Compute (2025-04-17)
**核心思想**：Agent 不活跃时的计算也是价值——用于技能巩固和模式发现。
**落地**：
- skill-evolution/SKILL.md 增加 Sleep 模式触发条件
- 每周自动运行 kb-consolidator 进行知识库整理

### 5. 安全生命周期（HarnessRisk）
**来源**：HarnessRisk (2026-08-18)
**核心思想**：Harness 安全需要全生命周期管理（设计→实现→验证→监控→退役）。
**落地**：
- AGENTS.md 增加安全生命周期检查清单
- 每次 Skill 发布后运行安全回归测试

---

## 三、下一步实施计划

### Week 1：Harness 代码化
- [ ] 编写 `harness/code.py`：将 AGENTS.md 规则编译为校验函数
- [ ] 编写 `harness/scorecard.py`：Harness 质量评分卡
- [ ] 运行基准测试：对比手动规则 vs 代码化规则

### Week 2：诊断式护栏
- [ ] 更新 harness-guardrails/SKILL.md：增加诊断报告输出
- [ ] 实现 AgentDoG 风格的诊断框架
- [ ] 集成到 loop-engineering 的验证阶段

### Week 3：语义 Checkpoint
- [ ] 重写 .loop/state.md：增加 semantic_diff 字段
- [ ] 实现 Crab 风格的语义快照
- [ ] 测试恢复正确性

### Week 4：离线巩固
- [ ] 更新 skill-evolution/SKILL.md：增加 Sleep 模式
- [ ] 实现每周自动 consolidation
- [ ] 运行第一个 Sleep 周期
