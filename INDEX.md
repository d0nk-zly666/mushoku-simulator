# INDEX · 路由表（L1/L2 入口）

> 本文件只做**意图 → 场景卡 → 知识库切片**的路由，不含知识内容。
> 精确锚点与章节清单在 [INDEX_ANCHORS.md](file:///e:/无职转生/INDEX_ANCHORS.md)（大文件，**只按章节标题 grep，不整本读**）。
> 常驻规则见 [AGENTS.md](file:///e:/无职转生/AGENTS.md)。

## 一、意图路由

| 玩家意图 | 场景卡 | 知识库 / CLI |
|---|---|---|
| 开局建卡 | [start](file:///e:/无职转生/knowledge/_cards/start.md) | 08 第四十九章；04 第七章 |
| 日常推进 | [daily](file:///e:/无职转生/knowledge/_cards/daily.md) | 无 |
| NPC 对白 | [npc_voice](file:///e:/无职转生/knowledge/_cards/npc_voice.md) | `query_lore.py -c <角色>`；07 切片 |
| 战斗 / 检定 | [combat](file:///e:/无职转生/knowledge/_cards/combat.md) | 03 切片 |
| 正史节点 / `/canon` / `/sync` | [canon_guard](file:///e:/无职转生/knowledge/_cards/canon_guard.md) | `query_lore.py -y <年>`；02；联网；`query_novel.py` |
| 人神托梦 | [hitogami](file:///e:/无职转生/knowledge/_cards/hitogami.md) | `query_lore.py -d <n>`；05 |
| 快进 | [timeskip](file:///e:/无职转生/knowledge/_cards/timeskip.md) | `query_lore.py -y` |
| 存档 / 读档 / 状态 | [save_load](file:///e:/无职转生/knowledge/_cards/save_load.md) | `saves/` |
| 校准 | [recovery](file:///e:/无职转生/knowledge/_cards/recovery.md) | — |
| 家族谱系 / 蛇足篇 | — | `query_lore.py -r <n或关键词>`；06 |
| 地理 / 货币 / 危险度 | — | 01 |
| 势力 / 出身 / 偏见 | — | 04 |

## 二、知识库一览

| 模块 | 主题 | 规模 |
|---|---|---|
| 01 | 世界第一原则、地理、货币、危险梯队 | ~15KB |
| 02 | 万年编年史（含鲁迪 74 年生平） | ~112KB |
| 03 | 魔术、斗气、三大剑派、魔眼、魔导铠 | ~29KB |
| 04 | 势力政体、25 大出身、种族偏见 | ~24KB |
| 05 | 人神十次托梦、龙神轮回 | ~21KB |
| 06 | 家族谱系、蛇足篇 | ~42KB |
| 07 | 文学引擎、32 位声音指纹 | ~86KB |
| 08 | 运行规则、指令、十二时代 | ~29KB |
| `corpus/web_novel` | 正传 24 卷 283 话 | 约 229 万字 |
| `corpus/gaiden` | 外传与特典 8 分支 162 篇 | 约 90 万字 |

## 三、CLI 速查

```bash
python scripts/query_lore.py -c 艾莉丝      # 角色声音指纹（别名可用）
python scripts/query_lore.py -y 417         # 年份编年史
python scripts/query_lore.py -d 5           # 第 5 次托梦
python scripts/query_lore.py -r 诺伦婚礼     # 蛇足篇
python scripts/query_lore.py "关键词"        # 全文检索
python scripts/query_lore.py --canon        # 顺应正史规范
python scripts/query_novel.py "关键词"       # 正传原文
python scripts/query_novel.py --gaiden "关键词"
python scripts/query_novel.py --dialogue "关键词"   # 仅检索台词与心声
```

## 四、读取纪律
- 一轮最多读 2 个切片，优先 CLI。
- 需要锚点时先在 `INDEX_ANCHORS.md` 里 grep 章节名，再按行范围 `view_file`，不要整本打开。
