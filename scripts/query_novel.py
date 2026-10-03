#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《无职转生：人生模拟器》全景小说原文与外传语料超能全文检索 CLI 工具 (v2.0 智能增强版)
===================================================================================
功能特性：
1. 毫秒级双库联搜：对 228 万字正传 + 90 万字外传/特典语料进行极速检索（平均耗时 < 80ms）；
2. 多关键词 AND 共现检索：支持空格/逗号/加号分隔多词（如「艾莉丝 妻子」「龙神 诅咒」），
   默认在段落滑动窗口内共现匹配，彻底解决译文断行导致的单行失配问题；
3. 智能中文长短语降级：长短语（如「成为第三位妻子」）无字面全等时，自动剥离语法虚词、
   提取核心专有名词与词组（如【第三位】+【妻子】）进行段落共现检索，杜绝 Agent 检索抓瞎；
4. 语义相关度排序：同行动词紧邻 > 同段邻行共现 > 远距共现，最高相关度章节优先置顶；
5. 精准高亮与片段呈现：匹配行以「>>」指示并用【关键词】高亮，附带真实上下文行号；
6. 对白精细提取：支持 --dialogue 专搜台词「……」与心声『……』；
7. 100% 向下兼容：保持原 CLI 参数与 JSON 输出结构规范完全一致。
"""

import os
import sys
import re
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_CORPUS_DIR = os.path.join(BASE_DIR, 'corpus', 'web_novel')
GAIDEN_CORPUS_DIR = os.path.join(BASE_DIR, 'corpus', 'gaiden')

WEB_MANIFEST_PATH = os.path.join(WEB_CORPUS_DIR, 'chapter_manifest.json')
GAIDEN_MANIFEST_PATH = os.path.join(GAIDEN_CORPUS_DIR, 'gaiden_manifest.json')

# 常用多字虚词/连词/语法词
MULTI_STOPWORDS = [
    '成为', '成了', '作为', '并且', '或者', '因为', '所以', '但是', '如果', '虽说',
    '一个', '一位', '一只', '一件', '一条', '什么', '怎么', '怎样', '为什么', '如何', '哪里',
    '非常', '十分', '真的', '更加', '觉得', '感觉', '没有', '没法', '不能', '不可',
    '为了', '关于', '对于', '由于', '哪怕', '哪怕是', '就是', '还是', '之后', '之前'
]

# 纯语法助词/介词（仅用于首尾安全剥离，绝不收录实词词根如'最'、'更'、'真'、'看'、'听'等）
PURE_PARTICLES = set('的了着过得地在于从向对被把将给由让和与跟同及且或啊呀呢吧吗么')

# 助词/连词正则切分器（用于将长句自然打散为词块，例如 "最后的报酬" -> "最后" + "报酬"）
PARTICLE_SPLIT_REGEX = re.compile(
    r'[\s,，+＋、/|·\-—]+|' + '|'.join(re.escape(w) for w in sorted(MULTI_STOPWORDS + list('的之与和及在于从向对被把将给由让了着过得地啊呀呢吧吗么'), key=len, reverse=True))
)

# 无职转生高频专有名词词典（加速精准切分）
KNOWN_ENTITIES = [
    '鲁迪乌斯', '卢迪乌斯', '鲁迪', '卢迪', '洛琪希', '希露菲叶特', '希露菲', '艾莉丝', '保罗',
    '塞妮丝', '莉莉雅', '诺伦', '爱夏', '奥尔斯帝德', '龙神', '人神', '奇希莉卡', '基列奴',
    '瑞杰路德', '札诺巴', '克里夫', '艾莉娜丽洁', '佩尔基乌斯', '阿托菲', '斗神', '剑神',
    '水神', '北神', '技神', '魔神', '冥王', '蓝道夫', '维妲', '拉普拉斯', '魔导铠', '预知眼',
    '妻子', '丈夫', '结婚', '婚礼', '求婚', '怀孕', '出生', '死亡', '陵墓', '转生', '召唤', '转移',
    '白房间', '诅咒', '豪雷', '圣级', '王级', '帝级', '神级', '七大列强', '狂剑王', '剑王',
    '第一位', '第二位', '第三位', '第三个', '大老婆', '二老婆', '三老婆', '魔力灾害', '转移事件',
    '爱丽丝', '菲利普', '绍罗斯', '希露菲', '阿斯拉', '米里斯', '贝卡利特', '魔大陆'
]

def load_manifest(scope: str = "web") -> List[Dict[str, Any]]:
    """加载章节清单 (scope: 'web', 'gaiden', 'all')"""
    entries = []
    
    if scope in ("web", "all"):
        if os.path.exists(WEB_MANIFEST_PATH):
            with open(WEB_MANIFEST_PATH, 'r', encoding='utf-8') as fp:
                web_items = json.load(fp)
                for item in web_items:
                    item['_scope'] = 'web'
                    item['_base_dir'] = WEB_CORPUS_DIR
                    entries.append(item)
                    
    if scope in ("gaiden", "all"):
        if os.path.exists(GAIDEN_MANIFEST_PATH):
            with open(GAIDEN_MANIFEST_PATH, 'r', encoding='utf-8') as fp:
                gaiden_items = json.load(fp)
                for item in gaiden_items:
                    item['_scope'] = 'gaiden'
                    item['_base_dir'] = GAIDEN_CORPUS_DIR
                    # 字段对齐规范化
                    item['id'] = item.get('chapter_id', 0)
                    item['volume'] = item.get('series', '')
                    item['volume_num'] = item.get('chapter_id', 0)
                    item['relative_path'] = item.get('rel_path', '')
                    item['light_novel_vol'] = item.get('canonical_status', '外传')
                    entries.append(item)
                    
    return entries

def read_chapter_content(manifest_entry: Dict[str, Any]) -> str:
    """读取章节完整 Markdown 内容"""
    base_dir = manifest_entry.get('_base_dir', WEB_CORPUS_DIR)
    fpath = os.path.join(base_dir, manifest_entry['relative_path'])
    if not os.path.exists(fpath):
        return ""
    with open(fpath, 'r', encoding='utf-8') as fp:
        return fp.read()

def strip_stopwords(s: str) -> str:
    """仅剥离真正的语法虚词，不伤害包含'最/更/极/想'等实词词根的词汇"""
    s = s.strip()
    changed = True
    while changed and len(s) > 1:
        changed = False
        for mw in MULTI_STOPWORDS:
            if s.startswith(mw):
                s = s[len(mw):].strip()
                changed = True
            if s.endswith(mw):
                s = s[:-len(mw)].strip()
                changed = True
        if s and s[0] in PURE_PARTICLES:
            s = s[1:].strip()
            changed = True
        if len(s) > 1 and s[-1] in PURE_PARTICLES:
            s = s[:-1].strip()
            changed = True
    return s

def parse_query(raw_query: str) -> Tuple[List[str], bool]:
    """解析检索词，返回 (tokens, is_explicit_multi)"""
    raw_query = raw_query.strip()
    # 提取引号内精确词组
    quoted = re.findall(r'[\"“]([^\"”]+)[\"”]', raw_query)
    unquoted = re.sub(r'[\"“][^\"”]+[\"”]', ' ', raw_query)
    
    tokens = [q.strip() for q in quoted if q.strip()]
    raw_tokens = re.split(r'[\s,，+＋、/|]+', unquoted)
    for t in raw_tokens:
        t = t.strip()
        if t:
            tokens.append(t)
            
    is_multi = len(tokens) > 1
    if not tokens and raw_query:
        tokens = [raw_query]
    return tokens, is_multi

def smart_decompose(query: str) -> Tuple[str, List[str]]:
    """长句智能降级拆解：返回 (词干优化短语, 核心实体/语义块列表)"""
    cleaned = strip_stopwords(query)
    found_entities = []
    temp = cleaned
    for entity in sorted(KNOWN_ENTITIES, key=len, reverse=True):
        if entity in temp:
            found_entities.append(entity)
            temp = temp.replace(entity, ' ')
            
    parts = PARTICLE_SPLIT_REGEX.split(temp)
    for p in parts:
        p = strip_stopwords(p)
        if p and p not in found_entities:
            if len(p) >= 2 or (len(p) == 1 and p in '剑魔枪铠神'):
                found_entities.append(p)
                
    # 若专名切分不足2个词，尝试直接按语法助词切分原始 query
    if len(found_entities) < 2:
        parts_direct = PARTICLE_SPLIT_REGEX.split(cleaned)
        direct_tokens = [p.strip() for p in parts_direct if len(p.strip()) >= 2 and p.strip() not in MULTI_STOPWORDS and p.strip() not in PURE_PARTICLES]
        if len(direct_tokens) >= 2:
            return cleaned, direct_tokens
            
    return cleaned, found_entities

def highlight_tokens(text: str, tokens: List[str]) -> str:
    """在文本中为匹配到的词打上【】标记（避免重复嵌套）"""
    res = text
    # 按长度倒序，优先替换长词
    for tok in sorted(tokens, key=len, reverse=True):
        if not tok:
            continue
        # 避免在已有的【】内重复包裹
        pattern = re.compile(rf'(?<!【)({re.escape(tok)})(?!】)', re.IGNORECASE)
        res = pattern.sub(r'【\1】', res)
    return res

def scan_chapter_for_tokens(
    lines: List[str],
    tokens: List[str],
    window_size: int = 5,
    dialogue_only: bool = False,
    context_lines: int = 2,
    start_line: int = 1
) -> Tuple[List[Dict[str, Any]], int]:
    """
    在单章行列表中扫描 tokens 的段落滑动窗口共现。
    返回 (matched_snippets, chapter_relevance_score)
    """
    token_patterns = [re.compile(re.escape(t), re.IGNORECASE) for t in tokens]
    dialogue_regex = re.compile(r'(「[^」]+」|『[^』]+』|"[^"]+"|[“][^”]+[”])')

    # 1. 扫描每一行的 token 命中情况与对白情况
    line_hits = []
    for idx, line in enumerate(lines):
        if (idx + 1) < start_line:
            continue
        hits = set()
        for t, pat in zip(tokens, token_patterns):
            if pat.search(line):
                hits.add(t)
        has_dialogue = bool(dialogue_regex.search(line))
        if hits:
            line_hits.append((idx, hits, has_dialogue))

    if not line_hits:
        return [], 0

    # 2. 段落滑动窗口查找
    matched_ranges = []
    for i in range(len(line_hits)):
        curr_hits = set(line_hits[i][1])
        s_line = line_hits[i][0]
        any_dialogue = line_hits[i][2]

        for j in range(i, len(line_hits)):
            e_line = line_hits[j][0]
            if e_line - s_line > window_size:
                break
            curr_hits.update(line_hits[j][1])
            if line_hits[j][2]:
                any_dialogue = True

            if len(curr_hits) == len(tokens):
                if dialogue_only and not any_dialogue:
                    continue
                dist = e_line - s_line
                score = 100 - dist * 15
                matched_ranges.append((s_line, e_line, score))
                break

    if not matched_ranges:
        return [], 0

    # 3. 合并相邻/重叠的窗口并生成切片
    merged_windows = []
    curr_s, curr_e, curr_score = matched_ranges[0]
    for s, e, sc in matched_ranges[1:]:
        if s <= curr_e + 2:
            curr_e = max(curr_e, e)
            curr_score = max(curr_score, sc)
        else:
            merged_windows.append((curr_s, curr_e, curr_score))
            curr_s, curr_e, curr_score = s, e, sc
    merged_windows.append((curr_s, curr_e, curr_score))

    # 计算整章评分：最高窗口分 + 匹配窗口数量加成
    chapter_score = max(w[2] for w in merged_windows) + len(merged_windows) * 10

    snippets = []
    for s_line, e_line, sc in merged_windows:
        ctx_s = max(0, s_line - context_lines)
        ctx_e = min(len(lines), e_line + 1 + context_lines)

        ctx_lines_formatted = []
        for lno in range(ctx_s, ctx_e):
            raw_l = lines[lno]
            is_matched_line = (s_line <= lno <= e_line) and any(p.search(raw_l) for p in token_patterns)
            hl_l = highlight_tokens(raw_l.strip(), tokens)
            prefix = " >> " if is_matched_line else "    "
            ctx_lines_formatted.append(f"{prefix}{lno + 1:4d}: {hl_l}")

        # 核心代表行文本
        core_line_text = lines[s_line].strip()
        snippets.append({
            "line_num": s_line + 1,
            "end_line_num": e_line + 1,
            "type": "dialogue" if dialogue_only else "narrative",
            "score": sc,
            "text": core_line_text,
            "context": "\n".join(ctx_lines_formatted)
        })

    return snippets, chapter_score

def search_novel(
    keyword: str,
    scope: str = "web",
    volume: Optional[str] = None,
    series: Optional[str] = None,
    chapter: Optional[str] = None,
    dialogue_only: bool = False,
    limit: int = 5,
    context_lines: int = 2,
    window_size: int = 5,
    exact_mode: bool = False,
    start_line: int = 1,
    max_matches: int = 5
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    执行高精度全文检索，支持多词共现与智能降级。
    返回: (results, fallback_info)
    """
    manifest = load_manifest(scope)
    
    # 1. 过滤卷次 / 系列 / 章节
    filtered_manifest = []
    for item in manifest:
        if volume is not None:
            v_str = str(volume).strip()
            if v_str.isdigit():
                if item.get('volume_num') != int(v_str):
                    continue
            else:
                if v_str.lower() not in item.get('volume', '').lower():
                    continue

        if series is not None:
            s_str = str(series).strip().lower()
            item_series = item.get('series', '') + " " + item.get('series_id', '')
            if s_str not in item_series.lower():
                continue

        if chapter is not None:
            c_str = str(chapter).strip()
            if c_str.isdigit():
                if item.get('id') != int(c_str):
                    continue
            else:
                if c_str.lower() not in item.get('title', '').lower():
                    continue

        filtered_manifest.append(item)

    # 2. 如果无关键词，则是章节直接调阅模式
    if not keyword:
        results = []
        for item in filtered_manifest[:limit if limit > 0 else None]:
            content = read_chapter_content(item)
            body = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
            lines = body.splitlines()
            base_dir = item.get('_base_dir', WEB_CORPUS_DIR)
            abs_path = os.path.abspath(os.path.join(base_dir, item['relative_path']))
            results.append({
                "scope": item.get('_scope', 'web'),
                "chapter_id": item['id'],
                "volume": item['volume'],
                "series": item.get('series', ''),
                "title": item['title'],
                "canonical_status": item.get('canonical_status', item.get('light_novel_vol', '')),
                "word_count": item['word_count'],
                "relative_path": item['relative_path'],
                "absolute_path": abs_path,
                "total_lines": len(lines),
                "matched_count": 0,
                "score": 0,
                "matches": [],
                "content_preview": body[:1500] if len(body) > 1500 else body
            })
        return results, None

    # 3. 词法解析
    tokens, is_explicit_multi = parse_query(keyword)

    def execute_query_plan(search_tokens: List[str]) -> List[Dict[str, Any]]:
        plan_results = []
        for item in filtered_manifest:
            content = read_chapter_content(item)
            if not content:
                continue

            # 极速前置过滤：必须全部 token 都在文本中
            if not all(tok in content for tok in search_tokens):
                continue

            body = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
            lines = body.splitlines()

            snippets, ch_score = scan_chapter_for_tokens(
                lines=lines,
                tokens=search_tokens,
                window_size=window_size,
                dialogue_only=dialogue_only,
                context_lines=context_lines,
                start_line=start_line
            )

            if snippets:
                # 若包含原始字面完整短语，给予额外相关度加分
                if keyword in body:
                    ch_score += 200

                base_dir = item.get('_base_dir', WEB_CORPUS_DIR)
                abs_path = os.path.abspath(os.path.join(base_dir, item['relative_path']))

                plan_results.append({
                    "scope": item.get('_scope', 'web'),
                    "chapter_id": item['id'],
                    "volume": item['volume'],
                    "series": item.get('series', ''),
                    "title": item['title'],
                    "canonical_status": item.get('canonical_status', item.get('light_novel_vol', '')),
                    "word_count": item['word_count'],
                    "relative_path": item['relative_path'],
                    "absolute_path": abs_path,
                    "total_lines": len(lines),
                    "matched_count": len(snippets),
                    "score": ch_score,
                    "matched_terms": search_tokens,
                    "matches": snippets[:max_matches]
                })

        plan_results.sort(key=lambda x: x['score'], reverse=True)
        return plan_results

    # 4. 执行常规检索
    results = execute_query_plan(tokens)
    fallback_info = None

    # 5. 若未命中且允许降级：智能分词降级检索
    if not results and not exact_mode:
        cleaned_stem, subterms = smart_decompose(keyword)

        # 尝试阶段 A: 词干优化检索（如剥离开头的“成为”后搜索“第三位妻子”）
        if cleaned_stem and cleaned_stem != keyword and len(cleaned_stem) >= 2:
            stem_results = execute_query_plan([cleaned_stem])
            if stem_results:
                results = stem_results
                fallback_info = {
                    "mode": "stem_strip",
                    "original": keyword,
                    "target": cleaned_stem,
                    "terms": [cleaned_stem]
                }

        # 尝试阶段 B: 核心专名与概念共现（如【第三位】+【妻子】）
        if not results and len(subterms) >= 2:
            subterm_results = execute_query_plan(subterms)
            if subterm_results:
                results = subterm_results
                fallback_info = {
                    "mode": "subterm_cooccurrence",
                    "original": keyword,
                    "terms": subterms
                }

    final_results = results[:limit] if limit > 0 else results

    # 6. 若启用了范围过滤（-c / -v / -s）且当前过滤下 0 命中，快速检测全局是否有该词，生成友好提示
    if not final_results and keyword and (chapter is not None or volume is not None or series is not None):
        unfiltered_res, _ = search_novel(
            keyword=keyword,
            scope=scope,
            limit=3,
            dialogue_only=dialogue_only,
            exact_mode=exact_mode,
            start_line=start_line,
            max_matches=max_matches
        )
        if unfiltered_res:
            active_filters = []
            if chapter is not None:
                active_filters.append(f"-c {chapter}")
            if volume is not None:
                active_filters.append(f"-v {volume}")
            if series is not None:
                active_filters.append(f"-s {series}")
            fallback_info = {
                "mode": "filter_restricted",
                "filters": " ".join(active_filters),
                "examples": [f"第 {r['chapter_id']} 话《{r['title']}》" for r in unfiltered_res],
                "count": len(unfiltered_res)
            }

    return final_results, fallback_info

def print_text_results(results: List[Dict[str, Any]], keyword: str, fallback_info: Optional[Dict[str, Any]] = None):
    """人类可读终端高亮打印"""
    print("\n" + "=" * 80)
    print(f"❖ 《无职转生》小说语料极速检索报告 | 关键词: 「{keyword}」 | 命中章节数: {len(results)}")
    print("=" * 80)

    if fallback_info:
        if fallback_info.get("mode") == "stem_strip":
            print(f"💡 [智能词干校准]: 原关键词「{fallback_info['original']}」无直接字面命中，已自动剥离首尾虚词，按「{fallback_info['target']}」执行检索：")
        elif fallback_info.get("mode") == "subterm_cooccurrence":
            terms_str = " + ".join([f"【{t}】" for t in fallback_info['terms']])
            print(f"💡 [智能分词降级检索]: 原长短语「{fallback_info['original']}」无直接字面命中，已自动识别为核心词组 {terms_str} 展开段落共现检索：")
        elif fallback_info.get("mode") == "filter_restricted":
            ex_str = "、".join(fallback_info['examples'])
            print(f"💡 [范围过滤提示]: 当前指定的范围过滤 [{fallback_info['filters']}] 下未包含关键词「{keyword}」。")
            print(f"   但在全局范围内，该词在其他章节（如：{ex_str} 等）中存在！建议去除 {fallback_info['filters']} 参数进行全局检索。")
        print("-" * 80)

    if not results:
        print("未找到任何相关段落。请尝试缩短检索词、更换同义词或调整筛选范围。")
        print("=" * 80 + "\n")
        return

    for idx, r in enumerate(results, 1):
        scope_tag = "[外传]" if r.get('scope') == 'gaiden' else "[正传]"
        score_tag = f"匹配度: {r.get('score', 0)}" if r.get('score') else ""
        print(f"\n({idx}) {scope_tag} 【{r['volume']}】 {r['title']}  ({score_tag})")
        print(f"    - 对应正史/定位: {r.get('canonical_status', '')} | 章节字数: {r['word_count']:,} 字")
        print(f"    - 绝对路径 (供 view_file 直接读取): {r.get('absolute_path', r.get('relative_path', ''))}")
        print(f"    - 命中片段数: {r['matched_count']} 处 | 全文总行数: {r.get('total_lines', 0)} 行")
        print("    " + "-" * 74)

        if not keyword and "content_preview" in r:
            print("    [章节内容摘要]:")
            for pline in r['content_preview'].splitlines()[:15]:
                if pline.strip():
                    print(f"      {pline.strip()}")
            print(f"      ...... (完整正文请调用 view_file 直接研读: {r.get('absolute_path', '')})")
            continue

        for m_idx, m in enumerate(r['matches'], 1):
            line_info = f"第 {m['line_num']} 行" if m['line_num'] == m.get('end_line_num', m['line_num']) else f"第 {m['line_num']}~{m.get('end_line_num')} 行"
            prefix = "『台词/心声』" if m['type'] == 'dialogue' else line_info
            print(f"    ▶ [片段 {m_idx} | {prefix}] 核心行: {m['text']}")
            if m.get('context'):
                print("      [段落共现切片]:")
                for cline in m['context'].splitlines():
                    print(f"      {cline}")

    if results:
        top_res = results[0]
        abs_p = top_res.get('absolute_path', '')
        tot_l = top_res.get('total_lines', 0)
        first_m = top_res['matches'][0]['line_num'] if top_res.get('matches') else 1
        s_line = max(1, first_m - 10)
        e_line = min(tot_l if tot_l else first_m + 150, first_m + 150)
        print("\n" + "=" * 80)
        print("💡 [Agent 原著研读指引 - 两步法协议]")
        print("已成功定位章节！CLI 检索已完成。严禁继续在命令行反复试探猜参数！")
        print(f"下一步必须立刻调用 view_file 工具阅读原文（界面将显示为 Analyzed）：")
        print(f"  推荐起步调用: view_file(AbsolutePath=r\"{abs_p}\", StartLine={s_line}, EndLine={e_line})")
        print("  【阅读尺度】行号区间仅供起步参考！请按情节自然起止灵活调整（可短读数十行，亦可连续阅读多段直至完整高潮闭环）。")
        print("通读原著真实对白、受挫与动作细节后再开始叙事！")
        print("=" * 80 + "\n")
    else:
        print("\n" + "=" * 80 + "\n")

def list_volumes():
    """打印正传 24 卷概览"""
    manifest = load_manifest("web")
    print("\n" + "=" * 80)
    print("❖ 《无职转生》Web 版正传全 24 卷与文库版映射清单")
    print("=" * 80)
    vol_dict = {}
    for item in manifest:
        v = item['volume']
        if v not in vol_dict:
            vol_dict[v] = {
                'num': item['volume_num'],
                'ln': item['light_novel_vol'],
                'count': 0,
                'words': 0
            }
        vol_dict[v]['count'] += 1
        vol_dict[v]['words'] += item['word_count']

    for vname, info in sorted(vol_dict.items(), key=lambda x: x[1]['num']):
        print(f"第 {info['num']:02d} 卷 | {vname:<32} | {info['count']:2d} 话 | {info['words']:,} 字 | 对应: {info['ln']}")
    print("=" * 80 + "\n")

def list_gaiden():
    """打印外传 8 大分支概览"""
    manifest = load_manifest("gaiden")
    print("\n" + "=" * 80)
    print("❖ 《无职转生》外传与特典语料库 8 大分支清单")
    print("=" * 80)
    series_dict = {}
    for item in manifest:
        s = item['series']
        if s not in series_dict:
            series_dict[s] = {
                'id': item.get('series_id', ''),
                'canonical': item.get('canonical_status', ''),
                'count': 0,
                'words': 0
            }
        series_dict[s]['count'] += 1
        series_dict[s]['words'] += item['word_count']

    for sname, info in series_dict.items():
        print(f"【{sname}】 | {info['count']:2d} 篇 | {info['words']:,} 字 | 定位: {info['canonical']}")
    print("=" * 80 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="《无职转生：人生模拟器》全景小说原文与外传极速检索 CLI 工具 (v2.0 智能增强版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python scripts/query_novel.py "豪雷"                       # 全文检索正传
  python scripts/query_novel.py "艾莉丝 妻子"                # 多关键词段落共现检索
  python scripts/query_novel.py "成为第三位妻子"              # 智能分词降级检索
  python scripts/query_novel.py "拉普拉斯" --gaiden          # 全文检索外传
  python scripts/query_novel.py "死神" --all                 # 双库正传+外传联搜
  python scripts/query_novel.py "龙鸣山" -s "古龙昔话"       # 古龙昔话精准检索
  python scripts/query_novel.py "闭嘴" --dialogue            # 仅在对白与心声中检索
  python scripts/query_novel.py "毒鼠" --json                # 结构化纯净 JSON 格式输出
  python scripts/query_novel.py --list-volumes               # 列出正传全 24 卷概览
  python scripts/query_novel.py --list-gaiden                # 列出外传 8 大系列大盘
        """
    )

    parser.add_argument("keyword", nargs="?", default="", help="全文检索关键词（多个词以空格分隔，支持引号整词）")
    parser.add_argument("-k", "--keyword-opt", dest="keyword_opt", help="检索关键词（与位置参数等价）")
    parser.add_argument("--gaiden", action="store_true", help="检索外传与特典语料库 (corpus/gaiden)")
    parser.add_argument("--all", action="store_true", help="同时检索正传与外传全部语料 (319万字双库联搜)")
    parser.add_argument("-v", "--volume", help="筛选正传卷次编号（1~24）或卷名关键词")
    parser.add_argument("-s", "--series", help="筛选外传系列名或系列代号（如'古龙昔话'、'专职篇'、'蛇足篇'）")
    parser.add_argument("-c", "--chapter", help="筛选章节序号或标题关键词")
    parser.add_argument("-S", "--start-line", type=int, default=1, help="仅扫描指定起始行之后的匹配（1-indexed）")
    parser.add_argument("-m", "--max-matches", type=int, default=5, help="每章最大展示片段数（默认5条）")
    parser.add_argument("--dialogue", action="store_true", help="仅在角色对白「……」与内心独白『……』中检索")
    parser.add_argument("-n", "--limit", type=int, default=5, help="返回匹配章节数量上限（默认5条）")
    parser.add_argument("-C", "--context", type=int, default=2, help="命中行前后展示的上下文行数（默认2行）")
    parser.add_argument("-W", "--window", type=int, default=5, help="多关键词段落共现的最大跨越行数（默认5行）")
    parser.add_argument("--exact", action="store_true", help="禁用智能降级，强制严格字面精确匹配")
    parser.add_argument("--json", action="store_true", help="以结构化纯净 JSON 格式输出供 Agent 调用")
    parser.add_argument("--list-volumes", action="store_true", help="列出正传 24 卷总览表及文库版映射")
    parser.add_argument("--list-gaiden", action="store_true", help="列出外传 8 大分支大盘表")

    args = parser.parse_args()

    if args.list_volumes:
        list_volumes()
        return

    if args.list_gaiden:
        list_gaiden()
        return

    kw = args.keyword_opt or args.keyword

    if not kw and not args.chapter and not args.volume and not args.series:
        parser.print_help()
        return

    series_val = args.series
    start_line_val = args.start_line
    if series_val and series_val.strip().isdigit():
        val_int = int(series_val.strip())
        if val_int > 24:
            # 误把 -s 当作起始行号传入（如 -s 1150），智能转为 start_line 处理
            start_line_val = val_int
            series_val = None

    scope = "all" if args.all else ("gaiden" if (args.gaiden or series_val) else "web")

    results, fallback_info = search_novel(
        keyword=kw,
        scope=scope,
        volume=args.volume,
        series=series_val,
        chapter=args.chapter,
        dialogue_only=args.dialogue,
        limit=args.limit,
        context_lines=args.context,
        window_size=args.window,
        exact_mode=args.exact,
        start_line=start_line_val,
        max_matches=args.max_matches
    )

    if args.json:
        # JSON 格式输出：在每个章节结果中附加降级元数据，并保持旧结构兼容
        output_payload = results
        if fallback_info:
            for item in output_payload:
                item['is_fallback'] = True
                item['fallback_info'] = fallback_info
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    else:
        print_text_results(results, kw, fallback_info)

if __name__ == '__main__':
    main()
