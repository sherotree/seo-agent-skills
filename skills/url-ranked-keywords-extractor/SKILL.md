---
name: url-ranked-keywords-extractor
description: Standalone extractor for Google ranked keywords of a given URL via DataForSEO Labs ranked_keywords/live. Returns Intent, Position, Volume, KD, CPC, Traffic, and Competition. Use only when the user asks to extract ranking keywords for a specific page or domain URL. Do not use for site audits, GEO, schema, content optimization, or seed-keyword research.
---

# URL Ranked Keywords Extractor

独立 skill：只负责从指定 URL 拉取 Google 排名词。不依赖、不调用其他 SEO/GEO skill。

输入指定网页 URL，通过 DataForSEO API 提取该页面当前在 Google 中排名的关键词及相关指标。

## Prerequisites

Prefer `.env.local` in the project (or git root). Shell `export` still works and wins.

```bash
# .env.local
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
```

Do not commit it. Confirm the consuming repo gitignores `.env` / `.env.*`. Do not store credentials in the skill directory or paste the file into chat.

Lookup order: existing env → `.env.local` then `.env` (cwd up to git root, then the skill dir) → `~/.env.local` / `~/.env` / `~/.dataforseo.env`. Only `DATAFORSEO_*` keys are read. No extra packages.

## Quick Start

```bash
python3 scripts/extract_ranked_keywords.py "https://www.uwarp.design/"
python3 scripts/extract_ranked_keywords.py "https://www.uwarp.design/" --mode tool-page
python3 scripts/extract_ranked_keywords.py "uwarp.design" --limit 50
```

竞品工具页复制场景，优先用 `--mode tool-page`（自动从 URL slug 解析 `{source}-to-{target}`）。

## Inputs

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `target_url` | String | 是 | — | 完整 URL 或域名 |
| `location_code` | Integer | 否 | `2840` | 地区代码（US） |
| `language_code` | String | 否 | `"en"` | 搜索语言 |
| `limit` | Integer | 否 | `100` | API 最大返回条数 |
| `sort` | String | 否 | `volume` | `volume` 或 `intent` |
| `mode` | String | 否 | `full` | `full` 全量；`tool-page` 工具页筛选 |
| `tool_pair` | String | 否 | 从 URL 解析 | 手动覆盖，如 `gif,jpg` |
| `max_position` | Integer | 否 | `20`（tool-page） | 最大排名位置 |
| `min_volume` | Integer | 否 | `300`（tool-page） | 最小月搜索量 |
| `min_traffic` | Float | 否 | `1`（tool-page） | 最小预估流量 (etv) |
| `max_kd` | Integer | 否 | `40`（tool-page） | 关键词难度上限（KD < 40） |
| `min_cpc` | Float | 否 | `0.2`（tool-page） | 最小 CPC（CPC >= 0.2） |

### `--mode tool-page` 筛选逻辑

1. **pair 解析**：从 path 最后一段匹配 `{source}-to-{target}`（如 `/gif-to-jpg` → gif,jpg）
2. **解析失败**：跳过 pair 筛选，仅应用 position / volume / traffic 阈值
3. **pair 匹配**：关键词须同时含源/目标别名；排除反向词（如 gif→jpg 页排除 `jpg to gif`）
4. **默认阈值**：position ≤ 20，volume ≥ 300，traffic ≥ 1，**KD < 40**，**CPC ≥ 0.2**

```bash
python3 scripts/extract_ranked_keywords.py "https://www.uwarp.design/" --mode tool-page
# 根路径无法解析 pair → 仅 position/volume/traffic 筛选
```

## API Protocol

**Endpoint:** `POST https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live`

### URL 解析

1. 去掉协议（`http://` / `https://`）与末尾多余 `/`
2. 去掉前缀 `www.`
3. 域名 → 请求字段 `target`（例：`uwarp.design`）
4. 相对路径 → filter（例：有 path 时才加；`https://www.uwarp.design/` 不设）
5. **纯根域名**（无 path 或 path 为 `/`）→ **不设** `relative_url` filter，查全站排名词

### Filter（有 path 时）

```json
["ranked_serp_element.serp_item.relative_url", "=", "/pricing"]
```

### 请求体示例

```json
[{
  "target": "uwarp.design",
  "location_code": 2840,
  "language_code": "en",
  "limit": 100,
  "order_by": ["keyword_data.keyword_info.search_volume,desc"]
}]
```

## Output Field Mapping

| 输出字段 | API 路径 | 说明 |
| --- | --- | --- |
| Keyword | `keyword_data.keyword` | 搜索关键词 |
| Intent | `keyword_data.search_intent_info.main_intent` | informational / navigational / commercial / transactional |
| Position | `ranked_serp_element.serp_item.rank_group` | SERP 排名 |
| Volume | `keyword_data.keyword_info.search_volume` | 月均搜索量 |
| KD % | `keyword_data.keyword_properties.keyword_difficulty` | 难度 0–100 |
| CPC | `keyword_data.keyword_info.cpc` | 单次点击成本 ($) |
| Traffic | `ranked_serp_element.serp_item.etv` | 预估月有机流量 |
| Competition | `keyword_data.keyword_info.competition` | 竞争度 0.00–1.00 |

> Traffic 使用 `etv`（estimated traffic volume）。`estimated_paid_traffic_cost` 是把该流量换成付费的预估美元成本，不是流量次数。

## Handling Rules

1. **URL 标准化**：去协议、去尾斜杠、去 `www.`；有 path 才加 `relative_url` filter。
2. **Empty State**：结果为空时返回（原话）：

   > 未查询到该 URL 的有效排名关键词，可能该页面属于新页面或未被搜索引擎充分收录。

3. **输出格式**：默认 Markdown 表格；按 `--sort volume`（默认）或 `--sort intent` 降序。
4. **Intent 排序**：transactional > commercial > navigational > informational > 未知。

## Agent Workflow

1. 确认 `target_url`（缺则向用户索取）
2. **做竞品同类工具页** → `--mode tool-page`；否则默认 `full`
3. 运行 `scripts/extract_ranked_keywords.py`
4. 将脚本 stdout 的 Markdown 表格呈现给用户
5. 可按需补充简要洞察 — 不要重复整表

## Additional resources

- API 细节见 [references/api-notes.md](references/api-notes.md)
