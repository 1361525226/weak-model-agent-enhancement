# Skill: Context Engineering — 上下文打包与压缩

## 触发条件
上下文窗口紧张、长对话历史、需要注入大量文件信息时。

## 适用场景
- 大文件读取（超过 4000 字符）
- 多文件上下文注入
- 长对话历史管理
- Token 预算敏感任务

## 执行步骤

### Step 1: 文件选择（高信号优先）
按相关度排序，只注入必要文件。

```
选择优先级：
1. 被当前任务直接引用的文件（完整路径）
2. 被选中文件 import 的文件（transitive dependency）
3. 测试文件（同模块）
4. 配置文件（package.json/tsconfig等）
```

### Step 2: 字节截断

```bash
# 前 4000 字符（保留头部）
head -c 4000 "$FILE_PATH"

# 后 4000 字符（保留尾部，适合日志/输出）
tail -c 4000 "$FILE_PATH"

# 关键段落（grep 搜索）
grep -A 20 -B 5 "target_function" "$FILE_PATH"
```

### Step 3: 完整路径引用
在 prompt 中直接写完整路径，省去搜索。

```
❌ 差：找到用户相关的代码
✅ 好：修改 @src/api/handlers/user.go 中的 GetUser 函数

路径格式：
- 相对项目根：@src/path/to/file.ts
- 绝对路径：/e:/项目/xxx/src/config.go
```

### Step 4: LLMLingua 压缩（可选）
对超长上下文进行 perplexity 评估压缩。

```python
# 使用 LLMLingua 压缩 prompt
from llmlingua import PromptCompressor

compressor = PromptCompressor(model_name="facebook/bart-large-cnn")
compressed = compressor.compress(
    prompt="原始长prompt...",
    target_token=1000,  # 目标 token 数
    force_tokens=["<sep>", "\n"]  # 保留的 token
)
```

### Step 5: 会话隔离

```
/new           # 新会话，切断无关历史
/compact       # 压缩当前会话历史
```

### Step 6: 注意力锚点
保留首轮目标和关键决策，滑动窗口丢弃中间。

```
锚点模板：
---
锚点（首条）：{原始目标描述}
锚点（关键决策）：
- 决策1：{decision_1}
- 决策2：{decision_2}
---
当前对话（最近 5 轮）：
{recent_conversation}
```

## 跨平台映射

| 平台 | 实现方式 |
|-----|---------|
| **Agnes** | head/tail 命令 + 完整路径引用 + /new /compact |
| **Aider** | `--mcp-limit 1000`（Repo Map）+ `--compress-context` |
| **LangGraph** | Memory Manager + contextual compression |
| **OpenHands** | 分块 + 摘要管道 |
| **DeerFlow** | 双层内存（工作记忆+归档记忆） |

## 验证标准
- 注入 Token 数 < 上下文窗口的 60%
- 关键文件完整路径在 prompt 中出现
- 截断后仍保留关键信息（前后各 4000 字符）

## 失败处理
- 截断丢失关键信息 → 分多次注入（分段 prompt）
- 压缩后性能下降 → 改用人工选择关键段落
