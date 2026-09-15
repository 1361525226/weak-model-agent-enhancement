# Skill: Skill Evolution — Skill 自动进化引擎

## 触发条件
- 同类任务失败 ≥3 次
- 完成复杂任务后自动触发
- 用户显式请求 "/evolve"

## 适用场景
- Skill 库需要迭代优化
- 重复失败模式需要抽象为规则
- 新发现的 Best Practice 需要固化

## 执行步骤

### Step 1: 收集证据
```bash
# 读取失败模式
cat .learnings/ERRORS.md | tail -50
cat .loop/run-log.md | tail -30

# 识别重复模式（Pattern-Key 匹配）
grep -r "Pattern-Key" .learnings/ | sort | uniq -c | sort -rn | head -10
```

### Step 2: 根因分类
对每个重复失败模式，判断根因类型：

| 根因类型 | 处理方式 |
|---------|---------|
| Skill 缺失 | 创建新 Skill |
| Skill 错误 | 编辑现有 Skill |
| 执行问题 | 记录到 ERRORS.md，不修改 Skill |
| 环境问题 | 记录到 ERRORS.md，更新 MEMORY.md |

### Step 3: G1-G7 门控检查

```
G1 唯一性: 是否与已有 Skill 功能重叠 >30%?
G2 大小: 预估 SKILL.md 是否 ≤15KB?
G3 依赖: 是否需要 API Key / 外部服务?
G4 语义: 是否偏离原始目的?
G5 可验证: 是否有验证方法?
G6 反漂移: 是否增加不必要复杂度?
G7 七维审查: 安全/正确性/性能/可维护性/测试/可访问性/文档
```

### Step 4: CRITIC 外部验证
- 代码验证：执行 Skill 中的示例代码
- 路径验证：检查 Skill 引用的文件路径
- 一致性验证：git diff 检查变更

### Step 5: 部署
- 通过 → 写入 skills/<category>/SKILL.md
- 失败 → 记录到 .learnings/rejected_edits.json

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | 本 Skill + reflexion_accumulator.py |
| **Aider** | .aider.skills/ 手动更新 |
| **LangGraph** | 通过节点验证后更新 Skill |
| **OpenHands** | repair_cycle 后自动更新 |

## 验证标准
- G1-G7 全部通过
- 外部工具验证通过
- 不与已有 Skill 冲突

## 失败处理
- 任一门控不通过 → 拒绝创建，记录原因
- 验证失败 → 修复后重新提交
