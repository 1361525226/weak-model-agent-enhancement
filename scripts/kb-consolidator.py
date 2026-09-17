#!/usr/bin/env python3
"""kb-consolidator.py — 知识库交叉进化整合器

聚合 arXiv:2507.21046 / MemSkill arXiv:2602.02474 / G1 门控，
将分散模式合并为高密度元模式。Agnes 可重复运行。
"""
import argparse, json, re, sys, unicodedata
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

META_DOMAINS = OrderedDict([
    ("记忆与状态", ["agent-memory-system","memory_system"]),
    ("协作与编排", ["agent_coordination","agent_protocol","architecture"]),
    ("护栏与安全", ["agent_harness","security","rule_engine"]),
    ("上下文与检索", ["context_management","long_context_attention",
                       "long_context_compression","rag_enhancement","multimodal_rag"]),
    ("推理与提示进化", ["reasoning_strategy","prompt_engineering",
                        "prompt_evolution","self_improvement"]),
    ("推理加速与部署", ["inference_acceleration","ai-inference-optimization",
                        "quantization","speculative_decoding","model_compression",
                        "model_distribution","edge-computing","edge_ai",
                        "edge_deployment","mobile_inference","neuromorphic",
                        "neuromorphic_computing","边缘AI","attention_mechanism","optimization"]),
    ("评测与观测", ["evaluation","testing","observability"]),
    ("模型训练与蒸馏", ["model_finetuning","fine_tuning","training_stability",
                        "distributed_training","embedding_training",
                        "knowledge_distillation","knowledge_transfer",
                        "synthetic_data","model_architecture","automl","data-pipeline"]),
    ("模型路由与成本", ["model_router"]),
    ("研发流程", ["development_workflow","code_review","code_understanding",
                 "code_generation","debugging","project_management",
                 "documentation","content_generation","output_control"]),
    ("工具与技能生态", ["tool_ecosystem","tool_reliability","skill_management",
                        "browser_automation","ai_engineering","data_storage","research"]),
    ("多模态与感知", ["multimodal","multimodal_fusion","multimodal_optimization",
                      "computer-vision","natural-language-processing",
                      "explainable-ai","real-time-streaming"]),
    ("专用领域", ["algorithm","blockchain-ai","quantum-computing","robotics-ai"]),
])
CAT_DOM = {}
for dom, cats in META_DOMAINS.items():
    for c in cats:
        CAT_DOM[c] = dom

STOP = {"模式","pattern","system","method","framework","架构","strategy","策略","的","与","和"}

def norm(name):
    s = re.sub(r'[（(].*?[)）]', ' ', name)
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'[^\w\u4e00-\u9fff]+', ' ', s)
    return ' '.join(t.lower() for t in s.split() if t.lower() not in STOP and len(t) > 0)

def bigrams(s):
    s = s.replace(' ', '')
    return {s[i:i+2] for i in range(max(0, len(s)-1))} if len(s) >= 2 else ({s} if s else set())

def jacc(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def similar(n1, n2, thr):
    t1, t2 = norm(n1), norm(n2)
    if not t1 or not t2:
        return False
    a, b = (t1, t2) if len(t1) <= len(t2) else (t2, t1)
    if len(a) >= 4 and a in b:
        return True
    return jacc(bigrams(a), bigrams(b)) >= thr

class P:
    __slots__ = ['pid','name','cat','src','stars','desc','benefit','code','origin']
    def __init__(self):
        self.pid = self.name = self.cat = self.src = self.stars = ''
        self.desc = self.benefit = self.code = ''
        self.origin = 'v48'

def last_cat(patterns, lines, idx):
    for j in range(idx - 1, -1, -1):
        m = re.match(r'^## 类别:\s*(\S+)', lines[j])
        if m:
            return m.group(1)
    return 'unknown'

def parse_v48(text):
    ps, cur, field, inc = [], None, None, False
    lines = text.split('\n')
    for i, line in enumerate(lines):
        m = re.match(r'^## 类别:\s*(\S+)\s*\((\d+)\s*个模式\)', line)
        if m:
            if cur:
                ps.append(cur)
            cur = P(); cur.cat = m.group(1); field = None; inc = False
            continue
        if not cur:
            continue
        m = re.match(r'^### (.+)$', line)
        if m and not line.startswith('####'):
            if cur.name:
                ps.append(cur)
                cur = P(); cur.cat = last_cat(ps, lines, i)
            cur.name = m.group(1).strip(); field = None; inc = False
            continue
        m = re.match(r'^\|\s*ID\s*\|\s*(pattern_\d+)\s*\|', line)
        if m and not cur.pid:
            cur.pid = m.group(1); continue
        m = re.match(r'^\|\s*来源\s*\|\s*(.+?)\s*\|', line)
        if m and not cur.src:
            cur.src = m.group(1); continue
        m = re.match(r'^\|\s*Stars\s*\|\s*(.+?)\s*\|', line)
        if m and not cur.stars:
            cur.stars = m.group(1); continue
        if line.startswith('**描述:**') or line.startswith('**描述**'):
            field = 'desc'; continue
        if line.startswith('**弱模型收益:**') or line.startswith('**弱模型收益**'):
            field = 'benefit'; continue
        if line.strip().startswith('```'):
            if inc:
                inc = False; field = None
            elif cur.name and (cur.desc or cur.benefit):
                inc = True
            continue
        if inc:
            cur.code += line + '\n'
            continue
        if field == 'desc' and line.strip() and not line.startswith('|') and not line.startswith('#'):
            cur.desc += line.strip() + '\n'
        elif field == 'benefit' and line.strip() and not line.startswith('|') and not line.startswith('#'):
            cur.benefit += line.strip() + '\n'
    if cur and cur.name:
        ps.append(cur)
    return ps

def parse_inc(text):
    ps, cur, field, inc = [], None, None, False
    for line in text.split('\n'):
        m = re.match(r'^## (pattern_\d+)\s*-\s*(.+)$', line)
        if m:
            if cur:
                ps.append(cur)
            cur = P(); cur.pid = m.group(1); cur.name = m.group(2).strip()
            cur.origin = 'incremental'; cur.cat = ''; field = None; inc = False
            continue
        if not cur:
            continue
        if line.startswith('- **来源**:') or line.startswith('- **来源**:'):
            cur.src = line.split(':', 1)[1].strip() if ':' in line else ''
            continue
        if line.startswith('- **类别**:') or line.startswith('- **类别**:'):
            cur.cat = line.split(':', 1)[1].strip() if ':' in line else ''
            continue
        if line.startswith('- **Stars**:') or line.startswith('- **Stars**:'):
            cur.stars = line.split(':', 1)[1].strip() if ':' in line else ''
            continue
        if line.startswith('**描述**'):
            field = 'desc'; inc = False; continue
        if line.startswith('**弱模型收益**'):
            field = 'benefit'; inc = False; continue
        if line.strip().startswith('```'):
            if inc:
                inc = False; field = None
            else:
                inc = True
            continue
        if inc:
            cur.code += line + '\n'
            continue
        if field == 'desc' and line.strip():
            cur.desc += line.strip() + '\n'
        elif field == 'benefit' and line.strip():
            cur.benefit += line.strip() + '\n'
    if cur and cur.name:
        ps.append(cur)
    return ps

def merge_group(g):
    p0 = max(g, key=lambda x: len(norm(x.name)))
    return {
        'title': p0.name,
        'ids': [p.pid for p in g if p.pid],
        'member_count': len(g),
        'members': [p.name for p in g],
        'origins': sorted({p.origin for p in g}),
        'categories': sorted({p.cat for p in g if p.cat}),
        'sources': sorted({p.src for p in g if p.src and p.src != 'N/A'})[:5],
        'stars_max': next((p.stars for p in g if p.stars and p.stars != 'N/A'), ''),
        'desc': ' '.join(s for p in g for s in [p.desc, p.benefit]
                        for x in re.split(r'(?<=[。.!?！？\n])\s*', s) if x.strip()),
        'benefit': '',
        'code': max((p.code for p in sorted(g, key=lambda x: -len(x.code))), default=''),
    }

def consolidate(patterns, threshold):
    by_dom = {d: [] for d in META_DOMAINS}
    unmapped = []
    for p in patterns:
        d = CAT_DOM.get(p.cat)
        (by_dom[d] if d else unmapped).append(p)
    result, stats = [], {}
    for dom, plist in by_dom.items():
        if not plist:
            stats[dom] = {'before': 0, 'after': 0}
            continue
        clusters = []
        for p in sorted(plist, key=lambda x: -len(norm(x.name))):
            placed = False
            for c in clusters:
                if any(similar(p.name, m.name, threshold) for m in c):
                    c.append(p); placed = True; break
            if not placed:
                clusters.append([p])
        for c in clusters:
            result.append((dom, merge_group(c)))
        stats[dom] = {'before': len(plist), 'after': len(clusters)}
    for p in unmapped:
        result.append(('未分类', merge_group([p])))
    stats['未分类'] = {'before': len(unmapped), 'after': len(unmapped)}
    return result, stats

def render(mps, stats, threshold):
    tb = sum(s['before'] for s in stats.values())
    ta = sum(s['after'] for s in stats.values())
    comp = round(100 - ta / max(tb, 1) * 100)
    L = []
    L.append('# 知识库交叉进化整合版 v1.0')
    L.append('')
    L.append('> 生成时间：' + datetime.now().isoformat())
    L.append('> 方法论：arXiv:2507.21046 x MemSkill arXiv:2602.02474 x G1 门控')
    L.append('> 工具：`scripts/kb-consolidator.py --threshold ' + str(threshold) + '` (Agnes 可重复运行)')
    L.append('')
    L.append('## 整合统计')
    L.append('')
    L.append('| 指标 | 值 |')
    L.append('|-----|-----|')
    L.append('| 原始模式数 | ' + str(tb) + ' |')
    L.append('| 整合后元模式数 | **' + str(ta) + '** |')
    L.append('| 压缩率 | **' + str(comp) + '%** |')
    L.append('| 元域数 | 13（原 74 类别）|')
    L.append('')
    L.append('| 元域 | 整合前 | 整合后 |')
    L.append('|-----|-------|-------|')
    for d, s in stats.items():
        if s['before']:
            L.append('| ' + d + ' | ' + str(s['before']) + ' | ' + str(s['after']) + ' |')
    L += ['', '---', '', '## 元模式详情', '']
    by_dom = {}
    for d, mp in mps:
        by_dom.setdefault(d, []).append(mp)
    for d, mps_d in by_dom.items():
        L.append('')
        L.append('### 元域：' + d + '（' + str(len(mps_d)) + ' 个元模式）')
        L.append('')
        for mp in mps_d:
            note = ' <- 合并 ' + str(mp['member_count']) + ' 个模式' if mp['member_count'] > 1 else ''
            L += ['', '# ' + mp['title'] + note, '', '- **ID**：' + ', '.join(mp['ids'])]
            if mp['origins']:
                L.append('- **来源版本**：' + ', '.join(mp['origins']))
            if mp['categories']:
                L.append('- **原类别**：' + ', '.join(mp['categories']))
            if mp['sources']:
                L.append('- **来源项目**：' + '; '.join(mp['sources']))
            if mp['stars_max']:
                L.append('- **最高 Stars**：' + mp['stars_max'])
            if mp['desc']:
                L += ['', '**描述**：' + mp['desc'][:600]]
            if mp['benefit']:
                L += ['', '**弱模型收益**：' + mp['benefit'][:400]]
            if mp['code'].strip():
                code = mp['code'].strip()
                if len(code) > 800:
                    code = code[:800] + ' # ...(完整代码见原始知识库对应 ID)'
                lang = 'python' if 'def ' in code or 'import ' in code else ''
                L += ['', '```' + lang, code, '```']
    L.append('')
    return '\n'.join(L)

def main():
    pa = argparse.ArgumentParser(description='知识库交叉进化整合器')
    pa.add_argument('--v48', default=str(ROOT / 'trae_kb_v48.md'))
    pa.add_argument('--inc', default=str(ROOT / 'trae_kb_incremental.md'))
    pa.add_argument('--out', default=str(ROOT / 'docs/kb-consolidated.md'))
    pa.add_argument('--index', default=str(ROOT / 'docs/kb-meta-index.json'))
    pa.add_argument('--threshold', type=float, default=0.45)
    args = pa.parse_args()

    v48p = Path(args.v48)
    if not v48p.exists():
        print('ERROR: 找不到主知识库: ' + str(v48p))
        print('  从 git 恢复: git show 3f8a557:trae_kb_v48.md > trae_kb_v48.md')
        return 1

    patterns = parse_v48(v48p.read_text(encoding='utf-8'))
    n_v48 = len(patterns); n_inc = 0
    incp = Path(args.inc)
    if incp.exists() and incp.stat().st_size > 0:
        inc = parse_inc(incp.read_text(encoding='utf-8'))
        v48ids = {p.pid for p in patterns}
        inc = [p for p in inc if p.pid not in v48ids]
        patterns.extend(inc); n_inc = len(inc)
    print('解析完成: v48=' + str(n_v48) + ', 增量=' + str(n_inc) + ', 合计=' + str(len(patterns)))

    mps, stats = consolidate(patterns, args.threshold)
    tb = sum(s['before'] for s in stats.values())
    ta = sum(s['after'] for s in stats.values())
    comp = round(100 - ta / max(tb, 1) * 100)
    print('整合: ' + str(tb) + ' -> ' + str(ta) + ' (' + str(comp) + '% 压缩, threshold=' + str(args.threshold) + ')')

    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(render(mps, stats, args.threshold), encoding='utf-8')
    print('输出: ' + str(outp))

    idx = {'generated_at': datetime.now().isoformat(), 'threshold': args.threshold,
           'total_before': tb, 'total_after': ta,
           'meta_domains': list(META_DOMAINS.keys()),
           'meta_patterns': [{'domain': d, 'title': mp['title'], 'ids': mp['ids'],
                              'member_count': mp['member_count']} for d, mp in mps]}
    idxp = Path(args.index); idxp.parent.mkdir(parents=True, exist_ok=True)
    idxp.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding='utf-8')
    print('索引: ' + str(idxp))

    rl = ROOT / '.loop/run-log.md'
    if rl.exists():
        with open(rl, 'a', encoding='utf-8') as f:
            f.write('\n## kb-consolidator — 交叉进化整合\n\n')
            f.write('**时间**: ' + datetime.now().isoformat() + '\n')
            f.write('**结果**: ' + str(tb) + ' 模式 -> ' + str(ta) + ' 元模式 (压缩 ' + str(comp) + '%)\n\n---\n\n')
    return 0

if __name__ == '__main__':
    sys.exit(main())
