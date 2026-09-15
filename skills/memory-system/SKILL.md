# Skill: Memory System — 记忆提取、分页与图谱

## 触发条件
长对话、跨会话任务、需要保持一致性时。

## 适用场景
- 跨会话状态保持
- 用户偏好学习
- 项目知识积累
- 历史事实检索

## 执行步骤

### Step 1: 记忆提取（Episodic → Semantic）

```python
# 从对话中提取结构化事实
def extract_memory(conversation_turns: list) -> list:
    memories = []
    for turn in conversation_turns[-10:]:  # 最近 10 轮
        # 使用 LLM 提取事实
        facts = llm_extract(
            f"从以下对话中提取事实：\n{turn}",
            schema=["user_preference", "project_fact", "decision", "error_pattern"]
        )
        memories.extend(facts)
    return memories
```

### Step 2: 三层记忆架构

```
┌─────────────────────────────────────┐
│  Working Memory（工作记忆，~4K token） │  ← 当前会话可见
│  - 当前任务上下文                    │
│  - 最近 5 轮对话                     │
│  - 活跃变量                          │
├─────────────────────────────────────┤
│  Core Memory（核心记忆，持久化）      │  ← 跨会话可见
│  - 用户偏好（MEMORY.md）            │
│  - 项目规范（CONTEXT.md）           │
│  - 成功模式（SUCCESS_PATTERNS.md）  │
│  - 失败模式（ERRORS.md）            │
├─────────────────────────────────────┤
│  Archive Memory（归档记忆）          │  ← 按需检索
│  - 历史任务记录                      │
│  - 旧版本 Skill                      │
│  - 实验数据                           │
└─────────────────────────────────────┘
```

### Step 3: 文件系统记忆（Memory as File System）

```
项目根目录/
├── MEMORY.md              # 核心记忆（跨会话）
├── CONTEXT.md             # 共享语言/术语表
├── SUCCESS_PATTERNS.md    # 成功模式库
├── ERRORS.md              # 失败模式库
├── LEARNINGS.md           # 学习记录
└── .loop/
    ├── state.md           # 当前状态
    └── run-log.md         # 运行日志
```

**MEMORY.md 模板：**

```markdown
# 项目记忆

## 用户偏好
- 偏好 Python 用于后端开发
- 项目使用 FastAPI + PostgreSQL

## 项目事实
- 技术栈：React + Node.js + PostgreSQL
- 部署：Docker + Kubernetes
- 代码规范：ESLint + Prettier

## 关键决策
- 2024-01-15：选择 PostgreSQL 而非 MongoDB
- 2024-02-20：引入 LangGraph 做工作流编排
```

### Step 4: 访问频率驱动分层（Access-Frequency-Driven Tiering）

```python
# 记忆分层检索
class MemoryTier:
    def __init__(self):
        self.working = []      # 热数据（最近访问）
        self.core = {}         # 温数据（常用）
        self.archive = []      # 冷数据（历史）
    
    def get(self, query: str, top_k=3) -> list:
        # 1. 先查 working
        results = self._search(self.working, query)
        if results:
            return results[:top_k]
        
        # 2. 再查 core（内存索引）
        results = self._search_indexed(self.core, query)
        if results:
            self._promote_to_working(results)
            return results[:top_k]
        
        # 3. 最后查 archive（磁盘检索）
        results = self._search_archive(query)
        return results[:top_k]
```

### Step 5: 时序知识图谱（Temporal Knowledge Graph）

```python
# 从对话中提取带时间戳的事实
from zep_cloud import Zep

zep = Zep(api_key="...")
zep.memory.add_message(
    session_id="s1",
    role="user",
    content="我在腾讯工作，之前在阿里待了三年"
)
# 自动提取：
# (用户)-[WORKED_AT{until:2023}]->(阿里)
# (用户)-[WORKS_AT{since:2023}]->(腾讯)

facts = zep.memory.search(session_id="s1", text="工作经历")
# 返回带时间戳的有效事实，自动消解矛盾
```

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | MEMORY.md + Skill 库 + `~/.agents/skills/` |
| **Agno** | Built-in Memory（短期+长期） |
| **LangGraph** | Long-term Memory + SqliteSaver |
| **Aider** | Git 历史 + .aidermem 文件 |
| **OpenHands** | Durable Memory + Checkpointer |
| **DeerFlow** | 双层内存（工作记忆+归档记忆） |

## 验证标准
- 跨会话事实一致性 > 90%
- 记忆检索命中率 > 80%
- 过期记忆自动淘汰（< 30 天未访问）

## 失败处理
- 记忆冲突 → 保留最新事实，记录旧事实到 ERRORS.md
- 检索失败 → 降级到全量搜索
- 内存溢出 → 触发压缩（/compact）
