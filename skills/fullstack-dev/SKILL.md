# Skill: Full-Stack Development — 全栈开发最佳实践

## 触发条件
全栈开发任务（前端+后端+数据库）。

## 适用场景
- 前后端 API 开发
- 数据库设计
- 前端组件开发
- 全栈功能实现

## 执行步骤

### Step 1: 前端边界规范（frontend-boundary）

```markdown
## 组件边界原则
1. 每个组件只负责一件事（Single Responsibility）
2. Props 接口明确，不做隐式依赖
3. 状态提升：共享状态放在父组件
4. 副作用分离：useEffect 只处理外部交互
```

**前端组件 SKILL 模板：**

```typescript
// 组件边界检查清单
const COMPONENT_CHECKLIST = [
  "Props interface fully typed?",
  "No implicit dependencies on parent state?",
  "Side effects in useEffect only?",
  "Error boundary wrapped?",
  "Loading state handled?",
  "Accessibility (aria attributes)?",
]

// 生成组件时必须通过检查
function validateComponent(component: string): boolean {
  return COMPONENT_CHECKLIST.every(check => checkIn(component, check))
}
```

### Step 2: 后端 API 规范（backend-api）

```markdown
## API 设计原则
1. RESTful 路由设计
2. 统一错误响应格式
3. 参数验证（Zod/Pydantic）
4. 速率限制
5. 认证授权中间件
```

**后端 API SKILL 模板：**

```python
# 统一错误响应
class APIError(Exception):
    def __init__(self, status_code: int, message: str, code: str = None):
        self.status_code = status_code
        self.message = message
        self.code = code

# 错误处理中间件
@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "code": exc.code}
    )

# 参数验证（Pydantic）
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
```

### Step 3: 数据库安全规范（db-security）

```markdown
## 数据库安全原则
1. 永远使用参数化查询（防 SQL 注入）
2. 敏感字段加密存储
3. 最小权限原则
4. 查询超时设置
5. 连接池管理
```

**数据库安全 SKILL 模板：**

```python
# ❌ 危险：SQL 拼接
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ 安全：参数化查询
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# ✅ 更安全：ORM
user = User.query.filter_by(email=email).first()
```

### Step 4: 全栈任务分解模板

```markdown
## 全栈功能开发流程
1. 数据库层：设计 schema + migration
2. 后端层：API 路由 + 服务层 + 验证
3. 前端层：组件 + API 调用 + 状态管理
4. 集成测试：端到端验证
5. 安全审查：注入/越权检查
```

### Step 5: 验收条件模板

```markdown
## 前端验收
- [ ] 组件 TypeScript 类型完整
- [ ] ESLint 无 error
- [ ] 单元测试覆盖率 > 80%
- [ ] 无障碍访问检查通过

## 后端验收
- [ ] API 参数验证通过
- [ ] 错误响应格式统一
- [ ] 数据库查询参数化
- [ ] 单元测试覆盖率 > 80%

## 数据库验收
- [ ] Migration 可逆
- [ ] 索引合理
- [ ] 外键约束完整
- [ ] 敏感字段加密
```

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | 三个 Skill 顺序执行 + MCP 工具 |
| **Aider** | 多文件编辑 + auto-commit |
| **LangGraph** | DB → API → Frontend 节点链 |
| **OpenHands** | 多 Agent 分工（DB Agent + API Agent + UI Agent）|
| **DeerFlow** | Supervisor 分配 SubAgent |

## 验证标准
- 全栈功能验收条件 100% 通过
- 安全扫描无高危漏洞
- 测试覆盖率 > 80%

## 失败处理
- 前端失败 → 回退到组件级修复
- 后端失败 → 检查 API 规范
- 数据库失败 → 检查 migration 和参数化查询
