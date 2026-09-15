# Skill: Loop Engineering — 串行循环模板

## 触发条件
任务需要多次尝试才能完成，或涉及"生成→验证→修复"迭代流程。

## 适用场景
- 代码生成（单函数/单模块）
- Bug 修复
- 配置调整
- 任何有明确验收条件的任务

## 执行步骤

### Step 1: 定义原子任务
将大任务拆为原子任务（每步只改一个文件/一个函数）。

```markdown
原子任务模板：
- 目标：[一句话描述]
- 输入文件：[完整路径]
- 验收条件：[可执行的检查命令]
- 最大重试次数：3
```

### Step 2: 生成（Generate）
基于当前上下文生成代码/方案。

```
Prompt:
你正在执行原子任务：{目标}
上下文文件：{文件路径}
请生成实现代码，满足以下验收条件：{验收条件}
只返回代码，不解释。
```

### Step 3: 验证（Validate）
运行验收条件检查。

```bash
# 示例：单元测试
pytest tests/test_{$task_name}.py -v

# 示例：Lint 检查
eslint src/path/to/file.ts

# 示例：构建验证
npm run build
```

### Step 4: 诊断（Diagnose）
若验证失败，分析错误原因。

```
失败类型判断：
- SyntaxError → 语法问题，检查代码结构
- TypeError → 类型问题，检查参数/返回值
- AssertionError → 逻辑问题，检查业务逻辑
- Import error → 依赖问题，检查包引用
```

### Step 5: 修复（Fix）
将错误信息拼入 prompt，重试。

```
重试 Prompt:
上次执行失败，错误信息：
{error_message}
文件：{file_path}
行号：{line_number}
请修复后重新生成代码。
```

### Step 6: 反思（Reflect）
成功或达到上限后，记录结果。

```markdown
# 成功
追加到 SUCCESS_PATTERNS.md：
- 任务：{description}
- 方案：{approach}
- 验收命令：{validation_command}

# 失败（达到上限）
追加到 ERRORS.md：
- 任务：{description}
- 错误类型：{error_type}
- 根因：{root_cause}
- 建议方案：{suggested_fix}
```

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | Agent 工具 run_in_background，每次调用串行执行 |
| **Aider** | `--auto-commits` 原生 Edit-Test-Commit 循环 |
| **LangGraph** | StateGraph + conditional edges + SqliteSaver |
| **OpenHands** | CodeSelfRepairEngine.repair_cycle() |
| **DeerFlow** | Supervisor loop + SubAgent 执行 |

## 失败处理
- 重试 3 次仍失败 → 升级到人（单向门）
- 错误模式写入 ERRORS.md，下次直接引用
- 不要无限循环，设 max_iterations=5

## 验证标准
- 验收条件通过 → Loop 成功
- 错误信息具体可执行 → 诊断有效
- 每次重试基于上轮错误 → 不回退重做
