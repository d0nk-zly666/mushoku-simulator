# 历史旧版构建脚本归档 (scripts/_legacy)

> [!WARNING]
> **请勿运行本目录下的任何脚本！**  
> 运行此类脚本会重新切分旧版合集，从而覆盖 `knowledge/` 目录下已重构、去重与校准的知识库正本。

## 归档文件清单及原用途说明
- `sync_knowledge.py`：早期的知识库自动化切分同步脚本，曾从《无职转生：人生模拟器·完整版》.md 切分构建 9 个知识库。
- `make_handbook.py`：早期知识库组装工具。
- `module_core_and_early.py`：早期生成 01、02 核心模块切片脚本。
- `module_chronicles.py`：早期生成编年史切片脚本。
- `module_world_systems.py`：早期生成地理与世界体系切片脚本。
- `module_gameplay_rules.py`：早期生成游戏机制切片脚本。
- `module_advanced_and_start.py`：早期生成高阶规则与建卡切片脚本。
- `module_ch50_rifujin_aesthetic_engine.py`：早期生成文学引擎与声音指纹切片脚本。

当前工作区中的 `knowledge/01~08` 与 `knowledge/_cards/` 已确立为**唯一事实源**，所有日常检索和推演均通过 `scripts/query_lore.py` 与 `scripts/query_novel.py` 进行。
