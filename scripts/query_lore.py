# -*- coding: utf-8 -*-
"""
无职转生智能极速检索 CLI 工具 (query_lore.py)
------------------------------------------------------------
功能特性：
1. 关键词全文检索：极速检索 knowledge/ 各模块，大小写不敏感精准高亮并切片输出上下文；
2. 角色声音指纹与反 OOC 禁令快速调取：支持 32 位全员人设、口癖、防御机制与反 OOC 禁令，支持别名与称号（如泥沼、狂犬、龙神、死神等）；
3. 年份正史编年史大事件定位：输入甲龙历年份（如 425、417、500）或重大纪元关键词，智能去重提取原著正史大事件；
4. 人神十次托梦机密直接调阅：支持 -d/--dream 1~10，秒级调取托梦建议、幕后算盘与因果暗线；
5. 典型高频问答 (Q&A) 直达检索：一键查询 25+ 核心设定的判定标准与知识库跳转路径；
6. 支持 --list 查看全量 32 位角色清单；
7. 纯净结构化 JSON 输出支持（--json），便于本地 Agent、自动化工具与脚本无缝联动。
"""

import os
import sys
import re
import json
import argparse
import urllib.parse

# 设置 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

ROOT_DIR = r"e:\无职转生"
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, "knowledge")
INDEX_FILE = os.path.join(ROOT_DIR, "INDEX_ANCHORS.md")

# 颜色控制（Windows ANSI 支持）
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_MAGENTA = "\033[35m"

# 常用角色别名与称号映射表
CHARACTER_ALIASES = {
    "泥沼": "鲁迪乌斯",
    "老卢迪": "鲁迪乌斯",
    "狂犬": "艾莉丝",
    "狂剑王": "艾莉丝",
    "龙神": "奥尔斯帝德",
    "社长": "奥尔斯帝德",
    "老板": "奥尔斯帝德",
    "假面无音": "七星静香",
    "菲兹": "希露菲叶特",
    "菲兹学长": "希露菲叶特",
    "无音": "七星静香",
    "七星": "七星静香",
    "浪荡猴": "基斯",
    "狂魔剑客": "索尔达特",
    "魔界大帝": "奇希莉卡",
    "大帝": "奇希莉卡",
    "甲龙王": "佩尔基乌斯",
    "不死魔王": "巴迪冈迪",
    "死神": "齐格哈鲁特",
    "冥王": "齐格哈鲁特",
    "齐格": "齐格哈鲁特",
    "救世主": "菈菈",
    "剑神": "加尔·法利昂",
    "北神": "亚历山大·卡尔曼·卡隆",
    "北神三世": "亚历山大·卡尔曼·卡隆",
    "亚历山大": "亚历山大·卡尔曼·卡隆",
    "水神": "列妲",
    "阿尔斯": "阿尔斯",
    "爱夏阿尔斯": "阿尔斯与爱夏",
    "阿尔斯爱夏": "阿尔斯与爱夏",
    "帕克斯二世": "帕克斯二世",
    "露西": "露西",
    "克莉丝汀娜": "克莉丝汀娜",
    "莉莉": "莉莉",
    "杜加": "杜加与爱瑟尔",
    "爱瑟尔": "杜加与爱瑟尔"
}

def get_knowledge_files(module_filter=None):
    """获取目标知识库文件列表"""
    if not os.path.exists(KNOWLEDGE_DIR):
        return []
    all_files = sorted([
        os.path.join(KNOWLEDGE_DIR, f)
        for f in os.listdir(KNOWLEDGE_DIR)
        if f.endswith(".md")
    ])
    if module_filter:
        mod_str = str(module_filter).zfill(2)
        all_files = [f for f in all_files if os.path.basename(f).startswith(mod_str) or module_filter in f]
    return all_files

# -------------------------------------------------------------
# 1. 角色人设、声音指纹与反 OOC 禁令查询（支持 07 模块声音指纹与 06 模块外传谱系双轨直查）
# -------------------------------------------------------------
def list_characters():
    """获取 32 位全员角色清单"""
    char_file = os.path.join(KNOWLEDGE_DIR, "07_理不尽孙之手文学引擎与全员声音指纹.md")
    if not os.path.exists(char_file):
        return {"error": "未找到 07 模块文件", "count": 0, "characters": []}

    with open(char_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r'### 【(\d+)\.\s*([^】\n]+)】')
    matches = pattern.findall(content)
    char_list = []
    for idx_str, title in matches:
        char_list.append({
            "id": int(idx_str),
            "title": title.strip()
        })

    return {
        "count": len(char_list),
        "characters": char_list
    }

def query_character(char_name):
    """从 07 模块调取声音指纹，并联合 06 模块调取外传角色与格雷拉特儿女档案"""
    results = []
    char_clean = char_name.strip().lower()
    alias_target = CHARACTER_ALIASES.get(char_name.strip())

    # 1. 先查 07 模块：32 位核心人物的声音指纹与反 OOC 禁令
    char_file = os.path.join(KNOWLEDGE_DIR, "07_理不尽孙之手文学引擎与全员声音指纹.md")
    if os.path.exists(char_file):
        with open(char_file, "r", encoding="utf-8") as f:
            content_07 = f.read()

        pattern_07 = re.compile(r'(### 【\d+\.\s*([^】\n]+)】\s*\n(.*?))(?=\n### 【\d+\.|\n### 【面向玩家|\n## |\Z)', re.DOTALL)
        matches_07 = pattern_07.findall(content_07)

        for full_block, header_title, body in matches_07:
            header_lower = header_title.lower()
            matched = False
            
            if char_clean in header_lower or any(part in header_lower for part in char_clean.split()):
                matched = True
            elif alias_target and alias_target.lower() in header_lower:
                matched = True

            if matched:
                item = {
                    "character": header_title.strip(),
                    "source": "07_理不尽孙之手文学引擎与全员声音指纹.md",
                    "raw_text": full_block.strip(),
                    "sections": {}
                }
                # 提取 ■ 开头的各个板块（支持跨空行完整提取多形态对白示范）
                sub_sections = re.findall(r'(■\s*[^：:\n]+[：:])\s*(.*?)(?=\n■|\n### |\n## |\Z)', body, re.DOTALL)
                for s_title, s_content in sub_sections:
                    clean_st = s_title.strip().lstrip("■").strip().rstrip("：:")
                    item["sections"][clean_st] = s_content.strip()

                results.append(item)

    # 2. 联合检索 06 模块：格雷拉特家族第三代儿女与外传谱系档案（如阿尔斯、帕克斯二世、爱夏阿尔斯、露西、克莉丝汀娜等）
    family_file = os.path.join(KNOWLEDGE_DIR, "06_格雷拉特家族谱系与外传蛇足.md")
    if os.path.exists(family_file):
        with open(family_file, "r", encoding="utf-8") as f:
            content_06 = f.read()

        # 匹配形如 \d+\.\s*【([^】]+)】[：:]\s*(.*?)(?=\n\d+\.\s*【|\n### |\n## |\Z)
        pattern_06 = re.compile(r'(\d+\.\s*【([^】]+)】[：:]\s*(.*?))(?=\n\d+\.\s*【|\n### |\n## |\Z)', re.DOTALL)
        matches_06 = pattern_06.findall(content_06)

        for full_block, header_title, body in matches_06:
            header_lower = header_title.lower()
            matched = False

            if char_clean in header_lower or (alias_target and alias_target.lower() in header_lower):
                matched = True
            elif any(part in header_lower for part in re.split(r'[\s与和·]+', char_clean) if len(part) >= 2):
                matched = True

            if matched:
                existing = None
                for r in results:
                    if r["character"].split("（")[0].strip() == header_title.split("（")[0].strip():
                        existing = r
                        break
                if existing:
                    # 若 07 模块已收录声音指纹，将 06 模块详尽的家族谱系与生平正史合并进该角色的 sections，避免正史纪实丢失
                    bio_text = body.strip().lstrip("- ").strip()
                    if bio_text:
                        existing["sections"]["家族谱系与生平正史（06模块）"] = bio_text
                else:
                    item = {
                        "character": header_title.strip(),
                        "source": "06_格雷拉特家族谱系与外传蛇足.md",
                        "raw_text": full_block.strip(),
                        "sections": {}
                    }
                    # 尝试提取 - 【...】： 的子项
                    sub_bullets = re.findall(r'-\s*(【[^】]+】)[：:]\s*([^\n]+(?:\n(?!-)[^\n]+)*)', body)
                    if sub_bullets:
                        for b_title, b_content in sub_bullets:
                            clean_bt = b_title.strip().strip("【】")
                            item["sections"][clean_bt] = b_content.strip()
                    else:
                        item["sections"]["身份与生平纪实"] = body.strip().lstrip("- ").strip()

                    results.append(item)

    return {
        "query": char_name,
        "matched_count": len(results),
        "results": results
    }

# -------------------------------------------------------------
# 2. 年份正史编年史大事件查询
# -------------------------------------------------------------
def query_timeline(year):
    """查询指定甲龙历年份或历史大事件（智能去重与上下文整合）"""
    year_str = str(year).strip()
    num_match = re.search(r'\d+', year_str)
    year_num = num_match.group(0) if num_match else None

    # 编年史以 02 模块为唯一权威正史主干
    chronicle_file = os.path.join(KNOWLEDGE_DIR, "02_殿堂级万年世界编年史.md")
    if not os.path.exists(chronicle_file):
        return {"year": year_str, "matched_count": 0, "events": []}

    with open(chronicle_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    raw_hits = []
    current_header = ""

    for i, line in enumerate(lines):
        line_str = line.strip()
        if line_str.startswith("#"):
            current_header = line_str.lstrip("#").strip()

        matched = False
        if year_num:
            if f"甲龙历{year_num}年" in line_str or f"甲龙历 {year_num} 年" in line_str or f"【时代{year_num}】" in line_str or f"前{year_num}年" in line_str or f"{year_num}年" in line_str:
                matched = True
        else:
            if year_str.lower() in line_str.lower():
                matched = True

        if matched:
            raw_hits.append((i, current_header))

    # 去重处理：如果相邻匹配行在 3 行以内，合并为同一事件
    merged_events = []
    last_line_idx = -999

    for line_idx, header in raw_hits:
        if line_idx - last_line_idx <= 3:
            continue
        last_line_idx = line_idx

        # 提取上下文 1~4 行
        snippet_lines = []
        start_idx = max(0, line_idx - 1)
        end_idx = min(len(lines), line_idx + 4)
        for j in range(start_idx, end_idx):
            snippet_lines.append(lines[j].strip())

        merged_events.append({
            "file": os.path.basename(chronicle_file),
            "section": header,
            "line_number": line_idx + 1,
            "snippet": "\n".join(snippet_lines)
        })

    return {
        "year": year_str,
        "matched_count": len(merged_events),
        "events": merged_events
    }

# -------------------------------------------------------------
# 3. 人神十次托梦机密直接查询
# -------------------------------------------------------------
def query_dream(dream_input):
    """从 05 模块快速查询人神在白房间对鲁迪乌斯的具体托梦档案"""
    dream_str = str(dream_input).strip()
    num_match = re.search(r'\d+', dream_str)
    dream_num = num_match.group(0) if num_match else None

    hitogami_file = os.path.join(KNOWLEDGE_DIR, "05_人神十次托梦全景与因果暗线.md")
    if not os.path.exists(hitogami_file):
        return {"error": "未找到 05 模块文件", "dream": dream_str, "matched_count": 0, "results": []}

    with open(hitogami_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配形如 #### 【人神第X次托梦...】 及其正文（遇到下一个标题或编号纪元结束）
    pattern = re.compile(r'(####\s*【(人神第\d+次托梦[^\n]+)】\s*\n(.*?))(?=\n####|\n###|\n##|\n\d+\.|\Z)', re.DOTALL)
    matches = pattern.findall(content)

    results = []
    for full_block, dream_title, body in matches:
        matched = False
        if dream_num:
            if f"第{dream_num}次" in dream_title:
                matched = True
        elif dream_str.lower() in dream_title.lower() or dream_str.lower() in body.lower():
            matched = True

        if matched:
            results.append({
                "dream_title": dream_title.strip(),
                "body": body.strip(),
                "full_text": full_block.strip()
            })

    return {
        "query": dream_input,
        "matched_count": len(results),
        "results": results
    }

# -------------------------------------------------------------
# 3.5 蛇足篇全部七大故事与外传史料直接查询
# -------------------------------------------------------------
REDUNDANCY_STORY_ALIASES = {
    "诺伦婚礼": 1,
    "诺伦的婚礼": 1,
    "诺伦": 1,
    "露耶莉亚": 1,
    "瑞杰路德婚礼": 1,
    "露西爸爸": 2,
    "露西与爸爸": 2,
    "露西": 2,
    "学校参观日": 2,
    "附小": 2,
    "杜加爱瑟尔": 3,
    "杜加与爱瑟尔": 3,
    "杜加": 3,
    "爱瑟尔": 3,
    "野花告白": 3,
    "克莉丝汀娜学校": 4,
    "克莉丝汀娜学校篇": 4,
    "克莉丝汀娜的阿斯拉学校篇": 4,
    "克莉丝汀娜": 4,
    "爱德华": 4,
    "爱德华王子": 4,
    "爱夏篇": 5,
    "爱夏阿尔斯": 5,
    "阿尔斯爱夏": 5,
    "阿尔斯与爱夏": 5,
    "阿尔斯": 5,
    "爱夏私奔": 5,
    "爱夏商会": 5,
    "死神诞生": 6,
    "死神诞生篇": 6,
    "jobless oblige": 6,
    "jobless": 6,
    "齐格": 6,
    "齐格哈鲁特": 6,
    "帕克斯二世": 6,
    "死神": 6,
    "冥王": 6,
    "王龙剑": 6,
    "鲁迪安息": 7,
    "鲁迪乌斯的安息": 7,
    "安息": 7,
    "寿终正寝": 7,
    "白房间终篇": 7,
    "外传": 8,
    "外传补遗": 8,
    "古龙昔话": 8,
    "基列奴返乡记": 8,
    "莉莉与扎诺巴": 8,
    "克里夫与米里斯主教之路": 8,
    "菲托亚领故土大祭典": 8
}

def query_redundancy(story_input):
    """从 06 模块快速查询《蛇足篇》（Redundancy）全部七大核心故事与外传史料"""
    query_str = str(story_input).strip()
    num_match = re.search(r'^\d+$', query_str)
    story_num = num_match.group(0) if num_match else None

    redundancy_file = os.path.join(KNOWLEDGE_DIR, "06_格雷拉特家族谱系与外传蛇足.md")
    if not os.path.exists(redundancy_file):
        return {"error": "未找到 06 模块文件", "query": query_str, "matched_count": 0, "results": []}

    with open(redundancy_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配形如 (\d+)\.\s*《([^》]+)》([^\n]*)\n(.*?)(?=\n\d+\.\s*《|\Z)
    pattern = re.compile(r'(\d+)\.\s*《([^》]+)》([^\n]*)\n(.*?)(?=\n\d+\.\s*《|\Z)', re.DOTALL)
    matches = pattern.findall(content)

    clean_query = query_str.lower().strip()
    alias_target_num = REDUNDANCY_STORY_ALIASES.get(clean_query)
    tokens = [t for t in re.split(r'[\s\-_与和的·]+', clean_query) if t]

    results = []
    for idx_str, title, subtitle, body in matches:
        matched = False
        full_text_lower = f"{title} {subtitle} {body}".lower()

        if story_num:
            if idx_str == story_num:
                matched = True
        elif alias_target_num and str(alias_target_num) == idx_str:
            matched = True
        elif clean_query in full_text_lower:
            matched = True
        elif tokens and all(t in full_text_lower for t in tokens):
            matched = True

        if matched:
            results.append({
                "id": int(idx_str),
                "title": f"《{title}》",
                "subtitle": subtitle.strip(" :："),
                "body": body.strip()
            })

    return {
        "query": query_str,
        "matched_count": len(results),
        "results": results
    }

# -------------------------------------------------------------
# 4. 典型高频问答 (Q&A) 查询
# -------------------------------------------------------------
def query_qa(question_kw):
    """从 INDEX.md 的 Q&A 表中检索最相关的问题与判定依据"""
    if not os.path.exists(INDEX_FILE):
        return {"error": "INDEX.md 不存在", "query": question_kw, "matched_count": 0, "results": []}

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取表格行形如 | **Qx: 问题** | 核心判定 | [直达链接](url) |
    qa_pattern = re.compile(r'\|\s*\*\*Q\d+:\s*([^|*]+)\*\*\s*\|\s*([^|]+)\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|')
    matches = qa_pattern.findall(content)

    results = []
    kw_lower = question_kw.strip().lower()

    for q, ans, link_text, link_url in matches:
        if kw_lower in q.lower() or kw_lower in ans.lower() or any(w in q.lower() for w in kw_lower.split()):
            results.append({
                "question": q.strip(),
                "answer_principle": ans.strip(),
                "link_text": link_text.strip(),
                "link_url": link_url.strip()
            })

    return {
        "query": question_kw,
        "matched_count": len(results),
        "results": results
    }

# -------------------------------------------------------------
# 4.5 原史同调 / 顺应正史见证者模式核心规范查询
# -------------------------------------------------------------
def query_canon():
    """获取【原史同调 / 顺应正史见证者模式】规范与每轮固化选项生成规则"""
    kb_08 = os.path.join(KNOWLEDGE_DIR, "08_模拟器运行规则_交互指令与检定系统.md")
    if not os.path.exists(kb_08):
        return {"error": "08 模块未找到", "matched": False}
    with open(kb_08, "r", encoding="utf-8") as f:
        content = f.read()

    m = re.search(r'(### 原史同调与顺应正史见证者模式规范\s*\n(.*?))(?=\n## |\Z)', content, re.DOTALL)
    body = m.group(2).strip() if m else ""

    return {
        "mode": "原史同调 / 顺应正史见证者模式 (Canonical Witness Mode)",
        "command": "/canon",
        "aliases": ["/顺应正史", "/boost canon", "/原史同调"],
        "core_principle": "贴合原剧情发展，不对未来剧情做出改变，以见证者与同行者视角沉浸体验原汁原味的无职世界，坚决不产生蝴蝶效应",
        "option_rule": "AI 在每轮剧情推进后向玩家提供的 2~4 个行动建议分支中，必须显式提供并固化一条标识为【原史同调 / 顺应正史】的专属选项",
        "example_option": "【原史同调 / 顺应正史】：贴合原剧情发展，不对未来剧情做出改变（如：默默守候在旁，见证保罗与鲁迪的宿醉和解，不干涉正史走向）",
        "awakening_incantation": "【原史同调校准】：请锁定【顺应正史模式】，接下来的剧情严格贴合原剧情发展，不对未来走向做出改变，我将以见证者与同行者视角沉浸体验原汁原味的无职世界，不产生蝴蝶效应。请给出符合正史发展的推进与选项。",
        "raw_text": body
    }

# -------------------------------------------------------------
# 5. 全文关键词极速检索（带不区分大小写高亮）
# -------------------------------------------------------------
def query_keyword(keyword, module_filter=None, max_results=5):
    """在知识库中进行全文关键词检索"""
    target_files = get_knowledge_files(module_filter)
    hits = []
    kw_lower = keyword.strip().lower()

    for fpath in target_files:
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_h2 = ""
        current_h3 = ""
        for i, line in enumerate(lines):
            line_str = line.strip()
            if line_str.startswith("## "):
                current_h2 = line_str.lstrip("#").strip()
            elif line_str.startswith("### "):
                current_h3 = line_str.lstrip("#").strip()

            if kw_lower in line_str.lower():
                # 上下文切片
                start_line = max(0, i - 2)
                end_line = min(len(lines), i + 3)
                context_snippet = "".join(lines[start_line:end_line]).strip()

                hits.append({
                    "file": os.path.basename(fpath),
                    "h2": current_h2,
                    "h3": current_h3,
                    "line_number": i + 1,
                    "matched_line": line_str,
                    "snippet": context_snippet
                })

                if len(hits) >= max_results:
                    break
        if len(hits) >= max_results:
            break

    return {
        "keyword": keyword,
        "module_filter": module_filter,
        "matched_count": len(hits),
        "results": hits
    }

# -------------------------------------------------------------
# 终端格式化美化输出
# -------------------------------------------------------------
def print_character_list_cli(data):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 《无职转生》32 位全员声音指纹人设总览表{COLOR_RESET}")
    print(f"收录角色总数: {data['count']}")
    print("-" * 60)
    for c in data["characters"]:
        print(f"  {COLOR_GREEN}[{c['id']:02d}]{COLOR_RESET} {c['title']}")
    print(f"\n{COLOR_YELLOW}提示：运行 `python scripts/query_lore.py -c <角色名/别名>` 可调取其声音指纹与反OOC禁令。{COLOR_RESET}")

def print_character_cli(data):
    query = data.get("query", "")
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 角色人设与声音指纹查询结果: [{query}]{COLOR_RESET}")
    print(f"匹配条数: {data['matched_count']}")
    print("-" * 60)

    if not data["results"]:
        print(f"{COLOR_YELLOW}未找到与 '{query}' 相关的角色档案。请尝试输入原著标准译名或常用别名（如：艾莉丝、奥尔斯帝德、洛琪希、保罗、泥沼、狂犬等）。{COLOR_RESET}")
        return

    for item in data["results"]:
        print(f"\n{COLOR_BOLD}{COLOR_GREEN}▶ {item['character']}{COLOR_RESET}")
        for s_title, s_content in item["sections"].items():
            color = COLOR_YELLOW if "禁令" in s_title or "防OOC" in s_title or "OOC" in s_title else COLOR_CYAN
            print(f"  {color}● {s_title}{COLOR_RESET}: {s_content}")

def print_timeline_cli(data):
    year = data.get("year", "")
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 甲龙历编年史大事记检索: [{year}]{COLOR_RESET}")
    print(f"匹配事件数: {data['matched_count']}")
    print("-" * 60)

    if not data["events"]:
        print(f"{COLOR_YELLOW}未检索到与 '{year}' 相关的正史记录。请尝试常用时间点：407(出生), 417(转移), 425(老卢迪/保罗牺牲), 429(决战), 481(寿终), 500(拉普拉斯复活)。{COLOR_RESET}")
        return

    for ev in data["events"]:
        print(f"\n{COLOR_BOLD}{COLOR_GREEN}▶ 出处: {ev['file']} ➔ {ev['section']} (Line {ev['line_number']}){COLOR_RESET}")
        print(f"{ev['snippet']}")

def print_dream_cli(data):
    query = data.get("query", "")
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 人神（Hitogami）白色房间托梦机密查询: [{query}]{COLOR_RESET}")
    print(f"匹配托梦数: {data['matched_count']}")
    print("-" * 60)

    if not data["results"]:
        print(f"{COLOR_YELLOW}未找到匹配的托梦记录。可输入托梦序号（1~10）或关键词（如：预知魔眼、买肉、毒老鼠、逼杀龙神等）。{COLOR_RESET}")
        return

    for item in data["results"]:
        print(f"\n{COLOR_BOLD}{COLOR_YELLOW}▶ {item['dream_title']}{COLOR_RESET}")
        print(f"{item['body']}")

def print_redundancy_cli(data):
    query = data.get("query", "")
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 《蛇足篇》（Redundancy）经典故事与外传检索: [{query}]{COLOR_RESET}")
    print(f"匹配篇章数: {data['matched_count']}")
    print("-" * 60)

    if not data["results"]:
        print(f"{COLOR_YELLOW}未找到匹配的蛇足篇故事。可输入故事编号（1~8）或关键词（如：诺伦、婚礼、露西、杜加、爱夏、阿尔斯、死神、齐格、安息、外传等）。{COLOR_RESET}")
        return

    for item in data["results"]:
        print(f"\n{COLOR_BOLD}{COLOR_GREEN}▶ {item['id']}. {item['title']} {item['subtitle']}{COLOR_RESET}")
        print(f"{item['body']}")

def print_qa_cli(data):
    query = data.get("query", "")
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 典型高频问答判定库 (Q&A): [{query}]{COLOR_RESET}")
    print(f"匹配条目: {data['matched_count']}")
    print("-" * 60)

    if not data["results"]:
        print(f"{COLOR_YELLOW}未匹配到问答条目。可直接使用关键词全文搜索。{COLOR_RESET}")
        return

    for item in data["results"]:
        print(f"\n{COLOR_BOLD}{COLOR_GREEN}Q: {item['question']}{COLOR_RESET}")
        print(f"  {COLOR_YELLOW}核心判定{COLOR_RESET}: {item['answer_principle']}")
        print(f"  {COLOR_CYAN}直达锚点{COLOR_RESET}: {item['link_text']} ➔ {item['link_url']}")

def print_canon_cli(data):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 【原史同调 / 顺应正史见证者模式】核心规范与每轮选项生成指南{COLOR_RESET}")
    print("-" * 60)
    print(f"{COLOR_BOLD}{COLOR_GREEN}▶ 核心定位{COLOR_RESET}: {data['mode']}")
    print(f"  {COLOR_YELLOW}第一原则{COLOR_RESET}: {data['core_principle']}")
    print(f"\n{COLOR_BOLD}{COLOR_GREEN}▶ 每轮末尾选项生成规范{COLOR_RESET}:")
    print(f"  {data['option_rule']}")
    print(f"  {COLOR_CYAN}示例格式{COLOR_RESET}: {data['example_option']}")
    print(f"\n{COLOR_BOLD}{COLOR_GREEN}▶ 快捷指令与别名{COLOR_RESET}:")
    print(f"  主指令: {COLOR_YELLOW}{data['command']}{COLOR_RESET} ｜ 兼容别名: {', '.join(data['aliases'])}")
    print(f"\n{COLOR_BOLD}{COLOR_GREEN}▶ 核心唤醒咒语（第8句）{COLOR_RESET}:")
    print(f"  {data['awakening_incantation']}")


def print_keyword_cli(data):
    kw = data.get("keyword", "")
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}❖ 全文知识库检索结果: [{kw}]{COLOR_RESET}")
    print(f"匹配切片: {data['matched_count']}")
    print("-" * 60)

    if not data["results"]:
        print(f"{COLOR_YELLOW}未找到包含 '{kw}' 的段落。{COLOR_RESET}")
        return

    for hit in data["results"]:
        sec_info = f"{hit['h2']} > {hit['h3']}" if hit['h3'] else hit['h2']
        print(f"\n{COLOR_BOLD}{COLOR_GREEN}▶ [{hit['file']}] {sec_info} (Line {hit['line_number']}){COLOR_RESET}")
        # 不区分大小写精准高亮关键词
        highlighted = re.sub(
            re.escape(kw),
            lambda m: f"{COLOR_YELLOW}{COLOR_BOLD}{m.group(0)}{COLOR_RESET}",
            hit["snippet"],
            flags=re.IGNORECASE
        )
        print(f"  {highlighted}")

# -------------------------------------------------------------
# CLI 命令行入口
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="《无职转生：人生模拟器》智能极速检索 CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例用法:
  python scripts/query_lore.py "预知魔眼"                 # 全文关键词检索
  python scripts/query_lore.py -c "艾莉丝"                # 调取角色声音指纹与反OOC禁令
  python scripts/query_lore.py -c "泥沼"                  # 支持别名查询（泥沼 -> 鲁迪乌斯）
  python scripts/query_lore.py -d 2                      # 直接调取人神第 2 次托梦（买肉救奇希莉卡）
  python scripts/query_lore.py -r "诺伦婚礼"              # 直接调取蛇足篇故事（1~8 或关键词）
  python scripts/query_lore.py -y 425                    # 定位甲龙历425年大事件
  python scripts/query_lore.py -q "三大诅咒"              # 查询典型问答判定
  python scripts/query_lore.py --list                    # 列出全部 32 位角色
  python scripts/query_lore.py --canon                  # 调取顺应正史见证者模式核心规范与选项生成指南
"""
    )

    parser.add_argument("keyword", nargs="?", default=None, help="全文搜索的关键词")
    parser.add_argument("-k", "--keyword", dest="keyword_opt", help="全文搜索的关键词（与位置参数等价）")
    parser.add_argument("--canon", "--canon-mode", action="store_true", dest="canon", help="调取【原史同调 / 顺应正史见证者模式】核心规范与每轮选项生成规则")
    parser.add_argument("-c", "--character", dest="character", help="查询指定角色的声音指纹、防御机制与反OOC台词禁令")
    parser.add_argument("-d", "--dream", dest="dream", help="查询人神白色房间十次托梦机密档案 (1~10 或关键词)")
    parser.add_argument("-r", "--redundancy", dest="redundancy", help="查询《蛇足篇》（Redundancy）全部七大核心故事与外传史料 (1~8 或关键词)")
    parser.add_argument("-y", "--year", "--timeline", dest="year", help="查询甲龙历对应年份的正史编年史大事件")
    parser.add_argument("-q", "--qa", "--ask", dest="qa", help="检索典型高频问答判定库")
    parser.add_argument("-w", "--web", "--web-novel", dest="web_novel", action="store_true", help="穿透检索 Web 版小说原文语料库 (联动 query_novel.py)")
    parser.add_argument("--list", "--list-characters", action="store_true", dest="list_chars", help="列出全部 32 位角色人设清单")
    parser.add_argument("-m", "--module", dest="module", help="限制检索的模块编号 (如 01, 02, 03)")
    parser.add_argument("-n", "--limit", dest="limit", type=int, default=5, help="返回结果数量上限（默认5条）")
    parser.add_argument("--json", action="store_true", help="以结构化纯净 JSON 格式输出结果")

    args = parser.parse_args()

    # 0. 顺应正史见证者模式与固化选项规范
    if args.canon:
        data = query_canon()
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_canon_cli(data)
        return

    # 0.1 列出全员角色清单
    if args.list_chars:
        data = list_characters()
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_character_list_cli(data)
        return

    # 1. 角色声音指纹模式
    if args.character:
        data = query_character(args.character)
        novel_res = None
        if args.web_novel:
            try:
                from query_novel import search_novel, print_text_results
                novel_res = search_novel(keyword=args.character, limit=args.limit)
            except Exception as e:
                print(f"[ERROR] 检索 Web 版小说原文失败: {e}", file=sys.stderr)

        if args.json:
            if args.web_novel:
                print(json.dumps({"character": data, "web_novel": novel_res}, ensure_ascii=False, indent=2))
            else:
                print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_character_cli(data)
            if args.web_novel and novel_res:
                print("\n" + "=" * 70)
                print(f"❖ 原著一手小说语料库 (Corpus) 对白与出场直调")
                print("=" * 70)
                from query_novel import print_text_results
                print_text_results(novel_res, args.character)
        return

    # 2. 人神托梦模式
    if args.dream:
        data = query_dream(args.dream)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_dream_cli(data)
        return

    # 2.5 蛇足篇模式
    if args.redundancy:
        data = query_redundancy(args.redundancy)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_redundancy_cli(data)
        return

    # 3. 年份编年史模式
    if args.year:
        data = query_timeline(args.year)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_timeline_cli(data)
        return

    # 4. 典型问答模式
    if args.qa:
        data = query_qa(args.qa)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_qa_cli(data)
        return

    # 5. 全文关键词模式（支持 -w 跨库双轨同查）
    kw = args.keyword or args.keyword_opt
    if kw:
        data = query_keyword(kw, module_filter=args.module, max_results=args.limit)
        novel_res = None
        if args.web_novel:
            try:
                from query_novel import search_novel
                novel_res = search_novel(keyword=kw, limit=args.limit)
            except Exception as e:
                print(f"[ERROR] 检索 Web 版小说原文失败: {e}", file=sys.stderr)

        if args.json:
            if args.web_novel:
                print(json.dumps({"lore": data, "web_novel": novel_res}, ensure_ascii=False, indent=2))
            else:
                print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_keyword_cli(data)
            if args.web_novel and novel_res:
                print("\n" + "=" * 70)
                print(f"❖ 原著一手小说语料库 (Corpus) 同步匹配结果")
                print("=" * 70)
                from query_novel import print_text_results
                print_text_results(novel_res, kw)
        return

    # 默认未输入参数时输出帮助
    parser.print_help()

if __name__ == "__main__":
    main()

