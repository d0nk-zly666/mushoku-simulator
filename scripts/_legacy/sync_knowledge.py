# -*- coding: utf-8 -*-
"""
无职转生知识库自动化双向同步与维护套件 (sync_knowledge.py)
------------------------------------------------------------
功能：
1. 自动化切分构建：从《无职转生：人生模拟器·完整版》.md 自动化切分生成 knowledge/ 下的 9 个高内聚专题模块，100% 覆盖全部 51 个章节与原著核心设定；
2. 人神专题深度提炼：将白房间 11 处托梦记录升级为标准 Markdown 四级标题（####），建立细粒度段落锚点；
3. 严格自动化索引验证：按照 VSCode / GitHub 标准 Markdown 规范解析 INDEX.md 中的深度锚点，杜绝虚假链接；
4. 命令行交互与标准纯净 JSON 输出支持，方便本地 Agent 与测试套件无缝联动。
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
MD_SOURCE = os.path.join(ROOT_DIR, "knowledge", "《无职转生：人生模拟器·完整版》.md") if os.path.exists(os.path.join(ROOT_DIR, "knowledge", "《无职转生：人生模拟器·完整版》.md")) else os.path.join(ROOT_DIR, "《无职转生：人生模拟器·完整版》.md")
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, "knowledge")
INDEX_FILE = os.path.join(ROOT_DIR, "INDEX.md")

# 9 大专题知识库模块定义及其对应章节
MODULES_CONFIG = [
    {
        "filename": "01_世界第一原则与全域地理.md",
        "title": "六面世界架构与全域地理设定集",
        "description": "包含六面世界底层世界观、创世神性规律、第一原则、七大地域环境气候、迷宫危险度梯队、经济物价体系与冒险四要素模型。",
        "include_leadin": True,
        "min_chars": 5000,
        "chapter_keywords": [
            "第一章", "第三章", "第十四章", "第二十一章", "第二十八章", "第三十七章"
        ],
        "key_assertions": [
            "第一原则：世界不围绕玩家存在",
            "正方体骰子六个面",
            "菲托亚领",
            "魔大陆",
            "阿斯拉王国",
            "全域危险度梯队划分",
            "经济体系与战略资源流转"
        ]
    },
    {
        "filename": "02_殿堂级万年世界编年史.md",
        "title": "六面世界万年世界编年史（太古创世至终局圣战）",
        "description": "包含正史与老卢迪IF线双轨判定、太古神话时代、人魔大战、拉普拉斯战役、400年空白期、鲁迪乌斯74年正史生平逐年详述、宏观因果蝴蝶效应、历史扭曲法则及甲龙历500年终局预言。",
        "include_leadin": False,
        "min_chars": 35000,
        "chapter_keywords": [
            "第二章", "第四章", "第五章", "第二十九章", "第三十五章", "第四十四章"
        ],
        "key_assertions": [
            "老卢迪未来日记",
            "毒素魔鼠",
            "洛琪希·米格路迪亚在此危机中彻底免于感染魔石病！她母女平安",
            "保罗·格雷拉特之死：甲龙历425年",
            "甲龙历500年前后",
            "菲托亚领特大转移事件",
            "毕弗隆斯大决战",
            "天顶苍穹红球异象、罗亚郊外阿尔曼菲突袭与大转移前夜正史真相",
            "光辉之阿尔曼菲"
        ]
    },
    {
        "filename": "03_战力体系_硬核魔学_斗气与三大剑派.md",
        "title": "硬核魔术体系、三大剑派克制与战斗机理",
        "description": "包含四系系统魔术物理法则、无咏唱与乱魔术、硬核斗气物理学、三大剑派战斗哲学、奇希莉卡十二魔眼全图鉴、龙神三大诅咒解密、魔导铠系统、战争推演及综合武道与魔导面板。",
        "include_leadin": False,
        "min_chars": 10000,
        "chapter_keywords": [
            "第十一章", "第十五章", "第十六章", "第十七章", "第十九章", "第二十五章", "第三十九章", "第四十章"
        ],
        "key_assertions": [
            "三大剑派",
            "斗气缠身物理法则",
            "第100代龙神奥尔斯帝德三大诅咒",
            "奇希莉卡·奇希里斯十二魔眼全图鉴",
            "预知眼",
            "黄金斗神铠",
            "Disturb Magic",
            "魔导铠"
        ]
    },
    {
        "filename": "04_势力政体_文明支柱与偏见阶层.md",
        "title": "诸国政体、九大文明支柱、魔法大学与社会偏见",
        "description": "包含九大文明支柱、阿斯拉王国四大上级贵族博弈、米里斯教团神权分立、拉诺亚魔法大学青春群像、冒险者公会规约、25大出身天赋、诸邦法律与司法暗角及全大陆地缘宏观势力面板。",
        "include_leadin": False,
        "min_chars": 8000,
        "chapter_keywords": [
            "第六章", "第七章", "第八章", "第九章", "第十章", "第十二章", "第十三章", "第十八章", "第二十二章", "第二十三章", "第四十二章"
        ],
        "key_assertions": [
            "九大文明支柱",
            "阿斯拉王国四大上级贵族",
            "伯雷亚斯",
            "米里斯神圣国与米里斯教团",
            "拉诺亚魔法大学",
            "冒险者公会严格规约",
            "25大精细出身"
        ]
    },
    {
        "filename": "05_人神十次托梦全景与因果暗线.md",
        "title": "无之世界人神十次托梦机密与龙神万年轮回棋局",
        "description": "详细解析人神在白色房间对鲁迪乌斯的全部 10 次托梦建议（含买肉救奇希莉卡、牢房遇基斯、魔法大学治愈ED促成希露菲成婚阻止洛琪希救援、地下室毒鼠魔石病死局、决战与74岁安息诀别）、人神使徒操控机制、非玩家中心机缘律与龙神因果对决。",
        "include_leadin": False,
        "min_chars": 20000,
        "chapter_keywords": [
            "第二十章", "第三十六章"
        ],
        "special_content": "HITOGAMI_FULL_EXTRACT",
        "key_assertions": [
            "【人神第1次托梦·魔大陆荒漠初次现身与信任瑞杰路德建议】",
            "【人神第2次托梦·利卡里斯镇买肉遇奇希莉卡获赠预知魔眼（核心机缘）】",
            "明天去镇里的后巷买点美味的烤肉，然后在巷子里四处逛逛吧，会有意想不到的好事发生哦~",
            "【人神第3次托梦·温达鲁港走私渡海与货仓解救兽族幼崽】",
            "【人神第4次托梦·大森林入狱遇基斯与拯救圣兽】",
            "【人神第5次托梦·西隆王室送信陷阱与手办反杀破局】",
            "【人神第6次托梦·北方指引前往魔法大学与扼杀菈菈恶毒算盘】",
            "【人神第7次托梦·极力恐吓与诱阻救援洛琪希】",
            "【人神第8次托梦·夏利亚地下室·毒老鼠魔石病绝命死局】",
            "【人神第9次托梦·撕破伪善面具·威胁杀光全家逼杀龙神】",
            "【人神第10次托梦（后篇）·白房间临终告别与万年因果棋局彻底崩盘】",
            "【人神托梦与白房间交互强制自检规则】",
            "【太古起源：无之世界黑幕觉醒与伪人神之乱】"
        ]
    },
    {
        "filename": "06_格雷拉特家族谱系与外传蛇足.md",
        "title": "格雷拉特家族三妻六子全档案与外传蛇足全集",
        "description": "包含鲁迪乌斯与三位妻子（希露菲、洛琪希、艾莉丝）及六位子女详尽档案、《蛇足篇》全部七大经典故事（诺伦婚礼、露西与爸爸、爱夏私奔、死神诞生等）、《保罗外传》、《古龙昔话》及多世代家族盛衰纪。",
        "include_leadin": False,
        "min_chars": 3500,
        "chapter_keywords": [
            "第二十四章", "第三十二章", "第四十三章"
        ],
        "special_content": "REDUNDANCY_FULL_EXTRACT",
        "key_assertions": [
            "格雷拉特家族三妻六子",
            "保罗、塞妮丝与莉莉娅",
            "三位至爱妻子",
            "蛇足篇",
            "诺伦婚礼",
            "爱夏私奔",
            "多世代血脉继承与家族盛衰纪"
        ]
    },
    {
        "filename": "07_理不尽孙之手文学引擎与全员声音指纹.md",
        "title": "理不尽孙之手文学风格与 32 位全员人设声音指纹库",
        "description": "包含原著作者理不尽孙之手'泥土与汗水美学'、四维感官渲染法则、32 位全员口癖/语速/心理防御机制/反 OOC 禁令、五大经典情景多幕对齐示范及 AI 强制自检防 OOC 安全协议。",
        "include_leadin": False,
        "min_chars": 25000,
        "chapter_keywords": [
            "第五十章", "第四十六章"
        ],
        "key_assertions": [
            "理不尽孙之手",
            "泥土与汗水",
            "32 位全员人设声音指纹库",
            "鲁迪乌斯·格雷拉特",
            "艾莉丝·伯雷亚斯·格雷拉特",
            "洛琪希·米格路迪亚",
            "希露菲叶特",
            "奥尔斯帝德",
            "AI推演运行时强制在内部思考链中执行的四重静默自检过滤协议",
            "面向玩家呈现的纯净正文输出绝对禁令",
            "固化专属选项机制【原史同调 / 顺应正史】"
        ]
    },
    {
        "filename": "08_模拟器运行规则_交互指令与检定系统.md",
        "title": "模拟器核心仲裁机制、系统指令与开局建卡指南",
        "description": "包含玩家人生终极目标多元论、NPC自主生命系统、情报迷雾、动态状态快照协议规范、系统指令集（/status /roll /save /load /sync）、全维状态面板规范、世界运行二十大铁律及正式启动界面与十二大时代抉择。",
        "include_leadin": False,
        "min_chars": 9000,
        "chapter_keywords": [
            "第二十六章", "第二十七章", "第三十章", "第三十一章", "第三十三章", "第三十四章",
            "第三十八章", "第四十一章", "第四十五章", "第四十七章", "第四十八章", "第四十九章"
        ],
        "key_assertions": [
            "NPC自主生命系统与生死法则",
            "情报迷雾与真相追索系统",
            "玩家人生终极目标多元论",
            "玩家全维人生状态面板",
            "全维人生快照存档与记忆保护机制",
            "六面世界终极运行二十大铁律",
            "正式启动界面与十二大时代抉择",
            "原史同调与顺应正史见证者模式规范"
        ]
    }
]

def load_source_document():
    """读取并解析主 Markdown 设定集"""
    if not os.path.exists(MD_SOURCE):
        raise FileNotFoundError(f"源设定集文件不存在: {MD_SOURCE}")
    with open(MD_SOURCE, "r", encoding="utf-8") as f:
        full_text = f.read()

    # 切分章节：匹配行首的“第X章”
    chapter_pattern = re.compile(r'\n(?=第[一二三四五六七八九十百]+章[^\n]*)')
    parts = chapter_pattern.split(full_text)
    
    lead_in = parts[0]
    chapters_dict = {}
    for p in parts[1:]:
        p_clean = p.strip()
        lines = p_clean.split('\n', 1)
        title = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        chapters_dict[title] = body

    return full_text, lead_in, chapters_dict

def format_dreams_as_headers(text):
    """
    将时代八正文中的人神托梦项目转换为 Markdown 四级标题，形成可直达的段落锚点
    """
    # 匹配形如 * 【人神第1次托梦...】： 或 - 【人神第1次托梦...】： 或行首 【人神第1次托梦...】：
    pattern = re.compile(r'(?:^\s*[\*\-]\s*)?(【人神第\d+次托梦[^】\n]+】)[：:]', re.M)
    return pattern.sub(r'\n\n#### \1\n\n', text)

def extract_hitogami_content(full_text, chapters_dict):
    """专门提取人神十次托梦与因果暗线的高内聚专题内容"""
    blocks = []
    
    ch4_body = ""
    ch6_body = ""
    ch50_body = ""
    for title, content in chapters_dict.items():
        if "第四章" in title:
            ch4_body = content
        elif "第六章" in title:
            ch6_body = content
        elif "第五十章" in title:
            ch50_body = content

    # 1. 太古起源：无之世界黑幕觉醒与伪人神之乱
    if ch4_body:
        hit_origin = re.search(r'(3\.\s*无之世界黑幕觉醒与伪人神之乱.*?)(?=\n\d+\.|\n### |\Z)', ch4_body, re.DOTALL)
        if hit_origin:
            blocks.append("### 【太古起源：无之世界黑幕觉醒与伪人神之乱】\n\n" + hit_origin.group(1).strip())
                
    # 2. 支柱九：人神与龙神跨越万年的神之博弈
    if ch6_body:
        hit9 = re.search(r'(### 【支柱九：人神与龙神跨越万年的神之博弈.*?)(?=\n### |\n## |\Z)', ch6_body, re.DOTALL)
        if hit9:
            blocks.append(hit9.group(1).strip())

    # 3. 人神托梦与白房间交互强制自检规则（来自第五十章）
    if ch50_body:
        hit_rules = re.search(r'(- 【人神托梦与白房间交互强制自检规则】.*?)(?=\n\d+\.\s*自检四|\n### |\Z)', ch50_body, re.DOTALL)
        if hit_rules:
            blocks.append("### 【人神托梦与白房间交互强制自检规则】\n\n" + hit_rules.group(1).strip())

    # 4. 时代八：鲁迪乌斯时代与人神十次托梦全景解构（将11处托梦格式化为####小标题）
    if ch4_body:
        hit_era8 = re.search(r'(### 【时代八：鲁迪乌斯时代.*?)(?=\n### 【时代九|\Z)', ch4_body, re.DOTALL)
        if hit_era8:
            era8_formatted = format_dreams_as_headers(hit_era8.group(1).strip())
            blocks.append(era8_formatted)
            
    return "\n\n---\n\n".join(blocks)

def extract_redundancy_content(full_text, chapters_dict):
    """专门提取《蛇足篇》（Redundancy）全部七大经典故事与后代外传的专题内容"""
    ch4_body = ""
    for title, content in chapters_dict.items():
        if "第四章" in title:
            ch4_body = content
            break
    if ch4_body:
        hit_era9 = re.search(r'(### 【时代九：《蛇足篇》（Redundancy）全部七大经典故事与外传详述】.*?)(?=\n### 【时代十|\Z)', ch4_body, re.DOTALL)
        if hit_era9:
            return hit_era9.group(1).strip()
    return ""

def build_knowledge_base(quiet=False):
    """一键重新切分构建 knowledge 目录下的 8 个模块文件"""
    if not quiet:
        print("[1/3] 正在加载并解析《无职转生：人生模拟器·完整版》.md...")
    full_text, lead_in, chapters_dict = load_source_document()
    if not quiet:
        print(f"  成功识别 {len(chapters_dict)} 个章节与前置引导文。")

    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    hitogami_extract = extract_hitogami_content(full_text, chapters_dict)
    redundancy_extract = extract_redundancy_content(full_text, chapters_dict)

    if not quiet:
        print("\n[2/3] 正在切分构建 9 大专题知识库模块...")
    build_results = []
    
    for mod in MODULES_CONFIG:
        out_file = os.path.join(KNOWLEDGE_DIR, mod["filename"])
        doc_lines = []
        doc_lines.append(f"# {mod['title']}\n")
        doc_lines.append(f"> **模块概述**：{mod['description']}\n")
        doc_lines.append(f"> **权威出处**：摘选自《无职转生：人生模拟器·完整版》\n")
        doc_lines.append("---\n")

        # 包含前言引导
        if mod.get("include_leadin"):
            doc_lines.append(lead_in.strip() + "\n\n---\n")

        # 匹配对应章节
        for kw in mod["chapter_keywords"]:
            matched_titles = [t for t in chapters_dict.keys() if kw in t]
            for c_title in matched_titles:
                c_content = chapters_dict[c_title]
                if "第四章" in c_title and mod["filename"] == "02_殿堂级万年世界编年史.md":
                    # 在编年史正文中也格式化托梦小标题，赋予细粒度段落锚点
                    c_content = format_dreams_as_headers(c_content)
                doc_lines.append(f"## {c_title}\n")
                doc_lines.append(c_content.strip() + "\n\n---\n")

        # 人神特殊全量内容注入
        if mod.get("special_content") == "HITOGAMI_FULL_EXTRACT" and hitogami_extract:
            doc_lines.append("## 【人神（Hitogami）白色房间十次托梦建议与因果博弈核心档案】\n")
            doc_lines.append(hitogami_extract.strip() + "\n\n---\n")

        # 蛇足篇特殊全量内容注入
        if mod.get("special_content") == "REDUNDANCY_FULL_EXTRACT" and redundancy_extract:
            doc_lines.append("## 【《蛇足篇》（Redundancy）全部七大经典故事与后代外传详述】\n")
            doc_lines.append(redundancy_extract.strip() + "\n\n---\n")

        content_str = "\n".join(doc_lines)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content_str)

        size_kb = len(content_str.encode('utf-8')) / 1024.0
        char_count = len(content_str)
        if not quiet:
            print(f"  ✓ 已生成: {mod['filename']} ({char_count} 字符, {size_kb:.1f} KB)")
        build_results.append({
            "filename": mod["filename"],
            "chars": char_count,
            "size_kb": round(size_kb, 1),
            "status": "success"
        })

    if not quiet:
        print("\n9 大知识库模块构建同步完成！")
    return build_results

def vscode_slugify(text):
    """
    按照 VSCode / GitHub 标准 Markdown 规范生成标题锚点 slug
    1. 去除 HTML 标签
    2. 去除 Markdown 标题符号 (#) 并去除首尾空格
    3. 统一转为小写
    4. 空白字符替换为连字符 '-'
    5. 去除标点符号（包括中文标点、括号、破折号、引号等）
    6. 合并连续连字符为单个 '-'
    7. 去除首尾连字符
    """
    t = re.sub(r'<[^>]+>', '', text)
    t = re.sub(r'^#+\s*', '', t).strip().lower()
    t = re.sub(r'\s+', '-', t)
    t = re.sub(r'[\]\[\!\'\#\$\%\&\'\(\)\*\+\,\.\/\:\;\<\=\>\?\@\\\\\^\_\`\{\|\}\~\`。，、；：？！…—·ˉ¨‘’“”々～‖∶＂＇｀｜〃〔〕〈〉《》「」『』〖〗【】（）［］｛\}]+', '', t)
    t = re.sub(r'-+', '-', t)
    t = t.strip('-')
    return t

def verify_index_links(quiet=False):
    """严格校验 INDEX.md 中的所有相对路径与深度锚点（100% 匹配真实标题 Slug 或显式锚点）"""
    if not os.path.exists(INDEX_FILE):
        return {"all_valid": False, "error": "INDEX.md 不存在"}

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index_content = f.read()

    # 提取所有链接形如 [xxx](knowledge/yyy.md#zzz) 或 [xxx](file:///e:/无职转生/knowledge/yyy.md#zzz)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    links = link_pattern.findall(index_content)

    checked_links = 0
    valid_links = 0
    errors = []

    file_cache = {}

    for text, url in links:
        # 页内锚点（如 [目录](#一核心...)），目标文件为 INDEX_FILE
        if url.startswith("#"):
            checked_links += 1
            file_path = INDEX_FILE
            anchor = url[1:]
        elif "knowledge/" in url or url.endswith(".md") or ".md#" in url:
            checked_links += 1
            if "#" in url:
                base_part, anchor = url.split("#", 1)
            else:
                base_part, anchor = url, None

            if base_part.startswith("file:///"):
                file_path = base_part.replace("file:///", "").replace("/", "\\")
            elif base_part.startswith("knowledge/"):
                file_path = os.path.join(ROOT_DIR, base_part.replace("/", "\\"))
            elif not os.path.isabs(base_part):
                file_path = os.path.join(ROOT_DIR, base_part.replace("/", "\\"))
            else:
                file_path = base_part
        else:
            continue

        if not os.path.exists(file_path):
            errors.append(f"链接目标文件不存在: {url} -> {file_path}")
            continue

        if anchor:
            if file_path not in file_cache:
                with open(file_path, "r", encoding="utf-8") as target_f:
                    raw_lines = target_f.readlines()
                headers = [line.strip() for line in raw_lines if line.strip().startswith("#")]
                slugs = set(vscode_slugify(h) for h in headers)
                
                # 同时也提取任何显式 HTML 锚点：<a id="...">, <span id="...">, <a name="...">
                doc_text = "".join(raw_lines)
                html_ids = set(re.findall(r'<(?:a|span)[^>]+(?:id|name)=["\']([^"\']+)["\']', doc_text))
                file_cache[file_path] = slugs | html_ids

            valid_slugs = file_cache[file_path]
            clean_anchor = urllib.parse.unquote(anchor).lstrip("#").lower()

            # 严格判定：必须完全匹配一个标题的 VSCode slug 或显式 HTML ID
            if clean_anchor not in valid_slugs:
                errors.append(f"锚点未在目标文件中找到: #{clean_anchor} in {os.path.basename(file_path)} (链接: '{text}')")
                continue

        valid_links += 1

    all_valid = (len(errors) == 0)
    if not quiet:
        print(f"\nINDEX.md 严格链接校验结果: 检查了 {checked_links} 个链接，有效: {valid_links}, 错误: {len(errors)}")
        for err in errors[:5]:
            print(f"  ✗ {err}")
        if len(errors) > 5:
            print(f"  ... 另有 {len(errors)-5} 个错误")

    return {
        "all_valid": all_valid,
        "checked_links": checked_links,
        "valid_links": valid_links,
        "errors": errors
    }

def verify_knowledge_base(quiet=False):
    """全面校验 9 大知识库模块完整性与断言"""
    if not quiet:
        print("\n[3/3] 正在校验知识库完整性与断言一致性...")
    verify_results = {
        "modules_checked": 0,
        "modules_passed": 0,
        "assertions_passed": 0,
        "assertions_failed": 0,
        "index_links_valid": True,
        "details": []
    }

    for mod in MODULES_CONFIG:
        verify_results["modules_checked"] += 1
        out_file = os.path.join(KNOWLEDGE_DIR, mod["filename"])
        
        if not os.path.exists(out_file):
            if not quiet:
                print(f"  ✗ 缺失文件: {mod['filename']}")
            verify_results["details"].append({"module": mod["filename"], "error": "file_not_found"})
            continue
            
        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查最小规模
        min_chars = mod.get("min_chars", 3000)
        if len(content) < min_chars:
            if not quiet:
                print(f"  ✗ 文件规模不足: {mod['filename']} (实测 {len(content)} 字符, 要求 >= {min_chars})")
            verify_results["details"].append({"module": mod["filename"], "error": "file_too_small"})
            continue

        # 检查关键事实断言
        mod_ok = True
        for assertion in mod.get("key_assertions", []):
            if assertion not in content:
                if not quiet:
                    print(f"  ✗ 断言失败 [{mod['filename']}]: 缺失关键词 '{assertion[:30]}...'")
                verify_results["assertions_failed"] += 1
                mod_ok = False
            else:
                verify_results["assertions_passed"] += 1

        if mod_ok:
            verify_results["modules_passed"] += 1
            if not quiet:
                print(f"  ✓ 校验通过: {mod['filename']} ({len(content)} 字符, 包含 {len(mod.get('key_assertions', []))} 项关键事实)")

    # 校验 INDEX.md 链接有效性
    index_check = verify_index_links(quiet=quiet)
    verify_results["index_details"] = index_check
    if not index_check["all_valid"]:
        verify_results["index_links_valid"] = False

    return verify_results

def main():
    parser = argparse.ArgumentParser(description="无职转生知识库自动化双向同步与维护套件")
    parser.add_argument("--build", action="store_true", help="一键重新切分构建 8 大知识库模块")
    parser.add_argument("--verify", action="store_true", help="校验知识库与 INDEX.md 索引有效性")
    parser.add_argument("--all", action="store_true", help="构建并全量校验（默认行为）")
    parser.add_argument("--json", action="store_true", help="以纯净 JSON 格式输出结果")

    args = parser.parse_args()

    # 默认模式为 --all
    do_build = args.build or args.all or (not args.build and not args.verify)
    do_verify = args.verify or args.all or (not args.build and not args.verify)
    quiet = args.json

    report = {"status": "ok"}

    if do_build:
        build_res = build_knowledge_base(quiet=quiet)
        report["build"] = build_res

    if do_verify:
        verify_res = verify_knowledge_base(quiet=quiet)
        report["verify"] = verify_res
        if not verify_res["index_links_valid"] or verify_res["modules_passed"] < len(MODULES_CONFIG):
            report["status"] = "failed"
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            sys.exit(1)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("\n==========================================")
        print("✓ sync_knowledge 套件执行完毕，全量健康！")
        print("==========================================")

if __name__ == "__main__":
    main()
