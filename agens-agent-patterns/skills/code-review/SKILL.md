# Skill: Code Review — 技能化代码审查

## 触发条件
代码提交前、PR 审查时、完成原子任务后。

## 适用场景
- 代码质量检查
- 安全漏洞扫描
- 团队规范一致性
- 测试覆盖度评估

## 执行步骤

### Step 1: 加载团队规范 Skill

```markdown
# 代码审查 Skill 加载顺序
1. 团队编码规范（team-code-review/SKILL.md）
2. 安全策略（security/SKILL.md）
3. 架构约束（architecture/SKILL.md）
```

### Step 2: 多维度审查

```python
# 审查维度
REVIEW_CHECKLIST = [
    {"name": "correctness", "weight": 3, "check": verify_correctness},
    {"name": "security", "weight": 3, "check": scan_security},
    {"name": "performance", "weight": 2, "check": check_performance},
    {"name": "readability", "weight": 1, "check": check_readability},
    {"name": "testing", "weight": 2, "check": check_test_coverage},
]

def code_review(code: str, context: dict) -> dict:
    results = {}
    for check in REVIEW_CHECKLIST:
        score, issues = check["check"](code, context)
        results[check["name"]] = {
            "score": score,
            "issues": issues,
            "weighted": score * check["weight"]
        }
    
    total_score = sum(r["weighted"] for r in results.values())
    max_score = sum(c["weight"] for c in REVIEW_CHECKLIST) * 10
    return {
        "overall_score": total_score / max_score,
        "details": results,
        "recommendation": "approve" if total_score / max_score > 0.8 else "revise"
    }
```

### Step 3: 审查报告输出

```markdown
## 代码审查报告

### 总体评分：85/100 ✅ 通过

### 各维度详情
| 维度 | 分数 | 问题 |
|-----|------|------|
| 正确性 | 9/10 | 边界条件未处理 |
| 安全性 | 10/10 | 无问题 |
| 性能 | 8/10 | 建议添加索引 |
| 可读性 | 9/10 | 注释不足 |
| 测试 | 7/10 | 缺少边界测试 |

### 待修复问题
1. [P0] 边界条件：当 input=null 时返回 500 错误
   文件：@src/api/handlers/user.go:45
   建议：添加 null check

2. [P1] 缺少数据库索引
   文件：@src/db/migrations/001_init.sql
   建议：在 user_email 字段添加 UNIQUE 索引
```

### Step 4: 自动修复建议

```python
# 针对常见问题自动生成修复建议
FIX_TEMPLATES = {
    "null_check": """
    if input is None:
        return {"error": "input cannot be null"}, 400
    """,
    "add_index": """
    CREATE INDEX idx_user_email ON users(email);
    """,
    "add_test": """
    def test_edge_case_null_input():
        response = client.get("/api/user", params={"id": None})
        assert response.status_code == 400
    """
}
```

### Step 5: 审查模式固化

```markdown
# 高频问题模式 → 写入 Skill
每次发现新问题模式，追加到 skills/code-review/patterns.md：

## patterns.md
### sql_injection_risk
- 检测：未参数化的 SQL 拼接
- 修复：使用参数化查询或 ORM
- 案例：@src/db/query.py:23

### unhandled_exception
- 检测：try/except 过于宽泛
- 修复：细化异常类型
- 案例：@src/api/handlers/user.go:67
```

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | Skill 注入团队规范 + Critic Agent 复审 |
| **Aider** | `.aider.skills/` + `--edit-format diff` |
| **LangGraph** | 独立 review 节点 + guardrail |
| **OpenHands** | SubAgent 专职审查 |
| **DeerFlow** | Supervisor 审查节点 |

## 验证标准
- 审查覆盖率 100%（所有提交必经审查）
- P0 问题拦截率 > 95%
- 误报率 < 10%

## 失败处理
- 误报 → 添加到白名单
- 漏报 → 追加检测规则
- 审查超时 → 降级到人工审查
