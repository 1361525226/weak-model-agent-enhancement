# HANDOFF.md — 跨会话进化交接包

> 生成时间：2026-09-18
> 目的：当当前会话 token 耗尽时，Agnes 可从此文件接手继续进化项目

---

## 当前状态快照

```
项目：weak-model-agent-enhancement
版本：v3.2.0
工作流：7阶段（需求→设计→实现→验证→审查→复盘→发布）
核心引擎：loop-engineering v3.5 + 闭环自进化学习 v3.3 + open-code-review-delegate
知识库：494 个原始模式 → 392 个元模式（21% 压缩，threshold=0.25）
Skill 数量：9 个（含 skill-evolution）
RPM 限制：~20
Thinking：已开启（default=high，budget=2048 tokens）
```

## 已完成工作（本轮）

### 交叉进化调研（已完成）
- [x] 分析 [loopx](https://github.com/huangruiteng/loopx) — 状态内核+控制平面
- [x] 分析 [arXiv:2507.21046](https://arxiv.org/abs/2507.21046) 自进化Agent综述 — What/When/How/Where 四维分类
- [x] 分析 [MemSkill arXiv:2602.02474](https://arxiv.org/abs/2602.02474) — Controller/Executor/Designer 三组件闭环
- [x] 分析 [Awesome-Self-Evolving-Agents](https://github.com/XMUDeepLIT/Awesome-Self-Evolving-Agents) — 资源索引

### 知识库整合（已完成）
- [x] 编写 kb-consolidator.py（可重复运行）
- [x] 494 模式 → 392 元模式，合并 58 组
- [x] 输出 docs/kb-consolidated.md + docs/kb-meta-index.json

### 最大合并组（TOP5）
| 合并数 | 元模式名称 | 来源 IDs |
|-------|-----------|---------|
| 8x | AI Agent设计原理书体系化 | pattern_256, 172, 356, 191, 039... |
| 7x | LangChain 长上下文RAG增强 | pattern_418, 431, 429, 450, 443... |
| 6x | Agent Compiler 综合 | pattern_395, 399, 084, 111, 076... |
| 6x | RadixAttention前缀缓存 | pattern_161, 405, 406, 408, 234... |
| 6x | Consumer GPU推理加速 | pattern_347, 282, 302, 370, 420... |

## 下一步建议（按优先级）

### P0：验证与文档
1. 运行 `scripts/verify-project.py` 确认项目完整性
2. 将 kb-consolidated.md 上传到「心墟的知识库」
3. 更新 AGENTS.md 版本号到 v3.2

### P1：Skill 进化
4. 根据整合结果，合并 agens-agent-patterns 中重复的 Skill
5. 将高价值合并组（≥4x）抽象为新的 composite Skill
6. 运行 `scripts/workflow-engine.py "生成合并后的Skill文档"` 验证

### P2：性能基准
7. 在 Agnes/Aider/LangGraph 上运行同一任务集，对比性能差异
8. 记录基准结果到 `docs/benchmark-results.md`
9. 将最佳实践沉淀到对应 Skill 中

### P3：长期进化
10. 设置 cron 定期运行 kb-consolidator（每周一次）
11. 建立性能追踪仪表板（每轮 Loop 记录关键指标）
12. 月度复盘：评估各阶段增益，调整 threshold 参数

## 关键文件索引

| 文件 | 用途 |
|-----|------|
| `AGENTS.md` | 主规则文件（7阶段工作流） |
| `project_config.json` | 项目配置（RPM/循环/Token预算） |
| `scripts/kb-consolidator.py` | 知识库整合工具 |
| `scripts/workflow-engine.py` | 7阶段编排器 |
| `scripts/verify-project.py` | 项目完整性验证 |
| `context-kernel.py` | 上下文投影 |
| `reflexion_accumulator.py` | 失败模式积累 |
| `docs/kb-consolidated.md` | 整合版知识库 |
| `docs/kb-meta-index.json` | 机器可读索引 |
| `skills/*/SKILL.md` | 9个Skill |
| `.loop/state.md` | 当前Loop状态 |
| `.learnings/session-state.md` | 会话状态 |

## Agnes 执行指令（token 耗尽后恢复）

```bash
# 1. 恢复项目（如需要）
git clone https://github.com/1361525226/weak-model-agent-enhancement.git
cd weak-model-agent-enhancement

# 2. 检查状态
D:/hermes/hermes-agent/venv/Scripts/python.exe scripts/verify-project.py

# 3. 继续 P0 任务
# （按 HANDOFF.md 中的优先级列表顺序执行）

# 4. 每次完成后更新本文件
# 在"已完成工作"部分追加，在"下一步建议"中移除已完成项
```

## 交叉进化方法论备忘

**What-to-evolve 四维分类**（arXiv:2507.21046）：
- What：模型/记忆/工具/架构
- When：测试时内/测试时间
- How：标量奖励/文本反馈/单多Agent
- Where：应用领域

**MemSkill 三组件闭环**：
- Controller：选技能（从轨迹中提取）
- Executor：执行（LLM生成）
- Designer：审查hard case（进化技能集）

**当前项目映射**：
- Controller → loop-engineering（A8 增益-成本预估）
- Executor → 各 Skill 的实现
- Designer → skill-evolution（G1-G7 门控 + CRITIC 验证）
