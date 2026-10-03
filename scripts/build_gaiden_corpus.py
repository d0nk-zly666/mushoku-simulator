"""
Build Gaiden Corpus for Mushoku Tensei Workspace
Extracts side stories from local EPUBs and fetches Web chapters from kxgxs.com cache.
Outputs pristine Markdown files with YAML frontmatter into corpus/gaiden/.
"""

import os
import re
import sys
import time
import json
import zipfile
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CORPUS_GAIDEN_DIR = os.path.join(BASE_DIR, 'corpus', 'gaiden')
CACHE_DIR = os.path.join(BASE_DIR, 'raw_downloads', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# ---------------- Text Cleaning Helpers ----------------

REPLACEMENTS = [
    (r'少N', '少女'),
    (r'N仆', '女仆'),
    (r'驽隶', '奴隶'),
    (r'内Q', '内情'),
    (r'事Q', '事情'),
    (r'情Q', '情况'),
    (r'Q况', '情况'),
    (r'Q报', '情报'),
    (r'感Q', '感情'),
    (r'爱Q', '爱情'),
    (r'同Q', '同情'),
    (r'心Q', '心情'),
    (r'表Q', '表情'),
    (r'烤禸', '烤肉'),
    (r'龙禸', '龙肉'),
    (r'裸@露', '裸露'),
    (r'裸露', '裸露'),
    (r'王N', '王子'),
    (r'倒下的N人', '倒下的男人'),
    (r'倒在路上的N人', '倒在路上的男人'),
    (r'称为狂犬的N人', '称为狂犬的女人'),
    (r'N人', '男人'), # fallback
]

def clean_text(text: str) -> str:
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&#8203;', '').replace('&#4;0;', '(').replace('&#4;1;', ')')
    
    # Strip HTML tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'</p>|<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean vocabulary filters
    for pat, rep in REPLACEMENTS:
        text = re.sub(pat, rep, text)
        
    # Quote normalization
    # Convert “ ” to 「 」 for standard quotes if they appear
    text = text.replace('“', '「').replace('”', '」')
    
    # Filter lines
    lines = []
    for line in text.splitlines():
        l = line.strip()
        if not l:
            continue
        # Remove ad / site banners
        if any(bad in l for bad in ['本章未完', '点击下一页继续阅读', '开心果小说', 'kxgxs.com', '无职转生吧', '扫图：', '录入：', '校对：', '仅供学习交流', '禁作商业用途']):
            if len(l) < 50:
                continue
        lines.append(l)
        
    return '\n\n'.join(lines)

def fetch_url_cached(url: str, cache_key: str) -> str:
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.html")
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
            
    print(f"Fetching: {url} -> {cache_key}")
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
            time.sleep(0.15) # Polite delay
            return content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_kxgxs_chapter(html: str):
    t_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
    title = re.sub(r'<[^>]+>', '', t_match.group(1)).strip() if t_match else ""
    
    idx = html.find('class="chapter-content"')
    if idx != -1:
        end_idx = html.find('</div>', idx)
        raw_text = html[idx:end_idx]
    else:
        raw_text = ""
        
    cleaned = clean_text(raw_text)
    return title, cleaned

def write_chapter_file(dir_path: str, filename: str, frontmatter: dict, body: str):
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)
    word_count = len(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]', body))
    frontmatter['word_count'] = word_count
    
    yaml_lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, str):
            yaml_lines.append(f'{k}: "{v}"')
        else:
            yaml_lines.append(f'{k}: {v}')
    yaml_lines.append("---")
    
    content = "\n".join(yaml_lines) + f"\n\n# {frontmatter.get('series', '')}\n\n## {frontmatter.get('title', '')}\n\n" + body + "\n"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [Saved] {filename} ({word_count:,} words)")
    return word_count

manifest = []

# ================= 1. 保罗外传 (Paul Gaiden) =================
print("\n>>> Processing 06_保罗外传_Paul_Gaiden...")
paul_dir = os.path.join(CORPUS_GAIDEN_DIR, '06_保罗外传_Paul_Gaiden')
with zipfile.ZipFile(os.path.join(BASE_DIR, 'raw_downloads', '无职转生_ixinzhi.epub'), 'r') as z:
    paul_chapters = [
        ("001_第一话_简妮斯.md", "第一话【简妮斯】", "OEBPS/Text/504.html", 1),
        ("002_第二话_S级冒险者队伍.md", "第二话【S级冒险者队伍】", "OEBPS/Text/505.html", 2),
        ("003_第三话_黑狼之牙解散.md", "第三话【黑狼之牙解散】", "OEBPS/Text/506.html", 3),
    ]
    for fn, title, path, cid in paul_chapters:
        raw = z.read(path).decode('utf-8', errors='ignore')
        body = clean_text(raw)
        # Fix Paul's wife name to standard 塞妮丝 if translated as 简妮斯
        body = body.replace('简妮斯', '塞妮丝')
        fm = {
            'title': title,
            'series': '保罗外传 冒险者退隐篇',
            'series_id': '06_Paul_Gaiden',
            'chapter_id': cid,
            'category': '官方外传',
            'canonical_status': '正史前传'
        }
        wc = write_chapter_file(paul_dir, fn, fm, body)
        manifest.append({**fm, 'filename': fn, 'rel_path': f'06_保罗外传_Paul_Gaiden/{fn}', 'word_count': wc})

# ================= 2. 蛇足篇 1~2 卷 (Redundancy Vol 1~2) =================
print("\n>>> Processing 01_蛇足篇_Redundancy (Vol 1 & 2 from EPUB)...")
sz_dir = os.path.join(CORPUS_GAIDEN_DIR, '01_蛇足篇_Redundancy')
with zipfile.ZipFile(os.path.join(BASE_DIR, 'raw_downloads', '蛇足篇.epub'), 'r') as z:
    sz_epub_items = [
        ("001_第一卷_诺伦的婚礼.md", "第一卷 〈诺伦的婚礼〉", "Text/01.html", 1),
        ("002_第一卷_露西与爸爸.md", "第一卷 〈露西与爸爸〉", "Text/02.html", 2),
        ("003_第一卷_阿斯拉七骑士物语.md", "第一卷 〈阿斯拉七骑士物语〉", "Text/03.html", 3),
        ("004_第一卷_从前被称为狂犬的女人.md", "第一卷 〈从前被称为狂犬的女人〉", "Text/04.html", 4),
        ("005_第一卷_特典_艾莉丝与蜜妮托纳.md", "第一卷 特典 艾莉丝与蜜妮托纳", "Text/06.html", 5),
        ("006_第一卷_特典_杜加结婚前夜祭.md", "第一卷 特典 杜加结婚前夜祭", "Text/07.html", 6),
        ("007_第二卷_人偶行走之日_前篇.md", "第二卷 〈来制作自动人偶吧！〉人偶行走之日 前篇", "Text/08.html", 7),
        ("008_第二卷_人偶行走之日_中篇.md", "第二卷 人偶行走之日 中篇", "Text/09.html", 8),
        ("009_第二卷_人偶行走之日_后篇.md", "第二卷 人偶行走之日 后篇", "Text/10.html", 9),
        ("010_第二卷_米里斯旅行手记_问候拉托雷亚家.md", "第二卷 〈米里斯旅行手记〉问候拉托雷亚家", "Text/11.html", 10),
        ("011_第二卷_米里斯旅行手记_亚尔斯在米里斯观光.md", "第二卷 米里斯旅行手记 亚尔斯在米里斯观光", "Text/12.html", 11),
        ("012_第二卷_米里斯旅行手记_洛琪希与使命.md", "第二卷 米里斯旅行手记 洛琪希与使命", "Text/13.html", 12),
        ("013_第二卷_米里斯旅行手记_前往圣剑大道.md", "第二卷 米里斯旅行手记 前往圣剑大道", "Text/14.html", 13),
        ("014_第二卷_米里斯旅行手记_温泉.md", "第二卷 米里斯旅行手记 温泉", "Text/15.html", 14),
        ("015_第二卷_米里斯旅行手记_险峻山峰之塔尔韩德.md", "第二卷 米里斯旅行手记 险峻山峰之塔尔韩德", "Text/16.html", 15),
        ("016_第二卷_剑之圣地的神_剑神吉诺布里兹.md", "第二卷 〈居住在剑之圣地的神〉剑神吉诺·布里兹", "Text/17.html", 16),
        ("017_第二卷_剑之圣地的神_在当座之间.md", "第二卷 剑之圣地的神 在当座之间", "Text/18.html", 17),
        ("018_第二卷_剑之圣地的神_妮娜布里兹.md", "第二卷 剑之圣地的神 妮娜·布里兹", "Text/19.html", 18),
        ("019_第二卷_格雷拉特家的孩子们.md", "第二卷 〈格雷拉特家的孩子们〉", "Text/20.html", 19),
        ("020_第二卷_特典_亚尔斯和菈菈.md", "第二卷 特典 亚尔斯和菈菈", "Text/22.html", 20),
        ("021_第二卷_特典_弟子与英雄与切达人.md", "第二卷 特典 弟子与英雄与切达人", "Text/23.html", 21),
        ("022_第二卷_特典_分身.md", "第二卷 特典 分身", "Text/24.html", 22),
        ("023_第二卷_特典_萌生.md", "第二卷 特典 萌生", "Text/25.html", 23),
    ]
    for fn, title, path, cid in sz_epub_items:
        path = f"OEBPS/{path}" if not path.startswith("OEBPS/") else path
        raw = z.read(path).decode('utf-8', errors='ignore')
        body = clean_text(raw)
        fm = {
            'title': title,
            'series': '无职转生 ～蛇足篇～',
            'series_id': '01_Redundancy',
            'chapter_id': cid,
            'category': '后日谈',
            'canonical_status': '文库正史'
        }
        wc = write_chapter_file(sz_dir, fn, fm, body)
        manifest.append({**fm, 'filename': fn, 'rel_path': f'01_蛇足篇_Redundancy/{fn}', 'word_count': wc})

# ================= 3. 蛇足篇第 3 卷·无职红毯 (Book 10036) =================
print("\n>>> Processing 01_蛇足篇_Redundancy (Vol 3 无职红毯 from kxgxs)...")
sz3_items = [
    ("024_第三卷_无职红毯_故事.md", "第三卷 无职红毯 二.「故事」", "https://www.kxgxs.com/index.php/book/read/10036/1864", "sz3_1864", 24),
    ("025_第三卷_无职红毯_家庭会议.md", "第三卷 无职红毯 三.「家庭会议」", "https://www.kxgxs.com/index.php/book/read/10036/1865", "sz3_1865", 25),
    ("026_第三卷_无职红毯_年轻.md", "第三卷 无职红毯 四.「年轻」", "https://www.kxgxs.com/index.php/book/read/10036/1866", "sz3_1866", 26),
    ("027_第三卷_无职红毯_搜查.md", "第三卷 无职红毯 五.「搜查」", "https://www.kxgxs.com/index.php/book/read/10036/1867", "sz3_1867", 27),
    ("028_第三卷_无职红毯_细微的裂痕.md", "第三卷 无职红毯 六.「细微的裂痕」", "https://www.kxgxs.com/index.php/book/read/10036/1868", "sz3_1868", 28),
    ("029_第三卷_无职红毯_小小守护者.md", "第三卷 无职红毯 七.「小小守护者」", "https://www.kxgxs.com/index.php/book/read/10036/1869", "sz3_1869", 29),
    ("030_第三卷_无职红毯_爱夏格雷拉特.md", "第三卷 无职红毯 八.「爱夏·格雷拉特」", "https://www.kxgxs.com/index.php/book/read/10036/1870", "sz3_1870", 30),
    ("031_第三卷_无职红毯_当爱夏辞去女仆之时.md", "第三卷 无职红毯 九.「当爱夏辞去女仆之时」", "https://www.kxgxs.com/index.php/book/read/10036/1871", "sz3_1871", 31),
    ("032_第三卷_无职红毯_后日谈.md", "第三卷 无职红毯 十.「后日谈」", "https://www.kxgxs.com/index.php/book/read/10036/1872", "sz3_1872", 32),
    ("033_第三卷_特典_恸哭的克莉丝.md", "第三卷 特典 恸哭的克莉丝", "https://www.kxgxs.com/index.php/book/read/10036/1873", "sz3_1873", 33),
    ("034_第三卷_特典_莉莉撒娇.md", "第三卷 特典 莉莉撒娇", "https://www.kxgxs.com/index.php/book/read/10036/1874", "sz3_1874", 34),
    ("035_第三卷_特典_菈菈看起来很寂寞.md", "第三卷 特典 菈菈看起来很寂寞", "https://www.kxgxs.com/index.php/book/read/10036/1875", "sz3_1875", 35),
    ("036_第三卷_特典_露西生气了.md", "第三卷 特典 露西生气了", "https://www.kxgxs.com/index.php/book/read/10036/1876", "sz3_1876", 36),
    ("037_第三卷_特典_亚尔斯与商人.md", "第三卷 特典 亚尔斯与商人", "https://www.kxgxs.com/index.php/book/read/10036/1877", "sz3_1877", 37),
    ("038_第三卷_特典_奔跑吧齐格.md", "第三卷 特典 奔跑吧，齐格", "https://www.kxgxs.com/index.php/book/read/10036/1878", "sz3_1878", 38),
]
for fn, title, url, ckey, cid in sz3_items:
    html = fetch_url_cached(url, ckey)
    _, body = extract_kxgxs_chapter(html)
    fm = {
        'title': title,
        'series': '无职转生 ～蛇足篇～',
        'series_id': '01_Redundancy',
        'chapter_id': cid,
        'category': '后日谈',
        'canonical_status': '文库正史 (修正版)'
    }
    wc = write_chapter_file(sz_dir, fn, fm, body)
    manifest.append({**fm, 'filename': fn, 'rel_path': f'01_蛇足篇_Redundancy/{fn}', 'word_count': wc})

# ================= 4. 蛇足篇 Web 独占篇章 (从事务所到最后的离巢) =================
print("\n>>> Processing 01_蛇足篇_Redundancy (Web 独占篇章)...")
sz_web_items = [
    ("039_Web篇_事务所的一天.md", "Web篇 13、事务所的一天", "https://www.kxgxs.com/index.php/book/read/5318/476", "sz_web_476", 39),
    ("040_Web篇_烤饭团.md", "Web篇 23、烤饭团", "https://www.kxgxs.com/index.php/book/read/5318/486", "sz_web_486", 40),
    ("041_Web篇_酱炖乌冬.md", "Web篇 24、酱炖乌冬", "https://www.kxgxs.com/index.php/book/read/5318/487", "sz_web_487", 41),
    ("042_Web篇_三文治.md", "Web篇 25、三文治", "https://www.kxgxs.com/index.php/book/read/5318/488", "sz_web_488", 42),
    ("043_Web篇_章鱼小丸子.md", "Web篇 26、章鱼小丸子", "https://www.kxgxs.com/index.php/book/read/5318/489", "sz_web_489", 43),
    ("044_Web篇_阿斯拉王立学校毕业典礼.md", "Web篇 27、阿斯拉王立学校毕业典礼", "https://www.kxgxs.com/index.php/book/read/5318/490", "sz_web_490", 44),
    ("045_Web篇_3年与成果.md", "Web篇 28、3年与成果", "https://www.kxgxs.com/index.php/book/read/5318/491", "sz_web_491", 45),
    ("046_Web篇_末路.md", "Web篇 29、末路", "https://www.kxgxs.com/index.php/book/read/5318/492", "sz_web_492", 46),
    ("047_Web篇_进路.md", "Web篇 30、进路", "https://www.kxgxs.com/index.php/book/read/5318/493", "sz_web_493", 47),
    ("048_Web篇_儿女离巢之时.md", "Web篇 31、儿女离巢之时", "https://www.kxgxs.com/index.php/book/read/5318/494", "sz_web_494", 48),
    ("049_Web篇_最后的离巢_鲁迪乌斯安息.md", "Web篇 32、最后的离巢（鲁迪乌斯安息）", "https://www.kxgxs.com/index.php/book/read/5318/495", "sz_web_495", 49),
]
for fn, title, url, ckey, cid in sz_web_items:
    html = fetch_url_cached(url, ckey)
    _, body = extract_kxgxs_chapter(html)
    fm = {
        'title': title,
        'series': '无职转生 ～蛇足篇～',
        'series_id': '01_Redundancy',
        'chapter_id': cid,
        'category': '后日谈',
        'canonical_status': 'Web原版正史'
    }
    wc = write_chapter_file(sz_dir, fn, fm, body)
    manifest.append({**fm, 'filename': fn, 'rel_path': f'01_蛇足篇_Redundancy/{fn}', 'word_count': wc})

# ================= 5. 专职篇 / 齐格篇 (Jobless Oblige) =================
print("\n>>> Processing 02_专职篇_Jobless_Oblige...")
jo_dir = os.path.join(CORPUS_GAIDEN_DIR, '02_专职篇_Jobless_Oblige')
jo_items = [
    ("001_第1话_过于的相遇.md", "第1话 过于的相遇", 496),
    ("002_第2话_现在的无职.md", "第2话 现在的无职", 497),
    ("003_第3话_现在的正义伙伴.md", "第3话 现在的正义伙伴", 498),
    ("004_第4话_现在的妹妹.md", "第4话 现在的妹妹", 499),
    ("005_第5话_现在的奴隶市场.md", "第5话 现在的奴隶市场", 500),
    ("006_第6话_过去的王子.md", "第6话 过去的王子", 501),
    ("007_第7话_现在的结婚.md", "第7话 现在的结婚", 502),
    ("008_第8话_现在的败北.md", "第8话 现在的败北", 503),
    ("009_第9话_过去的毕业.md", "第9话 过去的毕业", 504),
    ("010_第10话_现在的师傅.md", "第10话 现在的师傅", 505),
    ("011_第11话_现在的父亲.md", "第11话 现在的父亲", 506),
    ("012_第12话_现在的出门.md", "第12话 现在的出门", 507),
    ("013_第13话_现在的亲友.md", "第13话 现在的亲友", 508),
    ("014_最终话_未来的英雄.md", "最终话 未来的英雄", 509),
]
for i, (fn, title, cid_raw) in enumerate(jo_items, 1):
    url = f"https://www.kxgxs.com/index.php/book/read/5318/{cid_raw}"
    ckey = f"jo_{cid_raw}"
    html = fetch_url_cached(url, ckey)
    _, body = extract_kxgxs_chapter(html)
    fm = {
        'title': title,
        'series': '专职篇 Jobless Oblige',
        'series_id': '02_Jobless_Oblige',
        'chapter_id': i,
        'category': '后日谈外传',
        'canonical_status': '正史后日谈 (死神齐格哈鲁特篇)'
    }
    wc = write_chapter_file(jo_dir, fn, fm, body)
    manifest.append({**fm, 'filename': fn, 'rel_path': f'02_专职篇_Jobless_Oblige/{fn}', 'word_count': wc})

# ================= 6. 爱夏篇 Web 原版对照 (Aisha Arc Original) =================
print("\n>>> Processing 03_爱夏篇_Aisha_Arc...")
aisha_dir = os.path.join(CORPUS_GAIDEN_DIR, '03_爱夏篇_Aisha_Arc')
aisha_items = [
    ("001_01_童话.md", "01、童话", 510),
    ("002_02_抵抗.md", "02、抵抗", 511),
    ("003_03_搜索.md", "03、搜索", 512),
    ("004_04_阿尔斯.md", "04、阿尔斯", 513),
    ("005_05_爱莎.md", "05、爱莎", 514),
    ("006_06_爱莎格瑞拉特.md", "06、爱莎·格瑞拉特", 515),
    ("007_07_作者删除公告.md", "07、删除公告（作者原注）", 516),
]
for i, (fn, title, cid_raw) in enumerate(aisha_items, 1):
    url = f"https://www.kxgxs.com/index.php/book/read/5318/{cid_raw}"
    ckey = f"aisha_{cid_raw}"
    html = fetch_url_cached(url, ckey)
    _, body = extract_kxgxs_chapter(html)
    fm = {
        'title': title,
        'series': '爱夏篇 (Web原版私奔篇)',
        'series_id': '03_Aisha_Arc',
        'chapter_id': i,
        'category': 'Web外传原版对照',
        'canonical_status': 'Web原版 (已由文库第3卷修订替代，保留用于文献对照)'
    }
    wc = write_chapter_file(aisha_dir, fn, fm, body)
    manifest.append({**fm, 'filename': fn, 'rel_path': f'03_爱夏篇_Aisha_Arc/{fn}', 'word_count': wc})

# ================= 7. 古龙昔话 (Old Dragon's Tale) =================
print("\n>>> Processing 04_古龙昔话_Old_Dragons_Tale...")
odt_dir = os.path.join(CORPUS_GAIDEN_DIR, '04_古龙昔话_Old_Dragons_Tale')
odt_items = [
    ("001_第1话_龙与少女.md", "第1话 龙与少女", 517),
    ("002_第2话_龙魔的诞生.md", "第2话 龙魔的诞生", 518),
    ("003_第3话_族群中的一分子.md", "第3话 族群中的一分子", 519),
    ("004_第4话_训练终了.md", "第4话 训练终了", 520),
    ("005_第5话_赤龙调教.md", "第5话 赤龙调教", 521),
    ("006_第6话_龙的调教师.md", "第6话 龙的调教师", 522),
    ("007_第7话_异变.md", "第7话 异变", 523),
    ("008_第8话_搜索.md", "第8话 搜索", 524),
    ("009_第9话_人神的助言.md", "第9话 人神的助言", 525),
    ("010_第10话_魔龙王.md", "第10话 魔龙王", 526),
    ("011_第11话_龙与淑女.md", "第11话 龙与淑女", 527),
    ("012_第12话_龙之外交官.md", "第12话 龙之外交官", 528),
    ("013_第13话_诞生祭以及.md", "第13话 诞生祭，以及……", 529),
    ("014_第14话_葬礼.md", "第14话 葬礼", 530),
    ("015_第15话_愤怒的龙神.md", "第15话 愤怒的龙神", 531),
    ("016_第16话_一个世界终结之日.md", "第16话 一个世界终结之日", 532),
    ("017_第17话_对转移的研究.md", "第17话 对转移的研究", 533),
    ("018_第18话_魔界覆灭.md", "第18话 魔界覆灭", 534),
    ("019_第19话_离反.md", "第19话 离反", 535),
    ("020_第20话_五龙将的背叛.md", "第20话 五龙将的背叛", 536),
    ("021_第21话_龙界的终点.md", "第21话 龙界的终点", 537),
    ("022_第22话_于是走向新的故事.md", "第22话 于是，走向新的故事", 538),
]
for i, (fn, title, cid_raw) in enumerate(odt_items, 1):
    url = f"https://www.kxgxs.com/index.php/book/read/5318/{cid_raw}"
    ckey = f"odt_{cid_raw}"
    html = fetch_url_cached(url, ckey)
    _, body = extract_kxgxs_chapter(html)
    fm = {
        'title': title,
        'series': '古龙昔话 Old Dragon\'s Tale',
        'series_id': '04_Old_Dragons_Tale',
        'chapter_id': i,
        'category': '神话前传',
        'canonical_status': '六面世界核心历史 (魔龙王拉普拉斯前传)'
    }
    wc = write_chapter_file(odt_dir, fn, fm, body)
    manifest.append({**fm, 'filename': fn, 'rel_path': f'04_古龙昔话_Old_Dragons_Tale/{fn}', 'word_count': wc})

# ================= 8. 王龙王讨伐篇 (Subjugation of the King Dragon) =================
print("\n>>> Processing 05_王龙王讨伐篇_King_Dragon...")
kd_dir = os.path.join(CORPUS_GAIDEN_DIR, '05_王龙王讨伐篇_King_Dragon')
kd_items = [
    ("001_前言.md", "前言", 539),
    ("002_序章.md", "序章", 540),
    ("003_第1话_倒下的男人.md", "第1话 倒下的男人", 541),
    ("004_第2话_续倒在路上的男人.md", "第2话 续·倒在路上的男人", 542),
    ("005_第3话_英雄传.md", "第3话《英雄传》", 543),
    ("006_第4话_被大家抛弃的少年.md", "第4话 被大家抛弃的少年", 544),
    ("007_第5话_王龙王.md", "第5话 王龙王", 545),
    ("008_第6话_续被嫌弃的少年.md", "第6话 续·被嫌弃的少年", 546),
    ("009_第7话_胜负.md", "第7话 胜负", 547),
    ("010_第8话_开始.md", "第8话 开始", 548),
    ("011_尾声.md", "尾声", 549),
]
for i, (fn, title, cid_raw) in enumerate(kd_items, 1):
    url = f"https://www.kxgxs.com/index.php/book/read/5318/{cid_raw}"
    ckey = f"kd_{cid_raw}"
    html = fetch_url_cached(url, ckey)
    _, body = extract_kxgxs_chapter(html)
    fm = {
        'title': title,
        'series': '王龙王讨伐篇',
        'series_id': '05_King_Dragon',
        'chapter_id': i,
        'category': '前传外传',
        'canonical_status': '六面世界前传 (正传前约400年)'
    }
    wc = write_chapter_file(kd_dir, fn, fm, body)
    manifest.append({**fm, 'filename': fn, 'rel_path': f'05_王龙王讨伐篇_King_Dragon/{fn}', 'word_count': wc})

# ================= 9. 官方短篇集 (Special Book) =================
print("\n>>> Processing 07_官方短篇集_Special_Book...")
sb_dir = os.path.join(CORPUS_GAIDEN_DIR, '07_官方短篇集_Special_Book')
with zipfile.ZipFile(os.path.join(BASE_DIR, 'raw_downloads', '无职转生_ixinzhi.epub'), 'r') as z:
    for idx in range(511, 551):
        path = f"OEBPS/Text/{idx}.html"
        raw = z.read(path).decode('utf-8', errors='ignore')
        t_match = re.search(r'<title>(.*?)</title>', raw)
        full_title = t_match.group(1).replace('Special book', '').strip() if t_match else f"短篇_{idx}"
        body = clean_text(raw)
        seq = idx - 510
        fn = f"{seq:03d}_{re.sub(r'[^\w\u4e00-\u9fa5]', '_', full_title)[:25]}.md"
        fm = {
            'title': full_title,
            'series': '官方短篇集 Special Book',
            'series_id': '07_Special_Book',
            'chapter_id': seq,
            'category': '官方特典短篇',
            'canonical_status': '官方正史短篇'
        }
        wc = write_chapter_file(sb_dir, fn, fm, body)
        manifest.append({**fm, 'filename': fn, 'rel_path': f'07_官方短篇集_Special_Book/{fn}', 'word_count': wc})

# ================= 10. BD 与 广播剧特典 (Bonus Stories) =================
print("\n>>> Processing 08_BD与广播剧特典_Bonus_Stories...")
bonus_dir = os.path.join(CORPUS_GAIDEN_DIR, '08_BD与广播剧特典_Bonus_Stories')
with zipfile.ZipFile(os.path.join(BASE_DIR, 'raw_downloads', '无职转生_ixinzhi.epub'), 'r') as z:
    bonus_specs = [
        ("001_BD1_布耶纳村驻扎骑士的一天.md", "BD1 布耶纳村驻扎骑士的一天", "OEBPS/Text/474.html", "第一季BD特典"),
        ("002_BD2_罗亚市长遇上的问题.md", "BD2 菲托亚领要塞都市罗亚市长遇上的问题", "OEBPS/Text/475.html", "第一季BD特典"),
        ("003_BD3_他的枪柄有点短.md", "BD3 他的枪柄有点短", "OEBPS/Text/476.html", "第一季BD特典"),
        ("004_BD4_你不是被骗了吧.md", "BD4 你不是被骗了吧？", "OEBPS/Text/477.html", "第一季BD特典"),
        ("005_第二季BD1_狂犬来过了.md", "第二季BD1 狂犬来过了", "OEBPS/Text/507.html", "第二季BD特典"),
        ("006_第二季BD2_夏日的课外辅导.md", "第二季BD2 夏日的课外辅导", "OEBPS/Text/508.html", "第二季BD特典"),
        ("007_第二季BD3_旅途的回忆.md", "第二季BD3 旅途的回忆", "OEBPS/Text/509.html", "第二季BD特典"),
        ("008_第二季BD4_诺伦去往学生会.md", "第二季BD4 诺伦，去往学生会", "OEBPS/Text/510.html", "第二季BD特典"),
        ("009_广播剧_莉莉娅篇_骑士侍从最初的工作.md", "广播剧特典 莉莉娅篇 骑士侍从最初的工作", "OEBPS/Text/459.html", "广播剧特典"),
        ("010_广播剧_爱莎篇_天才女仆被表扬了.md", "广播剧特典 爱莎篇 天才女仆被表扬了", "OEBPS/Text/460.html", "广播剧特典"),
        ("011_广播剧_遗剑的故事.md", "广播剧短篇 遗剑的故事", "OEBPS/Text/461.html", "广播剧独占短篇"),
        ("012_迷宫广播剧_剑士和盗贼的花钱经历.md", "转移迷宫篇广播剧 剑士和盗贼的某次花钱经历", "OEBPS/Text/462.html", "广播剧特典"),
        ("013_迷宫广播剧_读书人和长耳族的战士.md", "转移迷宫篇广播剧 读书人和长耳族的战士", "OEBPS/Text/463.html", "广播剧特典"),
        ("014_迷宫广播剧_剑士和炭矿族的酒力较量.md", "转移迷宫篇广播剧 剑士和炭矿族的酒力较量", "OEBPS/Text/464.html", "广播剧特典"),
        ("015_迷宫广播剧_禁酒剑士就贪杯一次.md", "转移迷宫篇广播剧 禁酒剑士就贪杯一次", "OEBPS/Text/465.html", "广播剧特典"),
        ("016_活动特典_IF如果保罗还活着的话.md", "联动特典 IF 如果保罗还活着的话", "OEBPS/Text/473.html", "官方IF联动短篇"),
    ]
    for i, (fn, title, path, cat) in enumerate(bonus_specs, 1):
        raw = z.read(path).decode('utf-8', errors='ignore')
        body = clean_text(raw)
        fm = {
            'title': title,
            'series': 'BD与广播剧特典集',
            'series_id': '08_Bonus_Stories',
            'chapter_id': i,
            'category': cat,
            'canonical_status': '官方正史特典' if 'IF' not in cat else '官方IF短篇'
        }
        wc = write_chapter_file(bonus_dir, fn, fm, body)
        manifest.append({**fm, 'filename': fn, 'rel_path': f'08_BD与广播剧特典_Bonus_Stories/{fn}', 'word_count': wc})

# Write gaiden_manifest.json
manifest_path = os.path.join(CORPUS_GAIDEN_DIR, 'gaiden_manifest.json')
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

total_words = sum(m['word_count'] for m in manifest)
total_chapters = len(manifest)

print(f"\n================ SUMMARY ================")
print(f"Total Gaiden Chapters written: {total_chapters}")
print(f"Total Gaiden Words: {total_words:,}")
print(f"Manifest saved to: {manifest_path}")
