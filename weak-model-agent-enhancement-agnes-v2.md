# 弱模型 Agent 性能增强完整方案
## ——以免费 Agnes-2.5-Flash 实现全栈开发能力为例（知识库版）

**版本**：2.0
**适用对象**：使用免费 Agnes-2.5-Flash、希望通过外挂工具、工程流程、Loop 循环和上下文优化提升编码能力的开发者。
**与 Trae Work 方案的差异**：Agnes 有统一的 Agnes Code 桌面端、内置 Skill/MCP/Thinking 三层扩展体系，以及 20 RPM 的硬性限制；Trae Work 方案侧重纯 API 调用，本文将其全部映射到 Agnes 可用工具。
**免责声明**：文中涉及的工具、模型、RPM 限制和社区案例，请以官方最新说明为准。多账号聚合可能违反服务条款，存在封禁风险。

---

## 摘要

理论上，弱模型可以通过外挂数据库、工具、记忆、规划器、验证器等方式显著提升性能。但外挂增强的是"信息、记忆、执行和验证"，不是自动增强"推理、规划和泛化"。对于免费 Agnes，目标不是把它"教"成强模型，而是为它搭建一套工程化工作台：用流程约束守住底线，用 Skill/MCP/Thinking 扩展能力上限，用 Loop 以时间换性能，用 Context Engineering 节省 Token 并投入推理。最终，在可验证、可分解、可迭代的全栈开发任务上，免费 Agnes 可以接近远超其单次生成能力的工程质量。

---

## 1. 问题定义与目标

**目标**：使用免费 Agnes，在全栈开发中具备较强编码能力，满足日常开发需求。

**约束**：
- 免费，约 20 RPM（公开 30，实际可执行约 20）
- 弱模型推理能力有限（对比 GLM-5.2 744B MoE）
- 上下文窗口有限（弱模型默认 4K，需分块/RAG 补偿）
- Token 成本敏感，需精打细算

**核心策略**：

1. **外挂可外化的能力**：知识（Skill）、记忆（Memory/Skill）、计算（MCP）、工具（MCP）、验证（Loop + 测试）
2. **用大厂流程约束 Agent 行为**：OpenSpec / Agent Boost Kit / Strict Verifier
3. **用 Loop 以时间换性能**：串行生成→验证→修复循环
4. **用 Prompt / Context / Harness / Loop 四层工程协同**
5. **节省 Token，把省下的预算投入推理**
6. **在 20 RPM 下做极致优化**，不冒险聚合账号

---

## 2. 理论基础：弱模型 + 外挂能否提升

### 2.1 能，但有条件

外挂可以让弱模型 agent 在特定任务上显著变强，但增强的是信息、记忆和工具执行，不是自动增强推理、规划和泛化。

> **一句话**：弱模型 + 数据库可以变成更强的 agent，但不等于强模型。

### 2.2 外挂类别与 Agnes 映射

| 外挂类型 | 作用 | Agnes 映射 | 适合任务 |
|---------|------|-----------|---------|
| 数据库 / RAG / 知识库 | 弥补事实知识不足 | 微信知识库（ima-skill）+ Skill 库 | 问答、客服、检索 |
| 长期记忆 / 向量库 / 文件系统 | 保持一致性、跨会话状态 | `~/.agents/skills/` + MEMORY.md + agens 项目 memory/ | 长对话、多步任务 |
| 计算器 / Python / SQL / 编译器 | 精确计算与执行 | MCP 文件系统 + Bash 工具 + Python 执行 | 数学、代码、查询 |
| 规划器 / A* / MCTS / PDDL | 外部搜索可行路径 | Thinking 模式 + AGENTS.md 任务拆解 | 调度、路径、组合优化 |
| 验证器 / 测试 / 类型检查 / 形式验证 | 抑制错误累积 | Strict Verifier + Lint + Test + Build | 代码、逻辑、配置 |
| 强模型 API / 专家模型 / 投票路由 | 直接借用强智能 | Confidence Router（低置信→升级） | 复杂推理、架构设计 |
| 环境 / 模拟器 / 人类反馈 | 试错改进 | Agent Loop（生成→验证→诊断→修复） | RL、A/B、交互任务 |
| 元认知脚手架 | 反思、辩论、任务分解 | Reflexion 模式 + 失败模式写入 SKILL.md | 有限提升，需配合验证 |

### 2.3 性能约束公式

```
P(成功) ≤ P(信息在库中) × P(查询正确) × P(检索相关) × P(弱模型能整合) × P(验证正确)
```

任何一项趋近 0，整体提升就有限。对 Agnes 而言：

- **信息在库中**：Skill / Knowledge Base 覆盖率
- **查询正确**：Prompt Engineering 质量
- **检索相关**：Context Engineering（路径完整度、截断策略）
- **弱模型能整合**：Thinking 模式 Token 预算
- **验证正确**：测试/Lint/Build 的严格程度

### 2.4 理论边界

- 只读知识库类似查表，不自动增加图灵计算能力
- 可读写、可寻址、可循环的外部存储，理论上可让弱模型控制器模拟图灵机，但实际错误会累积
- 外挂不能超过外挂组件本身的能力
- 最有效的外挂其实是另一个强智能体（如 Supervisor），但那已接近换模型

---

## 3. 总体架构：三层协同（Agnes 专属）

### 第一层：Agnes Code 作为统一执行环境

Agnes Code 是官方桌面端 AI 编码代理，内置免费 Agnes-2.5-Flash，登录即可使用。它整合模型、Skill、MCP 和本地项目管理，是承载所有外挂组件的底座。

**关键工具**：
- `Skill` 工具：调用 `.zcode/skills/` 下的技能（如 `document-skills:docx`、`browser-use:control-browser`）
- `Bash` 工具：执行 shell 命令、运行脚本
- `Read` / `Write` / `Edit` 工具：文件操作
- `Agent` 工具：子 Agent 并行/异步任务

### 第二层：流程约束层

| 大厂实践 | Agnes 映射 | 作用 |
|---------|-----------|------|
| RFC / 设计文档先行 | OpenSpec：Proposal → Spec → Design → Tasks | 锁定需求，防止漂移 |
| 代码审查 | 独立 Critic Agent（换角色复审） | 捕获单模型盲区 |
| 小步提交 | 强制小 diff、原子任务 | 降低单次错误影响 |
| 测试金字塔 | Strict Verifier + 单元/集成测试 | 客观验证，不靠自评 |
| CI/CD | 每次改动自动跑 Lint/Test/Build | 阻断错误累积 |
| 金丝雀发布 | 先改小模块，验证后再扩散 | 限制爆炸半径 |
| 事后复盘 | Memory + Skill 记录失败模式 | 避免重复踩坑 |
| 结对编程 | Driver / Navigator 双 Agent | 一人写一人查 |
| 单向门 / 双向门 | 高风险改动人工确认 | 关键节点人工兜底 |

### 第三层：能力扩展层

#### Skill — 注入知识

将全栈开发最佳实践写成 `SKILL.md`，放入 `~/.agents/skills/`（或 ZCode 已配置的 skills 目录），让 Agnes 按标准执行。

**已有 Skill 示例**（ZCode 已安装）：
- `document-skills:docx` — DOCX 文档创建/编辑
- `document-skills:pdf` — PDF 处理
- `document-skills:pptx` — PPT 创建
- `document-skills:xlsx` — Excel 处理
- `browser-use:control-browser` — 浏览器自动化
- `ima-skill` — 微信知识库操作

**新建全栈开发 Skill 路径**：
```
~/.zcode/skills/fullstack-dev/SKILL.md
~/.zcode/skills/frontend-boundary/SKILL.md
~/.zcode/skills/backend-api/SKILL.md
~/.zcode/skills/db-security/SKILL.md
```

可用 `agnes-sync` 管理可移植 Skill。

#### MCP — 连接工具

通过 `agnes mcp sync` 把 `agents/mcp.json` 中的工具配置投射到 Agnes 的 MCP 目标路径。可接入：
- 文件系统 MCP 服务器
- 数据库查询 MCP 服务器
- Git MCP 服务器
- API 调用 MCP 服务器

#### Thinking 模式 — 激发推理

编码任务**务必开启 Thinking**：

```json
// OpenAI 兼容格式
{
  "chat_template_kwargs": {
    "enable_thinking": true
  }
}

// Anthropic 兼容格式
{
  "thinking": {
    "type": "enabled",
    "budget_tokens": 2048
  }
}
```

2048 是常见编码任务起步值，复杂调试可适当提高至 4096。

---

## 4. 四层工程：Prompt / Context / Harness / Loop

| 层级 | 解决的问题 | 对 Agnes 的作用 |
|-----|-----------|----------------|
| **Prompt Engineering** | 怎么问 | 角色设定、格式约束、Few-shot，让单次调用更准 |
| **Context Engineering** | 给它看什么 | 高信号、低噪声，决定上下文窗口内容 |
| **Harness Engineering** | 在什么环境干活 | 沙箱、权限、验证机制，安全边界内可靠执行 |
| **Loop Engineering** | 如何持续行动并收敛 | 自动触发、执行、验证、修正，直到完成 |

**四者协同**：Prompt 定基调，Context 控信息，Harness 守底线，Loop 推动收敛。

---

## 5. Loop 工程：用时间换性能

### 5.1 数学基础

若单次尝试正确概率为 `p`，验证器可靠，则 N 次独立尝试中至少一次正确的概率：

```
P_N = 1 - (1-p)^N
```

当 `N → ∞`，`P_N → 1`。这就是"以时间换性能"的数学基础。

### 5.2 可落地 Loop 形式（Agnes 适配）

| Loop 形式 | 描述 | Agnes 落地方式 |
|----------|------|---------------|
| **Best-of-N + 验证器选择** | 生成 N 个候选，用测试/Lint 筛出通过的 | 20 RPM 下串行 Best-of-N（非并行） |
| **生成 → 测试 → 诊断 → 修复** | 失败后错误信息回灌，循环直到通过或超预算 | Agnes Agent Loop（`Agent` 工具 run_in_background） |
| **TDD 循环** | 先写测试，再写实现，测试即规格 | Agnes 按 SKILL.md 顺序执行 |
| **多 Agent 对抗** | 一个写，一个找漏洞，一个裁决 | `Agent` 工具多子 Agent 并行 |
| **分层递进** | 接口→骨架→实现→优化，每层验证后进下一层 | AGENTS.md 分阶段约束 |
| **经验积累** | 成功轨迹和失败模式存入 Memory/Skill | Skill 库迭代更新 |

### 5.3 关键约束

- 验证器质量决定上限
- 反馈必须可理解（具体错误信息，而非模糊描述）
- 采样多样性会退化（多次重试模式趋同）
- 收益递减（N 越大边际收益越低）
- 不可验证任务失效（架构设计、UX 不能靠 Loop 兜底）
- 时间成本需设预算上限（最大迭代次数）

---

## 6. 节省 Token 策略：Context Engineering 战术

**核心原则**：高信号、低噪声。上下文塞满低信号 Token 会导致 context rot，回答变慢且更不准。

| 技巧 | 做法 | Agnes 适用场景 |
|-----|------|--------------|
| **字节上限截断** | `head -c 4000` 或 `tail -c 4000` | 单条规则可降约 50% Token |
| **引用文件带完整路径** | `@src/config/config.go` | 省去搜索链路，项目越大收益越高 |
| **意图一次说完** | 目标、文件、期望、验收条件一次写清 | 减少来回确认轮次 |
| **会话隔离** | `/new` 切断无关历史，`/compact` 避免历史污染 | 长会话必备 |
| **输出格式约束** | "只返回代码，不解释"、"用表格输出" | 减少废话输出 |
| **模型路由** | 简单任务 Flash，复杂任务 Thinking | 节省额度 |
| **上下文投影** | context-kernel 等工具按任务投影 | 社区案例减 79% Token |
| **输入优化** | context-guru 等工具精简提示词 | 社区案例减 65% 输入 Token |
| **LLMLingua 压缩** | 用免费小模型按 perplexity 逐 token 评估，删冗余 | 最高 20x 压缩，性能损失极小 |

**省 Token 不是目的**，而是为了把有限上下文预算花在刀刃上，让更多 Token 留给推理。

---

## 7. 以推理换性能：Token 预算与 Test-Time Compute

### 7.1 理论依据

推理时计算缩放定律指出，推理阶段投入更多计算，能显著提升复杂任务表现。研究显示：
- 1B 参数模型在数学推理上可击败 405B 巨型模型
- 0.5B 模型也能胜过 GPT-4o
- 但盲目增加 Token 并非总是有效，过多思考可能导致过度思考

### 7.2 Agnes 免费层 RPM 限制

| 用户类型 | 公开 RPM | 实际可执行 RPM |
|---------|---------|--------------|
| 免费用户 | 30 | **20** |
| 企业用户 | 60 | 40 |
| Token Plan 订阅 | 1000 | 1000 |

20 RPM 意味着 Loop 和并行采样受严重制约，每次 API 调用都需精打细算。

### 7.3 针对 Agnes 的实践策略

1. **动态分配推理预算**：简单任务快速响应，复杂任务才开 Thinking 并分配更多 Token
2. **优化验证器**：验证器是瓶颈，不是模型。清晰测试报错让每次重试更有价值
3. **串行 Best-of-N**：RPM 允许时 Best-of-N；弱模型在 SWE-bench 覆盖率可从 15.9% 提升至 56%
4. **级联路由**：Agnes 先试，失败或复杂才升级（Confidence Router）
5. **预算强制**：追加 "Wait" 等提示词，强制继续推理（参考 s1）
6. **上下文工程**：精简输入，把省下的 Token 留给思考
7. **系统化 Loop**：精心设计的 Loop 可让弱模型恢复约 90% 前沿模型性能，成本仅 4%

---

## 8. RPM 策略：20 RPM 极致优化（放弃多账号聚合）

### 8.1 为什么不推荐聚合账号

| 维度 | 分析 |
|-----|------|
| 技术可行性 | 用 New API 等网关聚合多个 API Key 实现负载均衡，技术上可行 |
| 合规风险 | 违反服务条款，属于规避服务限制 |
| 封禁风险 | 一旦被风控识别，所有相关账号可能暂停或永久封禁 |
| 投入产出 | 得不偿失，20 RPM 足够完成高质量工程 |

### 8.2 在 20 RPM 下的最优策略

**核心思路**：精打细算，串行优先，时间换性能。

1. **动态分配推理预算**：Plan-and-Budget 框架分解子问题，按难度分配 Token
2. **级联路由**：Agnes 先试，失败或复杂才升级
3. **极致优化上下文与验证**：截断输出、完整路径、`/new` 隔离；验证器给出具体错误
4. **串行化 Loop**：20 RPM 下并行采样会迅速耗尽额度，转为串行：生成 → 验证 → 诊断 → 修复 → 再验证，直到收敛或达到迭代上限

---

## 9. 完整工作流（融合版）

```
┌─────────────────────────────────────────────────────────────┐
│  阶段  步骤                              Agnes 实现方式       │
├─────────────────────────────────────────────────────────────┤
│  1.需求  OpenSpec 锁定规格，人工确认                         │
│         ├─ Proposal：自然语言描述需求                       │
│         └─ Spec/Design：生成规格文档                        │
├─────────────────────────────────────────────────────────────┤
│  2.设计  Agnes 出设计草案，Critic Agent 审查，人工过单向门   │
│         ├─ Agnes 开启 Thinking 模式生成设计                 │
│         └─ 换角色或子 Agent 做 Critic Review                │
├─────────────────────────────────────────────────────────────┤
│  3.规划  Agnes Thinking 模式拆解任务 → AGENTS.md 写入阶段   │
│         └─ 每阶段含：目标、文件范围、验收条件                │
├─────────────────────────────────────────────────────────────┤
│  4.执行  Agnes 通过 MCP/Bash 操作文件，输出受 AGENTS.md 约束 │
│         └─ 单阶段只做一件事，完成后进入验证                  │
├─────────────────────────────────────────────────────────────┤
│  5.验证  Strict Verifier 跑 Lint/Test/Build                  │
│         ├─ Bash：lint检查                                   │
│         ├─ Bash：单元测试执行                               │
│         └─ Bash：构建验证                                   │
├─────────────────────────────────────────────────────────────┤
│  6.修复  验证失败 → 错误回灌 → Agnes 重试（Loop）            │
│         └─ 最多重试 N 次（设上限，避免空转）                 │
├─────────────────────────────────────────────────────────────┤
│  7.审查  独立 Critic Agent 复审，检查测试覆盖盲区            │
│         └─ 可换角色或启动子 Agent                           │
├─────────────────────────────────────────────────────────────┤
│  8.收敛  验证通过 → 小步提交 → 下一原子任务                  │
│         └─ git commit 小 diff，记录进度                     │
├─────────────────────────────────────────────────────────────┤
│  9.复盘  失败模式写入 Memory/Skill，更新 Skill 库            │
│         └─ 追加到 ~/.agents/skills/<category>/SKILL.md      │
├─────────────────────────────────────────────────────────────┤
│  10.发布  小范围验证后再扩散，关键改动人工确认               │
│          └─ 金丝雀发布：先灰度再全量                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. 实施路线图

### 阶段一：基础环境（1-2天）

- [ ] 安装 Agnes Code，登录免费 Agnes
- [ ] 配置 Thinking 模式（budget_tokens=2048 起步）
- [ ] 建立 `AGENTS.md`，写入字节截断、输出格式、会话隔离规则
- [ ] 配置 `~/.agents/skills/` 目录结构

### 阶段二：流程约束（3-5天）

- [ ] 引入 OpenSpec，跑通 Proposal → Spec → Design → Tasks
- [ ] 配置 Agent Boost Kit，启用 Strict Verifier
- [ ] 建立最小测试与 Lint 流程（npm test / pytest / eslint）

### 阶段三：能力扩展（1-2周）

- [ ] 编写全栈开发 Skill：
  - `frontend-boundary/SKILL.md`：前端组件边界规范
  - `backend-api/SKILL.md`：后端 API 错误处理规范
  - `db-security/SKILL.md`：数据库参数化查询规范
- [ ] 配置 MCP：文件系统、数据库、API 调用
- [ ] 用 `agnes-sync` 和 `agnes mcp sync` 同步配置

### 阶段四：Loop 与优化（持续）

- [ ] 实现串行 Loop：生成 → 验证 → 诊断 → 修复
- [ ] 在 RPM 允许时尝试 Best-of-N
- [ ] 引入 context-kernel / context-guru 等上下文优化工具
- [ ] 记录失败模式，持续更新 Skill

### 阶段五：稳定运行（长期）

- [ ] 动态预算分配（简单任务 Flash，复杂任务 Thinking）
- [ ] 级联路由（置信度 < 阈值 → 升级）
- [ ] 关键改动人工确认（单向门）
- [ ] 定期复盘，优化验证器

---

## 11. 关键指标与预算

| 指标 | 目标 | 测量方式 |
|-----|------|---------|
| 单任务 RPM 消耗 | 尽量低于 20 | 观察 API 调用频率 |
| 单次上下文 Token | 高信号，低噪声 | 截断策略效果评估 |
| 验证通过率 | 每轮提升 | 记录每次 Loop 的通过率 |
| Loop 迭代次数 | 设上限，避免空转 | 最大 5-10 次/子任务 |
| 失败模式复用 | 写入 Skill/Memory | Skill 库迭代计数 |
| 人工介入点 | 单向门、高风险改动 | 记录人工干预次数 |

---

## 12. 理论边界与风险

1. **验证器质量是真正天花板**：验证器不准确，Loop 就是空转
2. **反馈不可理解，Loop 失效**：模糊报错无法驱动修复
3. **采样多样性退化**：N 再大模式趋同也没用
4. **不可验证任务失效**：架构设计、UX、需求理解，Loop 无法兜底
5. **多账号聚合有封禁风险**：不建议作为长期方案
6. **免费 Agnes 的理解和推理能力仍是瓶颈**：外挂弥补执行，不弥补推理上限
7. **省 Token 技巧不降低任务难度**：只是优化预算分配

---

## 13. 核心公式

```
最终性能 ≈ 外挂能力 × 弱模型编排能力 × 接口可靠性 × 验证纠错能力
```

在 20 RPM 下，最安全、最可持续的策略是：
- **极致优化上下文与验证**
- **串行化 Loop**
- **动态分配推理预算**
- **把省下的 Token 投入思考**

这套体系不能让免费 Agnes 变成强模型，但能让它在可验证、可分解、可迭代的任务上，成为一个**稳定、可靠、工程化**的全栈开发助手。

---

## 附录 A：与 Trae Work 知识库的关键差异对照

| 维度 | Trae Work 知识库 (v48.0.0) | Agnes 增强方案 (v2.0) |
|-----|--------------------------|---------------------|
| 目标模型 | Trae Work (GitHub Copilot 竞品) | Agnes-2.5-Flash (免费) |
| 执行环境 | 纯 API 调用 | Agnes Code 桌面端 |
| 扩展机制 | 无原生 Skill/MCP 概念 | Skill + MCP + Thinking 三层 |
| RPM 限制 | 无公开限制 | 20 RPM 硬性约束 |
| 知识库 | 484 个开源模式 | 微信知识库 + 本地 Skill 库 |
| 认证方式 | 自研凭证 | IMA OpenAPI (client_id + api_key) |
| 核心差异 | 模式库广度 | Agnes 工具链深度 |

---

## 附录 B：高频 Skill/MCP 配置速查

### Agnes Code 常用 Skill

```
document-skills:docx    # DOCX 文档操作
document-skills:pdf     # PDF 处理
document-skills:pptx    # PPT 创建
document-skills:xlsx    # Excel 处理
browser-use:control-browser   # 浏览器自动化
browser-use:web-gui-tester    # Web GUI 测试
computer-use:computer-use     # 桌面控制
ima-skill                    # 微信知识库操作
```

### agnes-sync 命令

```bash
# 同步 Skill
agnes-sync pull        # 从远程拉取 Skill
agnes-sync push        # 推送 Skill 到远程

# 同步 MCP 配置
agnes mcp sync         # 将 agents/mcp.json 投射到 Agnes MCP 路径
```

### AGENTS.md 核心规则模板

```markdown
# AGENTS.md — Agnes 编码规则

## 上下文规则
- 引用文件使用完整路径：@src/path/to/file.ts
- 单条规则文本不超过 4000 字符（head/tail 截断）
- 长会话使用 /compact 清理历史

## 输出规则
- 代码任务：只返回代码，不解释（除非要求）
- 文档任务：用表格/列表结构化输出
- 调试任务：先给出根因分析，再给修复方案

## 会话规则
- 新任务用 /new 开启，切断无关历史
- 完成一个原子任务后手动 /compact
- 复杂任务分阶段执行，每阶段独立验证
```

---

## 附录 C：来源说明

- **本文档主体**：基于用户提供原文档《弱模型 Agent 性能增强完整方案》修订
- **知识库内容**：Trae Work 弱模型增强知识库 v48.0.0（484 个模式，21577 行）+ 增量 v20260808（34 个模式）
- **本地项目**：agens-self-enhance / agents-self-enhance / trae-weak-model-enhancer（含 GLM-5.2 对比报告）
- **ZCode Skill 系统**：ima-skill / document-skills / browser-use / computer-use
