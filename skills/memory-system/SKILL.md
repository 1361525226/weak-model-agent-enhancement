# Skill: Memory System v2 — 基于 elfmem + memento + llm-wiki 交叉进化

## 触发条件
跨会话记忆管理、知识检索、记忆衰减/晋升、多Agent共享记忆。

## 来源模式（交叉进化）

### 1. elfmem（59 stars, Python）— 自适应记忆系统
> 核心创新：**内容可寻址 + Decay Tier + Ledger 事件日志 + RRF 三路融合检索**

- **内容地址块**：SHA-256 去重，相同内容只存一份
- **Decay Tier 分层**：PERMANENT / DURABLE / STANDARD / EPHEMERAL / ARCHIVED
- **Ledger 事件日志**：追加不可变事件流（reinforcement/recency/centrality）
- **RRF 三路融合检索**：向量 + BM25 + 图谱 → Reciprocal Rank Fusion (k=60)
- **Volatility Class**：identity/project/status 三类，区分"不再被使用"vs"不再真实"

### 2. memento（25 stars, Python/Go）— 跨Agent共享记忆
> 核心创新：**概念化记忆 + 提案-审查-发布工作流 + Git 审计追踪**

- **Concept 模型**：稳定ID + 结构化元数据 + Markdown 链接
- **Proposal-Review-Publish**：写操作必须经过审查，保留审计轨迹
- **Namespace 隔离**：不同Agent/项目有独立命名空间
- **Asset Pack**：Skill/模板可打包为概念资产

### 3. llm-wiki-brain（32 stars, Python）— 文件系统优先的记忆
> 核心创新：**Markdown 源数据 + Obsidian wikilinks + FTS5 索引 + drift detection**

- **Vault 结构**：START_HERE.md + _agent/ 目录 + 分层文件夹
- **Lint**：frontmatter + wikilinks + secrets 检查
- **Drift Detection**：源内容哈希 vs 索引一致性检查
- **Promote-Candidates**：自动识别晋升候选（高频引用+低龄）

---

## 执行步骤

### Step 1: 记忆写入（Content-Addressable Write）

```python
def write_memory(path: str, content: str, tier: str = "STANDARD",
                 tags: list[str] = None, category: str = "general"):
    """
    tier: PERMANENT | DURABLE | STANDARD | EPHEMERAL | ARCHIVED
    tags: self/constitutional, self/value, project/*, observation
    category: identity | project | status | observation | concept
    """
    # 1. 内容哈希（elfmem 模式）
    content_hash = sha256(content.strip().lower())[:16]
    
    # 2. 衰减层级
    decay_tier = determine_decay_tier(tags, category)
    
    # 3. 写入 Markdown 文件（llm-wiki 模式）
    vault_path = f".learnings/vault/{path}.md"
    
    # 4. 追加 Ledger 事件（elfmem 模式）
    append_ledger_event("write", path, content_hash, decay_tier)
    
    return {"path": vault_path, "hash": content_hash, "tier": decay_tier}
```

### Step 2: 记忆检索（Hybrid Retrieval Pipeline）

```python
def search_memory(query: str, top_k: int = 5, budget: int = 4000) -> list[dict]:
    """
    6阶段混合检索管道（elfmem 模式）：
    Stage 1: 预过滤（活跃块 + 搜索窗口）
    Stage 2: 向量搜索（余弦相似度 → top N_seeds × 4）
    Stage 2b: BM25 关键词搜索（term overlap）
    Stage 2c: RRF 融合（1/(k + rank)，k=60）
    Stage 3: 图谱扩展（1-hop neighbours）
    Stage 4: 复合评分（recency + reinforcement + centrality）
    Stage 5: MMR 多样性重排序（lambda=0.7）
    """
    bm25_results = bm25_search(query, top_k=top_k * 2)
    vector_results = vector_search(query, top_k=top_k * 2)
    fused = rrf_fuse(bm25_results, vector_results, k=60)
    expanded = graph_expand(fused, hops=1)
    scored = composite_score(expanded, budget=budget)
    final = mmr_reorder(scored, diversity_lambda=0.7)
    return final[:top_k]
```

### Step 3: 记忆衰减与晋升

```python
def memory_lifecycle_check():
    """
    晋升路径（elfmem + llm-wiki 融合）：
      EPHEMERAL → STANDARD: 引用 ≥ 3次 + 7天窗口
      STANDARD → DURABLE: 引用 ≥ 5次 + 跨 ≥ 3任务
      DURABLE → PERMANENT: 用户确认 + constitutional tag
    
    降级路径：
      HOT → WARM: 30天未引用
      WARM → COLD: 90天未引用
      COLD → ARCHIVED: 180天未引用 或 被 NEWER 替代
    
    内容漂移检测（llm-wiki 模式）：
      哈希变化 → 标记 STALE
      与上游矛盾 → 标记 CONTRADICTED
    """
    pass
```

### Step 4: 跨Agent共享（memento 模式）

```python
def share_memory(namespace: str, concept_id: str, proposal: dict):
    """
    跨Agent共享记忆工作流：
    1. Agent A 创建 Proposal（修改某概念）
    2. Curator（另一Agent或人）审查 Proposal
    3. 审查通过 → 发布到 Vault + Git commit
    4. 其他 Agent 通过 Namespace 查询
    """
    pass
```

---

## 存储结构（融合三种模式）

```
.learnings/vault/
├── START_HERE.md              # llm-wiki: Agent 入口
├── _agent/
│   ├── START_HERE.md          # llm-wiki: Agent 入口
│   ├── episodic/              # E（近期事件）
│   │   ├── decisions/         # 决策记录
│   │   ├── failures/          # 失败记录
│   │   └── successes/         # 成功记录
│   ├── semantic/              # S（持久事实）
│   │   ├── projects/          # 项目状态
│   │   ├── patterns/          # 模式库
│   │   └── constraints/       # 约束条件
│   └── procedural/            # P（流程知识）
│       ├── skills/            # 已验证的 Skill
│       └── workflows/         # 标准工作流
├── ledger/                    # elfmem: 事件日志（追加不可变）
│   └── 2026-09.jsonl
├── indexes/                   # 可重建的加速层
│   ├── bm25.index
│   ├── vector.index
│   └── graph.index
└── _meta/
    ├── manifest.json          # 源文件哈希清单（llm-wiki drift detection）
    └── drift-report.json      # 漂移检测报告
```

---

## 与现有 L1 记忆系统的关系

| 现有系统 | v2 增强方式 |
|---------|-----------|
| MEMORY.md | 保留为 HOT 层入口，内容指向 vault/semantic/ |
| USER.md | 保留为 IDENTITY 层，永不衰减（PERMANENT） |
| MEMORY_GRAPH.md | 升级为 vault/_meta/graph.index |
| .learnings/LEARNINGS.md | 扩展为 ledger/ + 审计追踪 |
| session-state.md | 保留但增加 tier 标记（WORKING/EPISODIC） |

---

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes/ZCode** | 本项目 .learnings/vault/ 目录 |
| **elfmem** | Python 包直接调用 |
| **memento** | MCP 服务器（跨Agent共享） |
| **llm-wiki** | brain CLI 命令 |
