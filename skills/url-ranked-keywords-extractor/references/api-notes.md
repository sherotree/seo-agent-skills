# DataForSEO Ranked Keywords — Notes

## Endpoint

`POST https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live`

Docs: https://docs.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live/

## Page vs domain

| 输入 | `target` | `filters` |
| --- | --- | --- |
| `https://www.uwarp.design/` | `uwarp.design` | 无（全站） |
| `uwarp.design` | `uwarp.design` | 无（全站） |

`relative_url` 不含协议与域名，须以 `/` 开头。

## Intent path correction

PRD 曾写 `keyword_data.keyword_info.search_intent_info.main_intent`。

实际响应中 `search_intent_info` 与 `keyword_info` 同级，位于 `keyword_data` 下：

```text
keyword_data.search_intent_info.main_intent
```

Values: `informational` | `navigational` | `commercial` | `transactional`

## Traffic vs paid cost

| Field | Meaning |
| --- | --- |
| `serp_item.etv` | 预估月有机流量（本 skill 的 Traffic） |
| `serp_item.estimated_paid_traffic_cost` | 将 etv 换成 PPC 的预估美元成本 |

## Auth

HTTP Basic: `DATAFORSEO_LOGIN`:`DATAFORSEO_PASSWORD`

Credentials come from the environment, or from `.env.local` / `.env` (see SKILL.md). Existing env vars win.
