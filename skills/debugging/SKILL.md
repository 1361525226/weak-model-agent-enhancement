# Skill: Debugging — Reflexion 与自主修复

## 触发条件
代码运行失败、测试不通过、出现报错时。

## 适用场景
- Bug 修复
- 错误诊断
- 性能问题排查
- 配置错误修正

## 执行步骤

### Step 1: 错误分类

```python
ERROR_CATEGORIES = {
    "syntax": {"pattern": "SyntaxError", "action": "fix_structure"},
    "type": {"pattern": "TypeError", "action": "fix_types"},
    "runtime": {"pattern": "Exception", "action": "add_guard"},
    "logic": {"pattern": "AssertionError", "action": "fix_logic"},
    "dependency": {"pattern": "ImportError", "action": "fix_imports"},
    "config": {"pattern": "ConfigError", "action": "fix_config"},
}

def classify_error(error_msg: str) -> str:
    for category, info in ERROR_CATEGORIES.items():
        if info["pattern"] in error_msg:
            return category
    return "unknown"
```

### Step 2: Reflexion 语言反思（pattern_065）

```python
# 让 Agent 在失败后生成自然语言反思
def reflexion_loop(task, error_msg, max_attempts=3):
    reflections = []
    
    for attempt in range(max_attempts):
        # 执行
        result = execute_task(task)
        
        if result.success:
            return result
        
        # 失败 → 生成反思
        reflection = generate_reflection(
            task=task,
            error=error_msg,
            attempt=attempt,
            previous_reflections=reflections
        )
        reflections.append(reflection)
        
        # 反思注入下一轮
        task = f"{task}\n\n反思：{reflection}"
        error_msg = result.error
    
    return {"success": False, "reflections": reflections}

# 反思生成 prompt
REFLECTION_PROMPT = """
任务：{task}
错误：{error}
已尝试：{attempt} 次
之前的反思：{previous_reflections}

请分析：
1. 错误的根本原因是什么？
2. 之前哪里想错了？
3. 下一步应该尝试什么不同的方法？

用一句话总结反思：
"""
```

### Step 3: SWE-agent 自主修复循环（pattern_111）

```python
# Agent-Computer Interface（ACI）
class SWEEagentLoop:
    def __init__(self, model, repo_path):
        self.model = model
        self.repo = repo_path
    
    def locate(self, error_msg: str) -> dict:
        """定位问题文件和行号"""
        result = self.model.generate(f"""
        错误信息：{error_msg}
        仓库路径：{self.repo}
        请定位问题文件、行号和原因。
        返回 JSON: {{"file": "...", "line": N, "cause": "..."}}
        """)
        return json.loads(result)
    
    def edit(self, file_path: str, line: int, fix: str) -> bool:
        """编辑代码"""
        # 使用 ACI 专用编辑命令
        return self.model.execute(f"edit {file_path}:{line} \"{fix}\"")
    
    def test(self) -> dict:
        """运行测试"""
        return self.model.execute("pytest -v")
    
    def loop(self, error_msg: str, max_iter=5):
        """自主修复循环"""
        for i in range(max_iter):
            # 定位
            loc = self.locate(error_msg)
            # 编辑
            self.edit(loc["file"], loc["line"], loc["cause"])
            # 测试
            result = self.test()
            if result["passed"]:
                return {"status": "fixed", "iterations": i+1}
            error_msg = result["failure_message"]
        
        return {"status": "failed", "iterations": max_iter}
```

### Step 4: 错误模式库（ERRORS.md）

```markdown
# 错误模式库

## sql_injection_risk
- **错误信息**：`psycopg2.errors.InsufficientPrivilege`
- **根因**：SQL 拼接未参数化
- **修复**：使用参数化查询
- **案例**：@src/db/query.py:23
- **上次修复**：2024-03-15

## null_pointer_risk
- **错误信息**：`TypeError: Cannot read property 'x' of null`
- **根因**：未检查 null/undefined
- **修复**：添加可选链 `?.` 或 null check
- **案例**：@src/api/handlers/user.ts:45

## race_condition
- **错误信息**：`Deadlock found when trying to get lock`
- **根因**：并发事务锁冲突
- **修复**：添加重试逻辑 + 锁定顺序
- **案例**：@src/db/transactions.go:67
```

### Step 5: 调试 Checklist

```markdown
## 通用调试流程
1. 复现问题（最小化 repro）
2. 读取错误信息（完整 traceback）
3. 定位文件（error 指向）
4. 分析原因（根据 ERROR_CATEGORIES）
5. 生成修复（Reflexion prompt）
6. 验证修复（运行测试）
7. 记录模式（写入 ERRORS.md）
```

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | Agent 工具 + ERRORS.md 模式库 |
| **Aider** | `--auto-ask` 交互式修复 |
| **LangGraph** | diagnose → fix → verify 节点链 |
| **OpenHands** | CodeSelfRepairEngine.repair_cycle() |
| **DeerFlow** | SubAgent 专职调试 |

## 验证标准
- 一次性修复成功率 > 60%
- 3 次内修复成功率 > 90%
- 错误模式复用率 > 50%

## 失败处理
- 5 次失败 → 升级到人（单向门）
- 新错误模式 → 追加到 ERRORS.md
- 重复错误 → 检查模式库是否遗漏
---

## 交叉进化增强（v3.8）

### Error Depth 深度分析（Decoding Self-Correction 论文）

错误深度定义：从症状到根因的函数调用栈深度。

| 深度 | 错误类型 | 修复策略 |
|------|---------|---------|
| 1（浅） | SyntaxError, NameError | 直接修复语法/拼写 |
| 2（中浅） | TypeError, ImportError | 修复类型/依赖 |
| 3（中） | AssertionError | 修复业务逻辑 |
| 4（深） | ArchitectureError | 架构重构 |
| 5（最深） | RequirementError | 需求澄清 |

```python
ERROR_DEPTH = {
    "syntax": 1, "name": 1,
    "type": 2, "import": 2,
    "assertion": 3, "logic": 3,
    "architecture": 4,
    "requirement": 5,
}

def analyze_error_depth(error_trace):
    max_d = max(ERROR_DEPTH.get(e.get('type', 'syntax'), 1) for e in error_trace)
    if max_d <= 2:
        return {'depth': 'shallow', 'strategy': 'direct_fix'}
    elif max_d <= 3:
        return {'depth': 'medium', 'strategy': 'refactor_module'}
    else:
        return {'depth': 'deep', 'strategy': 'architectural_review'}
```

### Reflexion 增强
失败后不仅记录错误，还进行根因深度分析：

```python
def enhanced_reflexion(failed_task):
    record_error(failed_task)           # 原有：记录错误
    depth_info = analyze_error_depth(failed_task.trace)  # 新增：分析深度
    root_cause = trace_root_cause(failed_task.trace)     # 新增：追溯根因
    update_skill_rule(failed_task.skill, root_cause)     # 新增：更新规则
    if failed_task.repeated >= 3:
        crystallize_sop(failed_task)                        # 新增：SOP结晶
```
