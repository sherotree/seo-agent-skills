# API notes

## Endpoints

1. `POST https://api.dataforseo.com/v3/backlinks/backlinks/live`
2. `POST https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_traffic_estimation/live`

Docs:

- https://docs.dataforseo.com/v3/backlinks/backlinks/live/
- https://docs.dataforseo.com/v3/backlinks/filters/
- https://docs.dataforseo.com/v3/dataforseo_labs/google/bulk_traffic_estimation/live/

## Why two calls

`backlinks/backlinks/live` 可过滤 `is_lost` / `is_broken` / `attributes` / `domain_from_rank`，**不能**按源站 organic etv 过滤，响应里也没有 `domain_stat`。

源站月流量来自 Labs Bulk Traffic Estimation：`items[].metrics.organic.etv`。默认 `location_code: 2840`（美国）+ `language_code: en`。

UGC 排除：`["attributes", "has_not", "ugc"]`（[filters 文档](https://dataforseo.com/help-center/using-filters)）。nofollow 不过滤；脚本对 `attributes` 含 `ugc` 再丢一次。

## Rank scale

默认 rank 是 0–1000。PRD 的 `> 30` 按 0–100 理解，因此请求必须带 `"rank_scale": "one_hundred"`。

## Output mapping

| 输出 | 来源 |
| --- | --- |
| From domain | `domain_from` |
| From URL | `url_from` |
| To URL | `url_to` |
| Anchor | `anchor` |
| Rel | `dofollow` + `attributes` |
| Rank | `domain_from_rank`（0–100） |
| ETV | Labs `metrics.organic.etv` |
| First seen | `first_seen` |

## Cost (approx)

| 调用 | 计费 |
| --- | --- |
| backlinks/live | $0.024 + $0.000036 × 返回行数 ≈ **$0.035 / 300 行** |
| bulk_traffic_estimation | Labs All Other：$0.012 + $0.00012 × 域名数 ≈ **$0.048 / 300 域名** |

每个竞品 target：**1 次 backlinks**。全部 unique 源域名合计：**1 次 bulk traffic**（最多 1000 个域名/次）。`--own` 再加 **1 次 backlinks**。满额 300 行大约 **$0.08 / 次**。
