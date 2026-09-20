# Harness 模块 — Code as Agent Harness

> 基于 Code as Agent Harness (arXiv 2026-05-18) + HarnessRisk (arXiv 2026-08-18)

## 组件

| 文件 | 功能 |
|-----|------|
| `code.py` | 可执行校验器：将 AGENTS.md 规则编译为 7 个检查函数 |
| `scorecard.py` | 质量评分卡：G7 七维审查（安全/正确性/性能/可维护性/测试/可访问性/文档） |

## 用法

```bash
# 校验任务输出
echo "目标：实现认证
文件：@src/auth/jwt.go
验收：go test ./... 通过" | python harness/code.py --task "实现JWT认证"

# 生成评分卡
python harness/scorecard.py
python harness/scorecard.py --json > harness-score.json
```

## 7 项检查

| # | 检查项 | 严重度 | 对应 AGENTS.md 规则 |
|---|-------|-------|------------------|
| 1 | 文件路径引用 | high | 2.1 完整路径 |
| 2 | 意图完整性 | high | 2.4 四要素 |
| 3 | 输出格式 | medium | 4.1/4.2 格式约束 |
| 4 | Loop 约束 | high | 三.3 重试上限+诊断 |
| 5 | 安全护栏 | critical | 6.3 危险操作白名单 |
| 6 | 错误回灌格式 | medium | 5.3 回灌规范 |
| 7 | 字节截断 | medium | 2.2 截断策略 |

## 评分卡 7 维度

| 维度 | 权重 | 评估内容 |
|-----|-----|---------|
| Security | 10 | 危险操作白名单、prompt injection 检测 |
| Correctness | 9 | 验证脚本、Loop 状态管理 |
| Performance | 8 | RPM 策略、上下文优化 |
| Maintainability | 7 | Skill 数量、AGENTS.md 大小 |
| Testing | 9 | 工作流引擎、知识库整合、Harness 校验器 |
| Accessibility | 6 | ZCode Skill 安装数 |
| Documentation | 5 | 关键文档完整性 |
