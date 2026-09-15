# 弱模型 Agent 性能增强方案 v3.0
## —— 7阶段工作流 × Best-of-N × Token换性能 × 持续进化

**版本**：3.0.0
**核心目标**：通过工程项目化手段，让弱模型在 Agent 驱动下的**表现性能**达到远超其单次生成能力的水平。
**关键洞察**：同模型在不同 Agent 平台上性能差异可达 15-22pp（Harness 质量决定上限）。我们不做模型增强，做**工程增强**。

---

## 一、核心理念

### 1.1 性能公式重新定义

```
表现性能 = f(弱模型能力, Harness质量, Context质量, Loop效率, 验证可靠性)
              ↑           ↑            ↑          ↑            ↑
            固定约束    可优化40%    可优化30%   可优化25%     可优化50%
```

**核心策略**：不改变模型本身，通过工程手段最大化 Harness、Context、Loop、验证四个维度的效率。

### 1.2 时间/Token 换性能的四种策略

| 策略 | 机制 | 适用场景 | 预期增益 |
|-----|------|---------|---------|
| **串行 Loop** | 生成→验证→修复（R=2最优） | 简单修复/代码生成 | +20-30% |
| **Best-of-N** | N个候选→验证→选优 | 中等复杂度任务 | +30-50% |
| **ToT 树搜索** | 多分支生成→评估→剪枝→深入 | 复杂决策/架构设计 | +40-60% |
| **Forest of Thought** | 多策略并行探索→注入洞察 | 极复杂任务/根因定位 | +50-70% |

### 1.3 跨平台性能差异来源

```
同一模型（agnes-2.5-flash）在不同平台的性能差异：

平台          Harness质量  Context管理  Loop效率  综合性能
──────────────────────────────────────────────────────
Aider         ★★★★★       ★★★★       ★★★★★    82%
LangGraph     ★★★★★       ★★★★       ★★★★     78%
OpenHands     ★★★★        ★★★        ★★★★     80%
DeerFlow      ★★★★★       ★★★★★      ★★★★     76%
Agnes Code    ★★★★        ★★★★       ★★★      75%
原生API       ★★          ★★         ★★       60%
```

**结论**：Harness 工程化是最大杠杆——同样一个弱模型，好的 Harness 可以让它表现提升 15-22pp。

---

## 二、7阶段工作流（完整闭环）

```
┌─────────────────────────────────────────────────────────────────────────┐
│  阶段    核心动作                         增强技术                      │
├─────────────────────────────────────────────────────────────────────────┤
│  1.需求   OpenSpec 锁定规格 + 人工确认                                  │
│          ├─ 产出：Spec.md（含验收条件）                                 │
│          └─ 增强：pattern_083 确定性工作流编排                          │
├─────────────────────────────────────────────────────────────────────────┤
│  2.设计   Agent 出草案 + Critic Agent 审查 + 人工单向门                 │
│          ├─ 产出：Design.md + Review.md                                 │
│          └─ 增强：pattern_052 辩论共识 + pattern_254 技能化审查         │
├─────────────────────────────────────────────────────────────────────────┤
│  3.实现   TDD 循环 + 小步提交 + Strict Verifier                        │
│          ├─ 产出：代码 + 测试 + git commit                              │
│          └─ 增强：pattern_062 Edit-Test-Commit + pattern_111 SWE-loop  │
├─────────────────────────────────────────────────────────────────────────┤
│  4.验证   Best-of-N 采样 → 测试筛选 → 失败回灌修复                      │
│          ├─ 产出：验证报告 + 修复记录                                   │
│          └─ 增强：pattern_064 ToT + pattern_073 Forest + R=2 最优      │
├─────────────────────────────────────────────────────────────────────────┤
│  5.审查   独立 Critic Agent 复审 → 检查测试盲区                         │
│          ├─ 产出：Code Review Report                                   │
│          └─ 增强：pattern_254 + pattern_139 CRITIC外部验证 + open-CR   │
├─────────────────────────────────────────────────────────────────────────┤
│  6.复盘   失败模式写入 Memory/Skill → 更新 Skill 库                    │
│          ├─ 产出：ERRORS.md + Skill 迭代                               │
│          └─ 增强：pattern_065 Reflexion + 闭环自进化 v3.3               │
├─────────────────────────────────────────────────────────────────────────┤
│  7.发布   小范围验证 → 扩散 → 关键改动人工确认                          │
│          └─ 增强：pattern_030 安全漂移检测 + pattern_089 Durable Exec   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、各阶段详细设计

### 阶段 1：需求 — OpenSpec 锁定规格

```markdown
## 输入
用户自然语言描述

## 处理
1. 解析为结构化 Spec：
   - 功能需求（what）
   - 约束条件（constraints）
   - 验收标准（acceptance criteria）
   - 非功能需求（性能/安全/兼容）

2. 生成 Spec.md：
   ```markdown
   ## Spec: [任务名称]
   
   ### 功能需求
   - [ ] 需求1
   - [ ] 需求2
   
   ### 约束
   - 文件大小 ≤ X
   - RPM 消耗 ≤ Y
   - 不能修改：...
   
   ### 验收标准
   - 命令1 返回码 0
   - 命令2 输出包含 "..."
   - 命令3 覆盖率 ≥ 80%
   
   ### 人工确认点
   - [ ] 关键设计决策
   - [ ] 风险评估
   ```

3. 人工确认（单向门）

## 输出
Spec.md（锁定需求，防止漂移）
```

**知识库模式**：pattern_083 确定性工作流编排、pattern_062 Edit-Test-Commit

---

### 阶段 2：设计 — Agent 草案 + Critic 审查

```markdown
## 输入
Spec.md

## 处理
1. Agent 生成 Design.md：
   - 架构选择 + 理由
   - 模块划分
   - 接口定义
   - 风险点识别

2. Critic Agent 审查（独立上下文）：
   - 用 open-code-review-delegate Skill
   - 检查：架构合理性、遗漏边界、安全风险
   - 输出：Review.md（含 Critical/High/Medium 问题）

3. 人工过单向门：
   - 确认 Critical 问题已解决
   - 确认 High 问题有处理方案
   - 批准进入实现阶段

## 输出
Design.md + Review.md + 人工签批
```

**知识库模式**：pattern_052 辩论共识、pattern_254 技能化代码审查、pattern_090 Supervisor-Worker

---

### 阶段 3：实现 — TDD 循环 + 小步提交

```markdown
## 输入
Design.md + Spec.md

## 处理
每个原子任务（单文件/单函数）：

  ┌─ 写测试 ──────────────────────────────┐
  │  先写失败的测试（红）                   │
  │  验收条件转化为可执行测试                │
  └──────────────┬────────────────────────┘
                 ↓
  ┌─ 实现代码 ────────────────────────────┐
  │  最小化实现（绿）                      │
  │  Strict Verifier 跑 Lint/Test/Build   │
  └──────────────┬────────────────────────┘
                 ↓
  ┌─ 验证 ────────────────────────────────┐
  │  全部通过 → commit 小 diff             │
  │  失败 → 错误回灌重试（最多 3 次）      │
  └──────────────┬────────────────────────┘
                 ↓
  ┌─ 记录 ────────────────────────────────┐
  │  成功 → SUCCESS_PATTERNS.jsonl        │
  │  失败 → ERRORS.md + reflexion积累     │
  └───────────────────────────────────────┘

## 输出
可工作的代码 + 测试 + git commit
```

**知识库模式**：pattern_062 Edit-Test-Commit、pattern_111 SWE-agent 自主修复、pattern_451 OpenHands 自修复

---

### 阶段 4：验证 — Best-of-N + 失败回灌

```markdown
## 输入
实现代码 + 测试套件

## 处理
### 策略选择（根据任务复杂度）

简单任务（R=2）：
  生成 → 验证 → 失败回灌 → 再验证（最多2轮）

中等任务（Best-of-3）：
  并行生成 3 个候选 → 各自运行测试 → 选通过率最高的
  → 失败的回灌修复 → 第二轮 Best-of-3

复杂任务（ToT/K=3）：
  思维分解 → 每层生成 3 候选 → 评估打分 → 剪枝 → 最优路径深入

极复杂任务（Forest/K=5）：
  5 种策略并行探索 → 自适应注入洞察 → 剪枝融合

### 四维诊断信号（监控循环健康度）
  ① 收敛信号：验证通过率是否已收敛？
  ② 方案多样性：是否有新修复角度？
  ③ 振荡信号：通过率是否增减交替？
  ④ 分布偏移：diff 是否有意义变化？

### 早停条件（任一命中）
  - 无进展计数 ≥ 2
  - 当前轮次 ≥ 3 且改进幅度 < 10%
  - 信号③振荡 或 信号④停止

## 输出
验证报告 + 最佳候选 + 失败记录
```

**知识库模式**：pattern_064 ToT 树搜索、pattern_073 Forest of Thought、pattern_251 Loop Engineering

---

### 阶段 5：审查 — Critic Agent 复审

```markdown
## 输入
最终代码 + 测试 + git diff

## 处理
### 使用 open-code-review-delegate Skill
  Step 1: ocr delegate preview → 确定审查范围
  Step 2: ocr delegate rule → 获取审查规则
  Step 3: git diff → 获取变更内容
  Step 4: Agent 执行审查（用自己的判断力）
  Step 5: 结构化输出（path/content/line/category/severity）
  Step 6: 按严重度分组报告

### CRITIC 外部验证层（pattern_139）
  - 代码执行验证：运行测试和 lint
  - 路径验证：检查引用的文件是否存在
  - 引用验证：WebFetch 验证链接
  - 一致性验证：git diff 检查版本

### 盲区检查
  - 测试覆盖不到的边界条件
  - 安全漏洞（注入/越权/泄露）
  - 性能问题（N+1查询/内存泄漏）
  - 可维护性问题（耦合/复杂度）

## 输出
Code Review Report（Critical/High/Medium/Low 分级）
```

**知识库模式**：pattern_139 CRITIC 外部验证、pattern_254 技能化代码审查

---

### 阶段 6：复盘 — 失败模式自动积累

```markdown
## 输入
本轮所有成功/失败记录

## 处理
### Reflexion 反思（pattern_065）
  对每个失败：
  1. 错误分类（syntax/type/logic/import/config）
  2. 根因分析（生成自然语言反思）
  3. 记忆注入（反思作为经验写入下一轮）

### 失败模式积累（reflexion_accumulator.py）
  python reflexion_accumulator.py \
    --task "任务描述" \
    --error "错误信息" \
    --fix-attempt "已尝试的修复"

### 模式库更新
  - 高频错误 → 抽象为 Skill 规则
  - 新发现 → 追加到 ERRORS.md
  - 成功策略 → 追加到 SUCCESS_PATTERNS.md

### Skill 进化触发（pattern_167 GEPA）
  同类失败 ≥ 3 次 → 触发 /evolve
  → G1-G7 门控检查
  → CRITIC 外部验证
  → 写入 skills/<category>/SKILL.md
```

**知识库模式**：pattern_065 Reflexion、pattern_167 DSPy GEPA

---

### 阶段 7：发布 — 小范围验证后扩散

```markdown
## 输入
通过审查的代码

## 处理
1. 金丝雀发布：先在测试环境/小范围验证
2. 安全漂移检测（pattern_030）：
   - 检查新版本与旧版本的行为差异
   - 确认没有引入安全退化
3. 人工确认关键改动
4. 全量发布
5. 监控：后续 N 次使用中的表现

## 输出
已发布的代码 + 发布报告
```

**知识库模式**：pattern_030 安全漂移检测、pattern_089 Durable Execution

---

## 四、Token 预算动态分配

### 4.1 任务分级与预算

| 级别 | 描述 | Thinking预算 | 最大Token消耗 | 最大轮次 | 升级阈值 |
|-----|------|------------|-------------|---------|---------|
| **S** | 读文件/写小函数/问答 | 关闭 | 1,000 | 1 | 无 |
| **A** | 单模块功能 | 512 | 3,000 | 3 | 2次失败 |
| **B** | 多模块联动 | 1024 | 8,000 | 5 | 3次失败 |
| **C** | 架构设计/复杂推理 | 2048 | 20,000 | 8 | 立即升级 |
| **X** | 高风险操作 | 4096 | 5,000 | 1 | 人工确认 |

### 4.2 以 Token 换性能的决策树

```
任务复杂度评估
  │
  ├─ S级（简单）
  │   └─ Thinking=关闭, R=1, Best-of-1
  │
  ├─ A级（中等）
  │   ├─ Thinking=512, R=2, Best-of-2
  │   └─ 失败 → Thinking=1024, R=3
  │
  ├─ B级（复杂）
  │   ├─ Thinking=1024, R=3, Best-of-3
  │   ├─ 失败 → ToT K=3
  │   └─ 仍失败 → Forest K=5
  │
  └─ C级（极复杂）
      ├─ Thinking=2048, ToT K=3
      ├─ Forest K=5
      └─ 仍失败 → 升级人工
```

### 4.3 RPM 预算控制

```
每日预算：~6,000 次调用（20 RPM × 8h × 60min × 0.8系数）

分配：
  S级任务（40%）：2,400 次 → 800 个简单任务
  A级任务（35%）：2,100 次 → 260 个中等任务
  B级任务（20%）：1,200 次 → 80 个复杂任务
  X级任务（5%）：300 次 → 60 个高风险任务
  预留缓冲：10%
```

---

## 五、知识库模式映射表

| 工作流阶段 | 核心模式 | 来源 | Stars |
|-----------|---------|------|-------|
| 需求 | pattern_083 确定性工作流编排 | google/adk-python | 15K |
| 需求 | pattern_062 Edit-Test-Commit | Aider | 32.5K |
| 设计 | pattern_052 辩论共识 | TauricResearch | 88K |
| 设计 | pattern_254 技能化代码审查 | GitHub Copilot | N/A |
| 设计 | pattern_090 Supervisor-Worker | DeerFlow | 25K |
| 实现 | pattern_111 SWE-agent 自主修复 | SWE-agent | 16K |
| 实现 | pattern_451 OpenHands 自修复 | OpenHands | 75K |
| 实现 | pattern_062 Edit-Test-Commit | Aider | 32.5K |
| 验证 | pattern_064 ToT 树搜索 | Princeton | 6K |
| 验证 | pattern_073 Forest of Thought | ICML 2025 | 55 |
| 验证 | pattern_251 Loop Engineering | Loop Engineering | N/A |
| 验证 | pattern_139 CRITIC 外部验证 | Microsoft | N/A |
| 审查 | pattern_254 技能化代码审查 | Copilot Skills | N/A |
| 审查 | pattern_029 护栏模式 | guardrails-ai | 4.2K |
| 复盘 | pattern_065 Reflexion 反思 | Reflexion | 3.2K |
| 复盘 | pattern_167 DSPy GEPA | Stanford | 36.5K |
| 复盘 | pattern_463 工具调用重试回灌 | pydantic-ai | 13K |
| 发布 | pattern_030 安全漂移检测 | Agent安全研究 | N/A |
| 发布 | pattern_089 Durable Execution | LangGraph | 97K |

---

## 六、实施路线图

### Week 1：基础框架
- [ ] 创建 workflow-engine.py（7阶段编排器）
- [ ] 集成 open-code-review-delegate 到审查阶段
- [ ] 实现 Best-of-N 采样器
- [ ] 实现 ToT/Forest 并行探索器

### Week 2：验证与反馈
- [ ] 集成 reflexion_accumulator.py 到复盘阶段
- [ ] 实现四维诊断信号监控
- [ ] 实现动态 Token 预算分配器
- [ ] 建立基准测试套件（对比不同策略的性能）

### Week 3：进化与优化
- [ ] 实现 Skill 自动进化触发器
- [ ] 建立性能追踪仪表板
- [ ] 月度复盘：评估各阶段增益
- [ ] 季度迭代：吸收新的知识库模式

---

## 七、关键指标

| 指标 | 基线 | 目标（3个月后） |
|-----|------|---------------|
| 单任务一次通过率 | 60% | 80% |
| Loop 平均迭代次数 | 3.5 | 2.0 |
| 验证失败修复率 | 50% | 85% |
| RPM 消耗/任务 | 8 | 5 |
| Skill 进化轮次/月 | 0 | 2-3 |
| 人工介入率 | 30% | 10% |
