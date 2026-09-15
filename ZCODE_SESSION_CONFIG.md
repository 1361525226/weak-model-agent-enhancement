# ZCode 弱模型增强会话配置

> 本文件定义当前会话的 Skill 加载顺序、规则注入和工作流。
> 适用平台：ZCode（非 Agnes Code）

---

## 当前会话激活的 Skill

| Skill | 状态 | 用途 |
|-------|------|------|
| `loop-engineering` (v3.5) | ✅ 已加载 | 循环设计+执行+增益-成本预估 |
| `闭环自进化学习` (v3.3) | ✅ 已加载 | L1-L5 记忆+Skill进化+门控 |
| `open-code-review-delegate` | ✅ 已加载 | OCR 确定性工程+智能审查 |
| `context-engineering` | ✅ 已加载 | 上下文投影+Token优化 |
| `harness-guardrails` | ✅ 已加载 | 输入输出护栏+安全校验 |
| `debugging` | ✅ 已加载 | Reflexion反思+SWE修复 |
| `code-review` | ✅ 已加载 | 七维审查+团队规范 |
| `memory-system` | ✅ 已加载 | 三层记忆架构 |
| `multi-agent` | ✅ 已加载 | Supervisor-Worker+Handoff |
| `skill-evolution` | ✅ 已加载 | Skill自动进化引擎 |
| `fullstack-dev` | ⏳ 按需加载 | 全栈开发最佳实践 |
| `AGENTS.md` (v2.0) | ✅ 已注入 | 编码规则+验证清单 |

---

## 本次会话工作流

```
1. [钩子0] 初始化自检
   → 检查 MEMORY.md / USER.md / MEMORY_GRAPH.md 存在性
   → 检查 .learnings/ 目录
   → 读取 session-state.md 恢复上下文

2. [任务执行] 遵循 AGENTS.md 规则
   → 完整路径引用
   → 字节截断 ≤4000
   → 意图一次说完（目标+文件+期望+验收）

3. [Loop 循环] 如需要多轮迭代
   → 使用 loop-engineering Skill
   → A8 增益-成本预估（默认 R=2）
   → 四维诊断信号监控

4. [验证] Strict Verifier
   → Layer 1: Lint
   → Layer 2: Test
   → Layer 3: Build

5. [反思] 钩子1 WAL
   → 记录成功/失败到 .learnings/
   → 更新 session-state.md

6. [结束] 钩子2 会话反思
   → 辩证推理更新 USER.md
   → 容量检查
```

---

## RPM 预算（ZCode 免费层）

- 当前 RPM：~20（与 Agnes 免费层相同）
- 策略：串行优先，Time换性能
- Thinking 预算：简单任务关闭，复杂任务 1024 tokens

---

## 项目路径

- 项目根目录：`E:/项目/Agnes提升计划`
- Skill 源目录：`E:/项目/Agnes提升计划/skills/`
- Pattern 源目录：`E:/项目/Agnes提升计划/agens-agent-patterns/skills/`
- 知识库 KB_ID：`L3oKvpnu0uVfNeVrsfs0zQxKwDB9kDqnuozkXM44_y4=`

---

## 立即可以执行的任务

1. **代码开发**：使用 fullstack-dev + loop-engineering
2. **Bug修复**：使用 debugging + reflexion_accumulator.py
3. **代码审查**：使用 code-review + open-code-review-delegate
4. **上下文优化**：使用 context-kernel.py
5. **Skill进化**：使用 skill-evolution（失败3次后自动触发）
