# Skill: Multi-Agent Collaboration — 多 Agent 协作

## 触发条件
复杂任务需要多视角、辩论共识、或分工执行时。

## 适用场景
- 复杂架构设计
- 代码审查（多视角）
- 辩论式决策
- 大规模功能开发

## 执行步骤

### Step 1: 辩论式共识机制（pattern_052）

```python
# 多立场 Agent 辩论
def debate_consensus(query: str, positions: list[str]) -> dict:
    # 1. 每个立场独立分析
    analyses = {}
    for pos in positions:
        analyses[pos] = generate_analysis(query, pos)
    
    # 2. 结构化辩论（多轮）
    for round_num in range(3):
        for pos in positions:
            counter_args = get_counter_arguments(analyses, exclude=pos)
            analyses[pos] = rebut(analyses[pos], counter_args)
    
    # 3. 裁判 Agent 综合决策
    final = judge_debate(analyses, query)
    return {
        "decision": final["choice"],
        "confidence": final["confidence"],
        "reasoning": final["justification"],
        "positions": analyses
    }

# 裁判 prompt
JUDGE_PROMPT = """
任务：{query}
各方观点：
{positions}

请综合各方观点，做出决策并说明理由。
考虑因素：正确性、性能、可维护性、安全性。
"""
```

### Step 2: Supervisor-Worker 双层分工（pattern_090）

```python
# Supervisor 负责规划与验证
# Worker 负责执行具体任务
class SupervisorWorker:
    def __init__(self, supervisor_model, worker_models):
        self.supervisor = supervisor_model  # 强模型
        self.workers = worker_models        # 弱模型
    
    def execute(self, task: str) -> dict:
        # 1. Supervisor 规划
        plan = self.supervisor.plan(task)
        
        # 2. 分配给 Worker
        results = {}
        for subtask in plan:
            worker = self.workers[subtask.role]
            results[subtask.id] = worker.execute(subtask)
        
        # 3. Supervisor 验证
        verification = self.supervisor.verify(results)
        
        # 4. 修复失败项
        for result_id, result in results.items():
            if not result["success"]:
                fixed = self.supervisor.fix(result)
                results[result_id] = fixed
        
        return results
```

### Step 3: Agent Handoff 优雅移交（pattern_091）

```python
# 弱模型遇到能力边界时移交给强模型
class AgentHandoff:
    def __init__(self, weak_agent, strong_agent):
        self.weak = weak_agent
        self.strong = strong_agent
    
    def run(self, query: str) -> dict:
        # 弱模型先试
        result = self.weak.execute(query)
        
        # 置信度评估
        confidence = self.weak.estimate_confidence(result)
        
        if confidence < 0.7:
            # 移交给强模型
            result = self.strong.execute(query)
            return {
                "result": result,
                "handoff": True,
                "reason": f"low confidence: {confidence}"
            }
        
        return {
            "result": result,
            "handoff": False,
            "reason": None
        }
```

### Step 4: 任务分发模板

```markdown
## 多 Agent 任务分发
1. 识别任务类型（简单/复杂/需辩论）
2. 简单任务 → 单 Agent 执行
3. 复杂任务 → Supervisor 分解 + Worker 执行
4. 争议任务 → 多立场辩论 + 裁判决策
5. 超出能力 → Handoff 升级到强模型
```

### Step 5: 协作协议（A2A）

```python
# Agent-to-Agent 通信协议
class A2AProtocol:
    def __init__(self):
        self.tasks = {}
        self.results = {}
    
    def dispatch(self, agent_id: str, task: dict) -> str:
        task_id = generate_id()
        self.tasks[task_id] = {
            "agent": agent_id,
            "task": task,
            "status": "pending"
        }
        return task_id
    
    def receive_result(self, task_id: str, result: dict):
        self.results[task_id] = result
        self.tasks[task_id]["status"] = "completed"
    
    def wait_for(self, task_ids: list[str]) -> dict:
        while not all(
            self.tasks[tid]["status"] == "completed" 
            for tid in task_ids
        ):
            time.sleep(0.1)
        return {tid: self.results[tid] for tid in task_ids}
```

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | Agent 工具多子 Agent 并行 + run_in_background |
| **Agno** | SubAgent + handoff 机制 |
| **LangGraph** | SubGraph + conditional edges |
| **OpenHands** | Multi-agent 架构 |
| **DeerFlow** | Supervisor + SubAgent（原生支持）|
| **CAMEL** | 多 Agent 角色扮演辩论 |

## 验证标准
- 多 Agent 任务完成率 > 单 Agent 的 1.5 倍
- 辩论共识决策质量 > 单立场决策
- Handoff 率 < 30%（大部分任务弱模型应能处理）

## 失败处理
- Agent 间通信失败 → 重试 + 超时降级
- 辩论僵局 → 裁判强制决策
- 超出所有 Agent 能力 → 升级到人
