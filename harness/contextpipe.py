#!/usr/bin/env python3
"""
contextpipe.py — 数据库启发的上下文组装管道

参考：ContextPipe (arXiv 2026-09) — Database-Inspired Context Assembly for Long-Horizon Agents

核心思想：
  将上下文视为"数据库查询结果"——不是把整个仓库喂给 Agent，
  而是根据当前任务动态组装最相关的上下文片段。
  类比 SQL：SELECT 相关片段 FROM context WHERE relevance > threshold

与现有 context-kernel.py 的关系：
  context-kernel.py = 文件级投影（选哪些文件）
  contextpipe.py    = 片段级组装（选文件的哪些部分 + 组装顺序）
"""
import re
import sys
from pathlib import Path
from typing import Optional


# ============================================================================
# 上下文分片
# ============================================================================

class ContextChunk:
    """上下文章节"""
    def __init__(self, source: str, content: str, relevance: float = 0.0,
                 chunk_type: str = "unknown", line_range: tuple = None):
        self.source = source
        self.content = content
        self.relevance = relevance
        self.chunk_type = chunk_type  # "code", "config", "test", "doc", "error"
        self.line_range = line_range  # (start, end)

    def to_dict(self):
        return {
            "source": self.source,
            "type": self.chunk_type,
            "relevance": self.relevance,
            "lines": self.line_range,
            "content_preview": self.content[:100] + "..." if len(self.content) > 100 else self.content,
        }


# ============================================================================
# 上下文检索器
# ============================================================================

class ContextRetriever:
    """从项目中检索相关上下文片段"""

    def __init__(self, project_root: Path, max_chunks: int = 10, max_tokens_per_chunk: int = 800):
        self.project_root = project_root
        self.max_chunks = max_chunks
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self._index: dict = {}  # file_path -> list of chunks

    def index_file(self, file_path: Path):
        """索引单个文件为 chunks"""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        chunks = []
        lines = content.split('\n')

        # 按函数/类分块
        current_chunk = []
        current_type = "code"
        chunk_start = 0

        for i, line in enumerate(lines):
            # 检测代码结构边界
            if re.match(r'^def\s+\w+', line) or re.match(r'^class\s+\w+', line):
                if current_chunk:
                    chunks.append(self._make_chunk(
                        file_path, current_chunk, chunk_start, i, current_type
                    ))
                current_chunk = [line]
                chunk_start = i
                current_type = "code"
            elif line.strip().startswith('#') and not line.strip().startswith('#!'):
                current_type = "doc"
                current_chunk.append(line)
            else:
                current_chunk.append(line)

        if current_chunk:
            chunks.append(self._make_chunk(
                file_path, current_chunk, chunk_start, len(lines), current_type
            ))

        self._index[str(file_path)] = chunks

    def _make_chunk(self, path: Path, lines: list, start: int, end: int, chunk_type: str) -> ContextChunk:
        content = '\n'.join(lines)
        # 截断到 token 限制
        if len(content) > self.max_tokens_per_chunk * 4:
            content = content[:self.max_tokens_per_chunk * 4] + "\n# ...[truncated]"
        return ContextChunk(
            source=str(path.relative_to(self.project_root)),
            content=content,
            chunk_type=chunk_type,
            line_range=(start + 1, end),
        )

    def search(self, query: str, top_k: int = None) -> list:
        """根据查询检索相关上下文"""
        top_k = top_k or self.max_chunks
        query_lower = query.lower()

        # 关键词匹配
        scored = []
        for file_path, chunks in self._index.items():
            for chunk in chunks:
                score = 0.0
                # 文件名匹配
                if query_lower in file_path.lower():
                    score += 3.0
                # 内容匹配
                content_lower = chunk.content.lower()
                for word in query_lower.split():
                    if word in content_lower:
                        score += 1.0
                # 类型匹配
                if chunk.chunk_type == "code" and any(k in query_lower for k in ["function", "def", "class", "实现"]):
                    score += 1.0
                elif chunk.chunk_type == "test" and any(k in query_lower for k in ["test", "测试", "验证"]):
                    score += 1.5

                if score > 0:
                    scored.append((score, chunk))

        # 排序取 top_k
        scored.sort(key=lambda x: -x[0])
        return [chunk for _, chunk in scored[:top_k]]

    def assemble(self, query: str, max_tokens: int = 4000) -> str:
        """组装上下文"""
        chunks = self.search(query, top_k=self.max_chunks)
        assembled = []
        total_tokens = 0

        for chunk in chunks:
            chunk_tokens = len(chunk.content) // 4  # 粗略估算
            if total_tokens + chunk_tokens > max_tokens:
                break
            assembled.append(f"## {chunk.source}:{chunk.line_range[0]}-{chunk.line_range[1]} [{chunk.chunk_type}]\n{chunk.content}")
            total_tokens += chunk_tokens

        return "\n\n---\n\n".join(assembled)


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ContextPipe — 数据库启发的上下文组装")
    parser.add_argument("query", help="查询关键词")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--max-tokens", type=int, default=4000, help="最大 Token 数")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    retriever = ContextRetriever(root)

    # 索引项目文件
    for pattern in ["*.py", "*.go", "*.ts", "*.tsx", "*.js", "*.jsx", "*.rs", "*.sql", "*.md"]:
        for f in root.rglob(pattern):
            if any(x in str(f) for x in ["node_modules", ".git", "__pycache__", "venv"]):
                continue
            retriever.index_file(f)

    print(f"索引了 {len(retriever._index)} 个文件")

    # 检索并组装
    result = retriever.assemble(args.query, args.max_tokens)

    if args.json:
        import json
        print(json.dumps({"query": args.query, "context": result, "tokens_estimated": len(result)//4},
                        ensure_ascii=False, indent=2))
    else:
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
