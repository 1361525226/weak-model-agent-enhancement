# Agnes 免费层 RPM 预算分配策略

> **版本**：v1.0
> **约束**：免费 Agnes 约 20 RPM（公开 30，实际可用约 20）
> **核心思想**：串行优先，时间换性能，Token 省下来投推理

---

## 一、RPM 消耗模型

### 1.1 单次调用成本估算

| 操作 | 平均 Token 输入 | 平均 Token 输出 | 估算 RPM 消耗 |
|-----|---------------|---------------|-------------|
| 简单问答 | 500 | 200 | 1 |
| 代码生成（单文件） | 2000 | 500 | 1 |
| 代码调试（含错误回灌） | 3000 | 800 | 1-2 |
| 设计评审 | 4000 | 1000 | 1-2 |
| Thinking 模式开启 | +1000（思考 token） | +300 | 1-2 |
| 多文件上下文投影 | 4000-8000 | 500 | 1-2 |
| 子 Agent 并行调用 | 每个 1-2 | 累计 | N×1 |

### 1.2 每日预算

```
20 RPM × 60 分钟 × 8 小时 = 9,600 次/天
保守估计：实际可用 ~6,000 次/天（含系统开销）
```

---

## 二、动态预算分配策略

### 2.1 任务分级

| 级别 | 描述 | 预算/任务 | 重试上限 | Thinking |
|-----|------|---------|---------|---------|
| **S**（简单） | 读文件、写小函数、回答问题 | 2-3 次调用 | 1 次 | 关闭 |
| **A**（中等） | 实现一个功能模块 | 5-8 次调用 | 2 次 | 512 tokens |
| **B**（复杂） | 多文件联动、架构设计 | 10-15 次调用 | 3 次 | 1024-2048 tokens |
| **X**（高风险） | 数据库迁移、部署、删文件 | 3-5 次调用 | 1 次 | 立即人工确认 |

### 2.2 每日分配模板

```
总预算：~6000 次/天

S 级任务（占 40%）：  2400 次 → ~800 个简单任务
A 级任务（占 35%）：  2100 次 → ~260 个中等任务
B 级任务（占 20%）：  1200 次 → ~80 个复杂任务
X 级任务（占 5%）：   300 次  → ~60 个高风险任务（人工兜底）
预留缓冲：                    剩下 10% 应对突发
```

### 2.3 实时预算监控

```python
# RPM 预算控制器（伪代码）
class RPMBudget:
    def __init__(self, max_rpm=20, daily_limit=6000):
        self.max_rpm = max_rpm
        self.daily_limit = daily_limit
        self.calls_this_minute = 0
        self.calls_today = 0
        self.minute_window = []

    def can_call(self) -> bool:
        now = time.time()
        # 清理 60 秒前的记录
        self.minute_window = [t for t in self.minute_window if now - t < 60]
        if len(self.minute_window) >= self.max_rpm:
            return False
        if self.calls_today >= self.daily_limit:
            return False
        return True

    def record_call(self):
        self.minute_window.append(time.time())
        self.calls_today += 1
        self.calls_this_minute += 1
```

---

## 三、节省 RPM 的战术

### 3.1 策略一：串行替代并行

```
❌ 低效：同时启动 5 个子 Agent（5 RPM 瞬时消耗）
✅ 高效：串行执行，每次 1 个（1 RPM，总时长稍长但总量不变）
```

### 3.2 策略二：Thinking 按需开启

```python
# 动态开启 Thinking
def should_enable_thinking(task: str) -> bool:
    simple_keywords = ["read", "list", "find", "show", "what is"]
    complex_keywords = ["design", "architect", "debug", "fix", "optimize", "plan"]

    task_lower = task.lower()
    is_simple = any(k in task_lower for k in simple_keywords)
    is_complex = any(k in task_lower for k in complex_keywords)

    if is_simple:
        return False   # 简单任务不开 Thinking
    if is_complex:
        return True    # 复杂任务开 Thinking
    return False       # 默认不开
```

### 3.3 策略三：Context 压缩先行

```
# 在调用模型前先压缩上下文
# 效果：输入 Token 减少 50-70%，同等 RPM 下可做更多任务

before:  "@src/api/handlers/user.go 中实现 GetUser 函数"
        → Agnes 需要扫描整个文件

after:  "文件 @src/api/handlers/user.go 第 45-78 行，实现 GetUser"
        → Agnes 直接定位，节省搜索 Token
```

### 3.4 策略四：失败快速降级

```python
# 三级降级策略
def execute_with_fallback(task, max_retries=3):
    # Level 1: 单轮生成（最快，最省）
    result = single_shot(task)
    if result.success:
        return result

    # Level 2: Loop 重试（中等）
    for i in range(max_retries):
        result = loop_retry(task, attempt=i)
        if result.success:
            return result

    # Level 3: 升级到人（保底）
    return escalate_to_human(task, result.error)
```

### 3.5 策略五：会话隔离避免历史污染

```
# 每个原子任务独立会话
/new                    # 新会话，历史清零
执行任务...
/compact                # 压缩为摘要
下一个任务 /new         # 再次隔离
```

**效果**：避免历史累积导致的 Token 浪费和 context rot。

---

## 四、RPM 监控仪表板（本地脚本）

```python
# rpm_monitor.py — 本地 RPM 监控
# 用法：python rpm_monitor.py --watch

import time
import json
from pathlib import Path

LOG_FILE = Path.home() / ".agnes" / "rpm_log.jsonl"

def log_call(rpm_level: str, task_type: str, tokens_in: int = 0):
    entry = {
        "ts": time.time(),
        "rpm_level": rpm_level,
        "task_type": task_type,
        "tokens_in": tokens_in,
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def get_minute_rate():
    """计算当前分钟的调用次数"""
    now = time.time()
    one_min_ago = now - 60
    count = 0
    if LOG_FILE.exists():
        for line in LOG_FILE.read_text().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry["ts"] > one_min_ago:
                    count += 1
            except:
                pass
    return count

def get_daily_total():
    """今日总调用次数"""
    today = time.strftime("%Y-%m-%d")
    count = 0
    if LOG_FILE.exists():
        for line in LOG_FILE.read_text().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if time.strftime("%Y-%m-%d", time.localtime(entry["ts"])) == today:
                    count += 1
            except:
                pass
    return count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="实时监控 RPM")
    parser.add_argument("--report", action="store_true", help="生成日报")
    args = parser.parse_args()

    if args.watch:
        print("📊 RPM 监控（Ctrl+C 退出）")
        print(f"{'时间':<12} {'当前RPM':<10} {'今日累计':<10} {'状态':<10}")
        print("-" * 45)
        while True:
            rpm = get_minute_rate()
            daily = get_daily_total()
            status = "⚠️ 限制" if rpm >= 18 else ("⏳ 注意" if rpm >= 15 else "✅ 正常")
            ts = time.strftime("%H:%M:%S")
            print(f"{ts:<12} {rpm:<10} {daily:<10} {status:<10}")
            time.sleep(5)
    elif args.report:
        daily = get_daily_total()
        print(f"📈 今日已用 RPM：{daily}")
        print(f"💡 剩余预算：{6000 - daily}（预估）")
```

---

## 五、RPM 紧急处理

### 5.1 触发限速时

```
1. 立即停止所有后台 Agent（Agent 工具取消）
2. 等待 60 秒让 RPM 窗口清空
3. 优先执行 S/A 级任务
4. B/X 级任务延后
```

### 5.2 预防性节流

```python
# 在每个 Agnes prompt 前检查
if rpm_monitor.get_minute_rate() >= 15:
    print("⚠️ RPM 接近上限，等待冷却...")
    time.sleep(60 - rpm_monitor.last_call_age())
```

---

## 六、关键原则

1. **串行 > 并行**：20 RPM 下并行会快速耗尽
2. **简单任务不花钱**：S 级任务尽量在单轮内完成
3. **Thinking 留给硬骨头**：复杂任务才开 Thinking
4. **历史及时清理**：`/new` 和 `/compact` 是 RPM 的好朋友
5. **失败快速降级**：3 次失败就升级，不要空转
