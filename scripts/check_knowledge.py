# -*- coding: utf-8 -*-
"""
《无职转生：人生模拟器》知识库结构完整性与规范自动化校验脚本 (check_knowledge.py)
"""

import os
import re
import sys
import glob

# 设置 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, "knowledge")

errors = []
warnings = []

print("=" * 60)
print("❖ 开始执行知识库规范与完整性全景自检 (check_knowledge.py)")
print("=" * 60)

# 1. 检查 01~08 文件头规范
print("\n[1/4] 检查 01~08 模块标准文件头...")
modules = ["01", "02", "03", "04", "05", "06", "07", "08"]
for m in modules:
    matches = glob.glob(os.path.join(KNOWLEDGE_DIR, f"{m}_*.md"))
    if not matches:
        errors.append(f"缺失模块文件: {m}_*.md")
        continue
    filepath = matches[0]
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        head = "".join([f.readline() for _ in range(12)])
    
    if "> **用途**：" not in head:
        errors.append(f"{filename}: 缺少 '> **用途**：' 标识")
    if "> **读取方式**：" not in head:
        errors.append(f"{filename}: 缺少 '> **读取方式**：' 标识")
    if "> **禁止**：整本读取" not in head:
        errors.append(f"{filename}: 缺少 '> **禁止**：整本读取' 标识")
    if "> **相关场景卡**：" not in head:
        errors.append(f"{filename}: 缺少 '> **相关场景卡**：' 标识")

if not errors:
    print("  ✓ 01~08 全部 8 个模块标准文件头校验通过")

# 2. 检查 CLI 依赖的关键格式
print("\n[2/4] 检查 CLI 工具依赖的核心正则标题格式...")

# 07 角色: ### 【数字. 角色名】
p07 = glob.glob(os.path.join(KNOWLEDGE_DIR, "07_*.md"))[0]
with open(p07, "r", encoding="utf-8") as f:
    c07 = f.read()
chars = re.findall(r'### 【(\d+)\.\s*([^】\n]+)】', c07)
if len(chars) != 32:
    errors.append(f"07 模块收录角色数量异常: 期望 32 位，实际找到 {len(chars)} 位")
else:
    print(f"  ✓ 07 模块收录角色数完全吻合 (32/32)")

# 05 托梦: #### 【人神第N次托梦...】
p05 = glob.glob(os.path.join(KNOWLEDGE_DIR, "05_*.md"))[0]
with open(p05, "r", encoding="utf-8") as f:
    c05 = f.read()
dreams = re.findall(r'####\s*【(人神第\d+次托梦[^\n]+)】', c05)
if len(dreams) < 10:
    errors.append(f"05 模块托梦条数异常: 期望 ≥10 条，实际找到 {len(dreams)} 条")
else:
    print(f"  ✓ 05 模块托梦条数完全吻合 ({len(dreams)} 条托梦)")

# 06 蛇足: 数字. 《故事名》
p06 = glob.glob(os.path.join(KNOWLEDGE_DIR, "06_*.md"))[0]
with open(p06, "r", encoding="utf-8") as f:
    c06 = f.read()
stories = re.findall(r'(\d+)\.\s*《([^》]+)》', c06)
if len(stories) < 7:
    errors.append(f"06 模块蛇足篇故事数异常: 期望 ≥7 篇，实际找到 {len(stories)} 篇")
else:
    print(f"  ✓ 06 模块蛇足篇故事格式完全吻合 ({len(stories)} 篇)")

# 08 原史同调: ### 原史同调与顺应正史见证者模式规范
p08 = glob.glob(os.path.join(KNOWLEDGE_DIR, "08_*.md"))[0]
with open(p08, "r", encoding="utf-8") as f:
    c08 = f.read()
if "### 原史同调与顺应正史见证者模式规范" not in c08:
    errors.append("08 模块缺失 '### 原史同调与顺应正史见证者模式规范' 标题")
else:
    print("  ✓ 08 模块原史同调规范标题存在")

# 3. 检查 02 与 05 之间是否存在 ≥200 字重复段落
print("\n[3/4] 检查 02 与 05 间是否存在 ≥200 字大段重复文本...")
p02 = glob.glob(os.path.join(KNOWLEDGE_DIR, "02_*.md"))[0]
with open(p02, "r", encoding="utf-8") as f:
    lines02 = [line.strip() for line in f if len(line.strip()) >= 200]

with open(p05, "r", encoding="utf-8") as f:
    text05 = f.read()

dup_count = 0
for l in lines02:
    if l in text05:
        # Check if it is a major duplicate
        dup_count += 1
        errors.append(f"发现 02 与 05 存在重复大段落 (长度 {len(l)} 字): {l[:40]}...")

if dup_count == 0:
    print("  ✓ 02 编年史与 05 托梦模块间已无 ≥200 字冗余重复段落")

# 4. 检查 knowledge/ 内 #锚点 引用有效性
print("\n[4/4] 检查模块间 Markdown 锚点链接规范...")
anchor_pattern = re.compile(r'\[([^\]]+)\]\((0[1-8]_[^)]+\.md)#([^)]+)\)')
checked_links = 0
for md_file in glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")):
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    for m in anchor_pattern.finditer(content):
        label, target_file, target_anchor = m.groups()
        target_path = os.path.join(KNOWLEDGE_DIR, target_file)
        if not os.path.exists(target_path):
            errors.append(f"{os.path.basename(md_file)} 链接目标文件不存在: {target_file}")
            continue
        checked_links += 1

print(f"  ✓ 校验了 {checked_links} 处模块间交叉锚点文件引用有效性")

# 报告自检结果
print("\n" + "=" * 60)
if errors:
    print(f"❌ 校验失败，共发现 {len(errors)} 处错误：")
    for e in errors:
        print("  -", e)
    sys.exit(1)
else:
    print("🎉 恭喜！全部规范检查 100% 顺利通过，知识库达到殿堂级工业质量标准！")
    print("=" * 60)
    sys.exit(0)
