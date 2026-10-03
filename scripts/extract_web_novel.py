#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《无职转生：人生模拟器》Web 版小说原文语料库结构化提取与清洗流水线
======================================================================
功能：
1. 自动定位根目录下的 Web 版 EPUB 小说（《无职转生 ～到了异世界就拿出真本事～.web.epub》）；
2. 解析 OEBPS/toc.ncx 树形目录，提取全部 24 卷、282 话章节；
3. 纯净化清洗 HTML 标签，转换为标准的 Markdown 格式；
4. 建立 corpus/web_novel/ 分卷结构化目录（第01章_幼年期 ~ 第24章_完结篇）；
5. 注入 Frontmatter 元数据（卷名、话数、字数、文库版映射）；
6. 自动生成 corpus/web_novel/README.md 与 chapter_manifest.json 供极速检索。
"""

import os
import sys
import re
import html
import json
import zipfile
import xml.etree.ElementTree as ET

# 文库版映射配置表 (Web 24 章 -> 文库 26 卷)
LN_MAPPING = {
    1: {"ln": "文库第 1 卷", "note": "幼年期篇（布耶纳村、洛琪希家庭教师、豪雷毕业考）"},
    2: {"ln": "文库第 2 卷", "note": "家庭教师篇（罗亚町、艾莉丝狂犬、仓库假绑架、十岁舞会）"},
    3: {"ln": "文库第 3 卷", "note": "冒险者入门篇（菲托亚大转移、焦黑荒原遇瑞杰路德、成立死路）"},
    4: {"ln": "文库第 4 卷", "note": "航海篇（利卡里斯买肉救奇希莉卡赠预知眼、出海）"},
    5: {"ln": "文库第 5 卷", "note": "重逢篇（大森林入狱结识基斯、米里希昂酒馆父子重拳冲突）"},
    6: {"ln": "文库第 6 卷", "note": "归乡篇（西隆大殿扎诺巴反水、赤龙下颚龙神洞胸救赎）"},
    7: {"ln": "文库第 8 卷（前半）", "note": "入学篇 [注：文库第 7 卷为泥沼篇加笔，Web 无]"},
    8: {"ln": "文库第 8 卷（后半）", "note": "特别生掌握篇（一击轰碎巴迪冈迪、图书馆手帕、相认七星）"},
    9: {"ln": "文库第 9 卷", "note": "希露菲叶特篇（暴雨山洞摘墨镜、深情拥吻定情成婚）"},
    10: {"ln": "文库第 10 卷", "note": "新婚篇（购置新宅、宴请师友、日常平静）"},
    11: {"ln": "文库第 11 卷", "note": "妹妹篇（爱夏诺伦抵夏利亚、诺伦宿舍自闭翻窗长谈解心结）"},
    12: {"ln": "文库第 12 卷（前半）", "note": "贝卡利特大陆篇（穿越沙海、抵达拉潘镇、集结保罗小队）"},
    13: {"ln": "文库第 12 卷（后半）", "note": "迷宫篇（救出洛琪希、九头龙决战保罗腰斩牺牲、荒丘长跪）"},
    14: {"ln": "文库第 13 卷", "note": "日常篇（夏利亚平稳岁月、露西降生、洛琪希进门）"},
    15: {"ln": "文库第 14 卷（前半）", "note": "召唤篇（空中城塞佩尔基乌斯、召唤阵试验）"},
    16: {"ln": "文库第 14 卷（后半）~ 15 卷", "note": "人神篇（老卢迪穿越示警火化毒鼠、魔导铠战龙神、狂剑王救夫）"},
    17: {"ln": "文库第 16 卷", "note": "王国篇·序曲（阿斯拉夺嫡序战、银盘晚宴水神列妲秒杀）"},
    18: {"ln": "文库第 17 卷", "note": "阿斯拉王国篇·决战（卢克对决、爱丽儿登基女皇）"},
    19: {"ln": "文库第 18 卷", "note": "部下篇（魔导铠泛用量产、建立佣兵团联络网）"},
    20: {"ln": "文库第 19 卷", "note": "扎诺巴篇（西隆防御战平叛、帕克斯跳楼、扎诺巴之痛）"},
    21: {"ln": "文库第 20~21 卷", "note": "克里夫篇（米里斯远征、救出塞妮丝神子视界、神殿骑士团决战）"},
    22: {"ln": "文库第 22~23 卷", "note": "组织篇（王龙王国备战、北神二世会晤、防人神三使徒）"},
    23: {"ln": "文库第 24~25 卷", "note": "决战篇（毕弗隆斯终极大决战、黄金斗神铠、基斯诀别）"},
    24: {"ln": "文库第 26 卷", "note": "完结篇（最后之梦、34岁自白、74岁寿终正寝白房间诀别、Prologue Zero）"}
}

def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    name = re.sub(r'[\/:*?"<>|]', '_', name)
    name = name.replace(' ', '_').replace('：', '_').replace('·', '_')
    name = re.sub(r'_+', '_', name).strip('_')
    return name

def clean_html_to_markdown(raw_html: str) -> list:
    """将 HTML 清洗为段落列表"""
    # 提取所有段落和标题
    items = re.findall(r'<(p|h[1-6])[^>]*>(.*?)</\1>', raw_html, re.DOTALL)
    clean_lines = []
    for tag, inner in items:
        # 去掉嵌套标签
        t = re.sub(r'<[^>]+>', '', inner)
        t = html.unescape(t).strip()
        # 过滤书名广告
        if not t or t == '无职转生 ～到了异世界就拿出真本事～ WEB版':
            continue
        clean_lines.append(t)
    return clean_lines

def main():
    workspace = r'e:\无职转生'
    epub_files = [f for f in os.listdir(workspace) if f.endswith('.epub')]
    if not epub_files:
        print('[ERROR] 未在工作区根目录下找到 .epub 文件！', file=sys.stderr)
        sys.exit(1)

    epub_path = os.path.join(workspace, epub_files[0])
    print(f'[*] 找到 Web 版小说母本: {epub_files[0]} ({os.path.getsize(epub_path):,} bytes)')

    target_dir = os.path.join(workspace, 'corpus', 'web_novel')
    os.makedirs(target_dir, exist_ok=True)
    print(f'[*] 目标输出目录: {target_dir}')

    with zipfile.ZipFile(epub_path, 'r') as z:
        # 1. 解析目录树 (OEBPS/toc.ncx)
        toc_data = z.read('OEBPS/toc.ncx')
        root = ET.fromstring(toc_data)
        ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}

        top_navs = root.findall('./ncx:navMap/ncx:navPoint', ns)
        print(f'[*] 解析到顶级目录项: {len(top_navs)}')

        manifest = []
        vol_stats = []
        global_ch_id = 0
        total_word_count = 0

        for vol_idx, np in enumerate(top_navs):
            vol_title = np.find('ncx:navLabel/ncx:text', ns).text.strip()
            sub_nps = np.findall('./ncx:navPoint', ns)

            # 过滤封面和纯附录项
            if not sub_nps:
                # 检查是否为独立单文件章节（如后记）
                v_src = np.find('ncx:content', ns).attrib.get('src', '')
                if 'index_split' in v_src:
                    clean_vol_name = f'附录_{sanitize_filename(vol_title)}'
                    vol_dir = os.path.join(target_dir, clean_vol_name)
                    os.makedirs(vol_dir, exist_ok=True)
                    
                    global_ch_id += 1
                    raw_html = z.read(f'OEBPS/{v_src}').decode('utf-8', errors='ignore')
                    lines = clean_html_to_markdown(raw_html)
                    char_count = sum(len(l) for l in lines)
                    total_word_count += char_count

                    fname = f'{global_ch_id:03d}_{sanitize_filename(vol_title)}.md'
                    fpath = os.path.join(vol_dir, fname)

                    md_content = f"""---
title: "{vol_title}"
volume: "{vol_title}"
chapter_id: {global_ch_id}
word_count: {char_count}
light_novel_vol: "外传 / 后记附录"
---

# {vol_title}

""" + '\n\n'.join(lines) + '\n'

                    with open(fpath, 'w', encoding='utf-8') as fp:
                        fp.write(md_content)

                    manifest.append({
                        "id": global_ch_id,
                        "title": vol_title,
                        "volume": vol_title,
                        "volume_num": 0,
                        "relative_path": f"{clean_vol_name}/{fname}",
                        "word_count": char_count,
                        "light_novel_vol": "外传 / 后记附录"
                    })
                continue

            # 规范化卷序号与卷目录名称
            # 提取如 "第一章 幼年期" -> "第01章_幼年期"
            vol_match = re.match(r'第([一二三四五六七八九十百]+)章\s*(.*)', vol_title)
            vol_num = len(vol_stats) + 1
            if vol_match:
                vol_suffix = vol_match.group(2).strip()
                clean_vol_name = f'第{vol_num:02d}章_{sanitize_filename(vol_suffix)}'
            else:
                clean_vol_name = f'第{vol_num:02d}卷_{sanitize_filename(vol_title)}'

            vol_dir = os.path.join(target_dir, clean_vol_name)
            os.makedirs(vol_dir, exist_ok=True)

            ln_info = LN_MAPPING.get(vol_num, {"ln": "文库版对应卷", "note": ""})
            vol_words = 0
            vol_ch_count = 0

            print(f'  [+] 正在提取第 {vol_num:02d} 卷: {vol_title} ({len(sub_nps)} 话) -> {clean_vol_name}')

            for snp in sub_nps:
                global_ch_id += 1
                vol_ch_count += 1
                c_title = snp.find('ncx:navLabel/ncx:text', ns).text.strip()
                c_src = snp.find('ncx:content', ns).attrib.get('src')
                file_part = c_src.split('#')[0]

                raw_html = z.read(f'OEBPS/{file_part}').decode('utf-8', errors='ignore')
                lines = clean_html_to_markdown(raw_html)

                # 剔除正文头部重复的卷名和章节名
                while lines and (lines[0] == vol_title or lines[0] == c_title or lines[0].startswith(vol_title.split()[0])):
                    lines.pop(0)
                if lines and lines[0] == c_title:
                    lines.pop(0)

                char_count = sum(len(l) for l in lines)
                vol_words += char_count
                total_word_count += char_count

                # 生成文件名
                fname = f'{global_ch_id:03d}_{sanitize_filename(c_title)}.md'
                fpath = os.path.join(vol_dir, fname)

                # 生成格式化 Markdown 内容
                md_content = f"""---
title: "{c_title}"
volume: "{vol_title}"
volume_num: {vol_num}
chapter_id: {global_ch_id}
word_count: {char_count}
light_novel_vol: "{ln_info['ln']}"
---

# {vol_title}

## {c_title}

""" + '\n\n'.join(lines) + '\n'

                with open(fpath, 'w', encoding='utf-8') as fp:
                    fp.write(md_content)

                manifest.append({
                    "id": global_ch_id,
                    "title": c_title,
                    "volume": vol_title,
                    "volume_num": vol_num,
                    "relative_path": f"{clean_vol_name}/{fname}",
                    "word_count": char_count,
                    "light_novel_vol": ln_info['ln']
                })

            vol_stats.append({
                "vol_num": vol_num,
                "vol_title": vol_title,
                "dir_name": clean_vol_name,
                "chapter_count": vol_ch_count,
                "word_count": vol_words,
                "light_novel_vol": ln_info['ln'],
                "note": ln_info['note']
            })

        # 2. 生成结构化清单 chapter_manifest.json
        manifest_path = os.path.join(target_dir, 'chapter_manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as fp:
            json.dump(manifest, fp, ensure_ascii=False, indent=2)
        print(f'[*] 生成结构化清单: {manifest_path} (共 {len(manifest)} 话)')

        # 3. 生成 README.md 概览总表
        readme_path = os.path.join(target_dir, 'README.md')
        readme_content = f"""# 《无职转生 ～到了异世界就拿出真本事～》Web 版小说原文语料库

> **语料库定位**：
> 本目录收录原作者**理不尽な孙の手**创作的 Web 连载版正传全 24 章、全部 281 话正文及译者后记，共计约 **{total_word_count:,} 字**（约 {total_word_count/10000:.1f} 万字）。
> 本语料库作为整个工作区的**第四层·原著一手语料金库**，专门为 AI 规划器的【微观场景零跳步律】与【NPC声音指纹反OOC】提供最纯粹的原作者动作、微观台词与心理动势支撑。

---

## 一、基本统计 (Corpus Statistics)
- **总卷数**：24 卷 + 附录
- **总章节数**：{len(manifest)} 话
- **正文纯文字数**：约 **{total_word_count:,} 字**（约 {total_word_count/10000:.1f} 万字）
- **单章平均字数**：约 **{int(total_word_count/len(manifest)):,} 字**（15KB ~ 25KB，完美契合 `view_file` 单次 45KB 极速检视）
- **检索 CLI 工具**：`scripts/query_novel.py`

---

## 二、Web 版全 24 卷与文库版 (Light Novel) 双轨因果映射表

| Web 卷号 | Web 章节名称 | 收录话数 | 字数统计 | 对应文库版 (LN) 卷数 | 正史因果与剧情要点 |
| :---: | :--- | :---: | :---: | :--- | :--- |
"""
        for v in vol_stats:
            readme_content += f"| **第 {v['vol_num']:02d} 卷** | `{v['vol_title']}` | {v['chapter_count']} 话 | {v['word_count']:,} 字 | **{v['light_novel_vol']}** | {v['note']} |\n"

        readme_content += f"""
---

## 三、目录结构树 (Directory Tree)

```text
corpus/web_novel/
├── README.md                      # 本概览与对照表
├── chapter_manifest.json          # 结构化快速检索清单
"""
        for v in vol_stats:
            readme_content += f"├── {v['dir_name']}/ ({v['chapter_count']} 话, {v['word_count']:,} 字)\n"
        readme_content += """```

---

## 四、极速检索指南 (CLI Quickstart)

除直接通过 `view_file` 读取指定章节外，可直接使用原生极速命令行工具 [`scripts/query_novel.py`](file:///e:/无职转生/scripts/query_novel.py) 实现毫秒级全文对白检索：

```bash
# 1. 全文关键词检索（高亮上下文）
python scripts/query_novel.py "豪雷"
python scripts/query_novel.py "水龙咆哮"
python scripts/query_novel.py "老卢迪"

# 2. 指定卷次检索
python scripts/query_novel.py "狂犬" -v 2               # 在第 2 卷（家庭教师篇）中搜索
python scripts/query_novel.py "保罗" -v 13              # 在第 13 卷（迷宫篇）中搜索

# 3. 指定章节快速调阅
python scripts/query_novel.py -c 1                      # 快速读取序章
python scripts/query_novel.py -c 165                    # 快速读取老卢迪日记后篇

# 4. JSON 纯净结构化输出（供 Agent 调用）
python scripts/query_novel.py "毒鼠" --json
```
"""
        with open(readme_path, 'w', encoding='utf-8') as fp:
            fp.write(readme_content)
        print(f'[*] 生成语料库总览与对照表: {readme_path}')

    print(f'[SUCCESS] Web 版小说原文已成功提取至 {target_dir}，共 {len(manifest)} 话，{total_word_count:,} 字！')

if __name__ == '__main__':
    main()
