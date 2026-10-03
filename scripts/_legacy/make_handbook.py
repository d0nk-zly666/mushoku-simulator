# -*- coding: utf-8 -*-
"""
主构建脚本：将所有章节模块整合并构建最终的纯 Markdown 主设定集
《无职转生：人生模拟器·完整版》.md 与备份文件 backup/《无职转生：人生模拟器·终极完整版》.md
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from module_core_and_early import add_core_and_early_chapters
from module_chronicles import add_chronicles_chapter
from module_world_systems import add_world_systems_chapters
from module_gameplay_rules import add_gameplay_rules_chapters
from module_advanced_and_start import add_advanced_and_start_chapters
from module_ch50_rifujin_aesthetic_engine import add_rifujin_aesthetic_engine_chapter

class HandbookDocBuilder:
    """纯原生 Markdown 构建器，零外部依赖，完全兼容所有装配模块接口"""
    def __init__(self):
        self.paragraphs = []

    def add_main_title(self, text):
        text_str = str(text).strip()
        if text_str:
            self.paragraphs.append(text_str)
        return text_str

    def add_sub_title(self, text):
        text_str = str(text).strip()
        if text_str:
            self.paragraphs.append(text_str)
        return text_str

    def add_heading_1(self, text):
        text_str = str(text).strip()
        if text_str:
            self.paragraphs.append(text_str)
        return text_str

    def add_heading_2(self, text):
        text_str = str(text).strip()
        if text_str:
            self.paragraphs.append(text_str)
        return text_str

    def add_heading_3(self, text):
        text_str = str(text).strip()
        if text_str:
            self.paragraphs.append(text_str)
        return text_str

    def add_paragraph(self, text):
        lines = str(text).split('\n')
        last_line = None
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            self.paragraphs.append(line_str)
            last_line = line_str
        return last_line

    def add_cover(self, title, subtitle=None):
        self.add_main_title(title)
        if subtitle:
            self.add_sub_title(subtitle)

    def add_chapter_title(self, text):
        return self.add_heading_1(text)

    def add_section_title(self, text):
        return self.add_heading_2(text)

    def add_sub_section_title(self, text):
        return self.add_heading_3(text)

    def add_meta_box(self, text):
        return self.add_paragraph(f"> {text}")

    @property
    def doc(self):
        class _ParagraphShim:
            def __init__(self, t):
                self.text = t
        class _DocShim:
            def __init__(self, paras):
                self._paras = paras
            @property
            def paragraphs(self):
                return [_ParagraphShim(p) for p in self._paras]
        return _DocShim(self.paragraphs)

    def export_md(self, md_path, backup_md_path=None):
        md_blocks = []
        for p_str in self.paragraphs:
            p_str = p_str.strip()
            if not p_str:
                continue
            if p_str.startswith('【'):
                md_blocks.append(f"### {p_str}")
            else:
                md_blocks.append(p_str)
        md_content = "\n\n".join(md_blocks)
        
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"成功导出 Markdown 文件: {md_path}")
        
        if backup_md_path:
            os.makedirs(os.path.dirname(backup_md_path), exist_ok=True)
            with open(backup_md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"成功保存 Markdown 备份文件: {backup_md_path}")

def main():
    print("开始构建《无职转生：人生模拟器·完整版》...")
    builder = HandbookDocBuilder()
    
    # 模块一：核心定位与第一至三章
    print("1/6 装配卷首定位、第一章、第二章、第三章...")
    add_core_and_early_chapters(builder)
    
    # 模块二：第四章（八大时代十万年编年史）
    print("2/6 装配第四章 殿堂级万年世界编年史（太古创世至终局决战）...")
    add_chronicles_chapter(builder)
    
    # 模块三：第五至十四章（世界演化、九大文明支柱、25大出身等）
    print("3/6 装配第五章至第十四章（九大支柱、25大出身与诸系统）...")
    add_world_systems_chapters(builder)
    
    # 模块四：第十五至二十八章（战斗机制、斗气与拉普拉斯因子、三妻六子全档案、NPC生死机制）
    print("4/6 装配第十五章至第二十八章（战斗机制、三妻六子档案与NPC自主系统）...")
    add_gameplay_rules_chapters(builder)
    
    # 模块五：第二十九章至第四十九章（全套面板、自检协议、二十大铁律、十二大时代启动界面）
    print("5/6 装配第二十九章至第四十九章（全套面板、自检与十二大时代启动界面）...")
    add_advanced_and_start_chapters(builder)
    
    # 模块六：第五十章（原著沉浸感引擎：理不尽孙之手文学风格与全景人设渲染规范）
    print("6/6 装配第五十章 原著沉浸感引擎：理不尽孙之手文学风格与全景人设渲染规范...")
    add_rifujin_aesthetic_engine_chapter(builder)
    
    # 仅输出 Markdown 主文件与备份文件（依据用户需求彻底移除 docx 与 txt 衍生）
    target_path_md = r'e:\无职转生\knowledge\《无职转生：人生模拟器·完整版》.md'
    target_path_backup_md = r'e:\无职转生\backup\《无职转生：人生模拟器·终极完整版》.md'
    
    builder.export_md(target_path_md, target_path_backup_md)

    # 验证新文档指标
    para_count = len(builder.paragraphs)
    total_chars = sum(len(p) for p in builder.paragraphs)
    print(f"\n=== 新文档统计结果 ===")
    print(f"段落总数: {para_count}")
    print(f"字符总数: {total_chars}")
    print(f"《无职转生：人生模拟器·完整版》.md 构建成功，已彻底移除 docx 与 txt 冗余格式。")

if __name__ == '__main__':
    main()
