# Skill: Context Engineering v2 — 基于 llm-wiki + elfmem 交叉进化

## 触发条件
上下文窗口紧张、需要高效检索相关信息、长对话历史管理。

## 来源模式

### 1. elfmem — 内容可寻址 + Volatility Class
- 相同内容只存一份（SHA-256 去重）
- 区分"不再被使用"和"不再真实"
- Weighted tier-aware context packet（预算感知上下文包）

### 2. llm-wiki — Drift Detection + Promote-Candidates
- 源内容哈希 vs 索引一致性检查
- 自动识别晋升候选（高频引用+低龄）
- Obsidian wikilinks 实现关联跳跃

---

## 执行步骤

### Step 1: Context Packet 构建（预算感知）

```python
def build_context_packet(task: str, budget: int = 4000) -> dict:
    """
    构建预算感知的上下文包（elfmem 模式）：
    
    优先级：
      L1_HOT (MEMORY.md + USER.md)       — 总是加载，~2000 tokens
      L2_WARM (vault/semantic/)          — 按需加载，~2000 tokens  
      L3_COLD (vault/episodic/)          — 搜索召回，~1000 tokens
      L4_ARCHIVE                         — 不加载，仅索引
    
    预算分配：
      - 硬上限：budget tokens
      - HOT 层：固定 40%（800 tokens）
      - WARM 层：动态 40%（根据相关性）
      - COLD 层：剩余 20%（检索 Top-K）
    """
    packet = {
        "hot": load_hot_layer(),           # MEMORY.md + USER.md
        "warm": weighted_search(task, tier="warm", budget=0.4),
        "cold": hybrid_retrieve(task, tier="cold", budget=0.2),
        "summary": generate_summary(packet),  # 自引用摘要
    }
    return packet
```

### Step 2: Drift Detection（漂移检测）

```python
def check_drift() -> dict:
    """
    对比源文件哈希与索引哈希，检测漂移（llm-wiki 模式）：
    - MODIFIED: 源文件变化但索引未更新
    - STALE: 源文件未变但内容已过期
    - DELETED: 源文件被删除但索引仍存在
    - ADDED: 新文件但未建立索引
    """
    manifest = json.loads(Path(".learnings/vault/_meta/manifest.json").read_text())
    current_hashes = {}
    for md_file in Path(".learnings/vault").rglob("*.md"):
        current_hashes[str(md_file.relative_to(".learnings/vault"))] = sha256(md_file.read_text())
    
    drifts = []
    for path, expected_hash in manifest.items():
        actual_hash = current_hashes.get(path)
        if actual_hash != expected_hash:
            drifts.append({"path": path, "status": "MODIFIED" if actual_hash else "DELETED"})
    for path in current_hashes:
        if path not in manifest:
            drifts.append({"path": path, "status": "ADDED"})
    
    return {"drifts": drifts, "total_checked": len(manifest) + len(current_hashes)}
```

### Step 3: Promote-Candidates（晋升候选）

```python
def find_promote_candidates() -> list[dict]:
    """
    自动识别应晋升的记忆（llm-wiki + elfmem 融合）：
    - 高频引用（ledger reinforcement count ≥ 5）
    - 低龄（created < 7天前）
    - 未被任何下层覆盖
    """
    candidates = []
    for ledger_entry in read_ledger():
        if ledger_entry["event"] == "reinforce" and ledger_entry["count"] >= 5:
            block = load_block(ledger_entry["block_id"])
            if block.age_days < 7 and block.tier in ("EPHEMERAL", "STANDARD"):
                candidates.append({
                    "path": block.path,
                    "reason": f"reinforced {ledger_entry['count']} times in 7 days",
                    "current_tier": block.tier,
                    "promoted_tier": "DURABLE" if block.category == "project" else "STANDARD",
                })
    return candidates
```

---

## 输出格式

```markdown
## Context Packet Report

**Budget**: 4000 tokens | **Used**: 3200 tokens (80%)

### HOT Layer (固定加载)
- MEMORY.md: 1301 bytes ✅
- USER.md: 471 bytes ✅

### WARM Layer (动态加载)
- vault/semantic/projects/agentic-pipeline.md (score: 0.92) ✅
- vault/semantic/patterns/loop-engineering.md (score: 0.87) ✅

### COLD Layer (搜索召回)
- vault/episodic/failures/LRN-20260915-001.md (score: 0.74) ⚠️ 降级候选

### Drift Status
- 0 MODIFIED, 0 DELETED, 0 ADDED ✅

### Promote Candidates
- vault/semantic/patterns/loop-engineering.md: STANDARD → DURABLE (reinforced 7x)
```
