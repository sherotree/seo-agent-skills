---
name: competitor-backlink-gap-extractor
description: Extract high-quality competitor backlinks via DataForSEO Backlinks API, filter live/non-broken/non-UGC/high-rank/high-traffic referring domains (nofollow allowed), and optionally compute link intersection or backlink gap vs our site. Use when the user asks for competitor backlinks, backlink gap, link intersection, outreach list, or referring domains for a competitor URL or domain. Do not use for ranked keywords, site audits, GEO, or content optimization.
---

# Competitor Backlink Gap Extractor

独立 skill：只负责从竞品域名/页面提取高质量外链，并可选做 Intersection / Gap。不依赖、不调用其他 SEO/GEO skill。

## Prerequisites

```bash
export DATAFORSEO_LOGIN=your_login
export DATAFORSEO_PASSWORD=your_password
```

## Quick Start

```bash
python3 scripts/extract_backlink_gap.py "https://ezgif.com/gif-to-jpg"
python3 scripts/extract_backlink_gap.py ezgif.com cloudconvert.com --limit 300
python3 scripts/extract_backlink_gap.py ezgif.com --own uwarp.design
```

## Inputs

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `target` | String… | 是 | — | 一个或多个竞品域名或页面 URL |
| `own` | String | 否 | — | 己方域名；提供后计算 Gap（竞品有、己方无） |
| `limit` | Integer | 否 | `300` | 每个 target 最多返回条数（API max 1000） |
| `min_rank` | Integer | 否 | `30` | 源站 `domain_from_rank` 下限（0–100 标尺） |
| `min_etv` | Integer | 否 | `300` | 源站月自然流量下限（美国 `location_code: 2840`） |
| `mode` | String | 否 | `one_per_domain` | `one_per_domain` 适合 Outreach；`as_is` 返回全部链接 |

**允许 nofollow**；**排除 UGC**（API `attributes has_not ugc`，本地再丢一次）。`rel="sponsored"` 不在排除范围内。

## Mandatory filters

PRD 意图必须满足。Backlinks API **没有** `domain_stat.*` 字段，映射如下：

| PRD | 实际请求 |
| --- | --- |
| `is_lost = false` | `["is_lost", "=", false]` + `backlinks_status_type: "live"` |
| `is_broken = false` | `["is_broken", "=", false]` |
| nofollow allowed | 不设 `dofollow` 过滤 |
| 不要 UGC | `["attributes", "has_not", "ugc"]` + 本地 `attributes` 含 `ugc` 则丢弃 |
| `domain_stat.ranks.dataforseo > 30` | `["domain_from_rank", ">", 30]` + `rank_scale: "one_hundred"` |
| `domain_stat.organic.etv > 300`（美国） | 二次请求 Labs `bulk_traffic_estimation/live`（`location_code: 2840`），本地过滤 |
| `orderBy etv desc` | API 用 `order_by: ["domain_from_rank,desc"]`，拿到 etv 后再按流量降序 |

### Backlinks 请求体

```json
[{
  "target": "{{target_domain_or_url}}",
  "limit": 300,
  "mode": "one_per_domain",
  "backlinks_status_type": "live",
  "rank_scale": "one_hundred",
  "exclude_internal_backlinks": true,
  "order_by": ["domain_from_rank,desc"],
  "filters": [
    ["is_lost", "=", false],
    "and",
    ["is_broken", "=", false],
    "and",
    ["attributes", "has_not", "ugc"],
    "and",
    ["domain_from_rank", ">", 30]
  ]
}]
```

`target` 规则：纯域名去掉 `https://` 和 `www.`；带 path 的页面用完整 URL。

## Agent Workflow

1. 确认竞品 target（可多个）；Gap 场景再问己方 `--own`
2. 运行 `scripts/extract_backlink_gap.py`
3. 把 stdout 的 Markdown 表呈现给用户
4. 可补 2–4 条 Outreach 优先级（高 etv 优先）— 不要重复整表

## Empty State

> 未查询到符合条件的高质量外链。可能该目标外链过少，或源站权重/流量未达到阈值。

## Additional resources

- 字段映射与费用见 [references/api-notes.md](references/api-notes.md)
