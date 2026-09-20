# AGENTS.md — Agnes Code 编码规则（完整版）

> 本文件位于项目根目录，自动加载。修改后立即生效，无需重启。
> 版本：v3.8 | 核心目标：通过工程化手段增强弱模型在Agent驱动下的表现性能
> 交叉进化来源：GenericAgent(14K⭐) + OpenViking(38K⭐) + EverOS(13K⭐)

---

## 一、核心理念

**我们不增强模型，我们增强 Harness。**

同模型在不同 Agent 平台上的性能差异可达 15-22pp。关键在于：
- Harness 质量（决定 40% 性能上限）
- Context 质量（决定 30% 性能上限）
- Loop 效率（决定 25% 性能上限）
- 验证可靠性（决定 50% 性能上限）

---

## 二、上下文规则

### 2.1 文件引用
- **必须使用完整路径**：`@E:/项目/Agnes提升计划/AGENTS.md`
- 优先注入当前任务直接相关文件，不注入无关历史

### 2.2 字节截断
```bash
head -c 4000 "$FILE_PATH"    # 保留头部
tail -c 4000 "$FILE_PATH"    # 保留尾部
```

### 2.3 三级上下文加载（OpenViking 模式）
- **HOT tier**（热）：当前任务直接相关文件，已加载到上下文窗口
- **WARM tier**（温）：最近 N 个任务的相关文件，缓存中
- **COLD tier**（冷）：全量项目文件索引，按需加载
- 原则：优先注入 HOT tier，避免无关历史占用上下文
- 新任务使用 `/new` 开启
- 长会话（>20轮）使用 `/compact`
- 完成一个原子任务后手动 `/compact`

### 2.4 意图一次说完
每次 prompt 包含：
1. **目标**：一句话描述
2. **文件**：完整路径
3. **期望**：输出格式
4. **验收条件**：可执行命令

### 2.5 SOP 结晶原则（GenericAgent 模式）
- 重复任务 ≥3 次 → 自动提炼为标准操作程序（SOP）
- SOP 写入对应 Skill 的 `patterns/` 子目录
- 新任务执行前先检查是否已有匹配 SOP

---

## 三、7阶段工作流

```
1.需求 → 2.设计 → 3.实现 → 4.验证 → 5.审查 → 6.复盘 → 7.发布
```

### 阶段 1：需求（OpenSpec）
- 产出：Spec.md（含验收条件）
- 人工确认单向门

### 阶段 2：设计（Agent草案 + Critic审查）
- 产出：Design.md + Review.md
- Critic Agent 用 open-code-review-delegate Skill
- 人工单向门签批

### 阶段 3：实现（TDD循环）
- 红→绿→重构循环
- 每步 Strict Verifier（Lint/Test/Build）
- 失败错误回灌重试（≤3次）

### 阶段 4：验证（Best-of-N）
- 简单：串行 R=2
- 中等：Best-of-3
- 复杂：ToT K=3
- 极复杂：Forest K=5
- 四维诊断信号监控

### 阶段 5：审查（Critic Agent）
- open-code-review-delegate
- CRITIC 外部验证层
- 盲区检查

### 阶段 6：复盘（Reflexion）
- 失败模式写入 ERRORS.md
- 成功模式写入 SUCCESS_PATTERNS.md
- 高频失败触发 Skill 进化

### 阶段 7：发布（金丝雀）
- 小范围验证
- 安全漂移检测
- 人工确认关键改动

---

## 四、输出规则

### 4.1 代码任务
```
要求：只返回代码，不解释
例外：调试/架构讨论需要解释根因
```

### 4.2 文档任务
```
要求：用表格/列表结构化输出
禁止：大段连续文字
```

### 4.3 调试任务
```
【根因】...
【修复】
```language
...代码...
```
【验证】$ command
```

---

## 五、验证规则

### 5.1 三层验证
```
Layer 1: Lint（静态检查）
Layer 2: Test（单元测试）
Layer 3: Build（构建验证）
```

### 5.2 验证失败处理
```
SyntaxError → 检查代码结构
TypeError → 检查类型标注
ImportError → 检查依赖
AssertionError → 检查业务逻辑
Test Failed → 读取失败用例，针对性修复
```

### 5.3 错误回灌格式
```
上次执行失败：
文件：{file_path}:{line_number}
错误：{error_message}
类型：{error_type}
请修复后重新生成。
```

---

## 六、安全护栏

### 6.1 输入护栏
- 检测 prompt injection
- 文件大小限制：单次 ≤8000 字符
- UTF-8 编码校验

### 6.2 输出护栏
- JSON 必须通过 schema 验证
- 代码必须通过 lint 检查
- 安全敏感操作必须人工确认

### 6.3 危险操作白名单
```
SAFE：read, write, execute_script, create_file, update_file
RISKY：rm, delete, deploy, restart_service → 人工确认
BLOCKED：format_disk, wipe_data → 直接拒绝
```

---

## 七、Token 预算分配

| 级别 | 描述 | Thinking预算 | 最大Token | 最大轮次 |
|-----|------|------------|----------|---------|
| S | 读/写小函数 | 关闭 | 1,000 | 1 |
| A | 单模块功能 | 512 | 3,000 | 3 |
| B | 多模块联动 | 1024 | 8,000 | 5 |
| C | 架构设计 | 2048 | 20,000 | 8 |
| X | 高风险操作 | 4096 | 5,000 | 1（人工确认）|

---

## 八、记忆与复盘

### 8.1 成功模式记录
```markdown
## {task_name}
- 目标：{description}
- 方案：{approach}
- 验收命令：{command}
- 日期：{date}
```

### 8.2 失败模式记录
```markdown
## {error_name}
- 任务：{description}
- 错误类型：{type}
- 根因：{root_cause}
- 修复方案：{fix}
- 日期：{date}
```

### 8.3 Skill 迭代
高频失败模式 → 抽象为 Skill → 写入 `~/.zcode/skills/<category>/SKILL.md`

### 8.4 离线记忆反思（EverOS 模式）
- 任务完成后：自动触发 `offline_reflection()`
- 合并相似 episode → 提炼共性 → 更新 Skill 规则
- 压缩旧会话历史，维持上下文窗口最优

---

## 九、技能清单

| Skill | 用途 | 触发条件 |
|-------|------|---------|
| loop-engineering | 循环设计+执行+SOP结晶 | /loop, /goal |
| 闭环自进化学习 | L1-L5记忆+Skill进化+离线反思 | 每次任务后 |
| open-code-review-delegate | 代码审查 | /open-code-review-delegate |
| context-engineering | 三级上下文加载 | 大文件/多文件任务 |
| harness-guardrails | 输入输出护栏+AgentDoG诊断 | 安全敏感操作 |
| debugging | Reflexion+Error Depth分析 | bug/错误 |
| code-review | 七维审查 | 提交前 |
| memory-system | 正交检索+记忆压缩 | 跨会话任务 |
| multi-agent | Supervisor-Worker | 复杂分工任务 |
| skill-evolution | SOP结晶+Skill自动进化 | 失败≥3次 |
| fullstack-dev | 全栈最佳实践 | 前后端开发 |

---

## 十、工作流检查清单

### 需求阶段
- [ ] Spec.md 已生成
- [ ] 验收条件可执行
- [ ] 人工确认签批

### 设计阶段
- [ ] Design.md 已生成
- [ ] Critic Agent 已审查
- [ ] 人工单向门签批

### 实现阶段
- [ ] 每个任务有明确验收条件
- [ ] 完成后运行 Lint/Test/Build
- [ ] 失败后错误回灌重试（≤3次）

### 验证阶段
- [ ] Best-of-N 采样完成
- [ ] 四维诊断信号正常
- [ ] 早停条件未触发
- [ ] SOP结晶检查（重复任务是否已提炼）

### 审查阶段
- [ ] Critic Agent 复审完成
- [ ] Critical/High 问题已处理
- [ ] 盲区检查完成

### 复盘阶段
- [ ] 失败模式写入 ERRORS.md
- [ ] 成功模式写入 SUCCESS_PATTERNS.md
- [ ] Skill 库已检查是否需要更新
- [ ] 离线记忆反思执行

### 发布阶段
- [ ] 小范围验证通过
- [ ] 关键改动人工确认
- [ ] 安全漂移检测通过
