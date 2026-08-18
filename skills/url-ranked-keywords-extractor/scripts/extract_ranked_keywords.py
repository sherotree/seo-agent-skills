#!/usr/bin/env python3
"""
Extract Google ranked keywords for a URL via DataForSEO Labs API.

Usage:
  python3 scripts/extract_ranked_keywords.py "https://www.uwarp.design/"
  python3 scripts/extract_ranked_keywords.py "uwarp.design" --limit 50 --sort volume
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

API_ENDPOINT = "https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live"

EMPTY_MESSAGE = (
    "未查询到该 URL 的有效排名关键词，"
    "可能该页面属于新页面或未被搜索引擎充分收录。"
)

INTENT_RANK = {
    "transactional": 0,
    "commercial": 1,
    "navigational": 2,
    "informational": 3,
}

# Extra aliases beyond the slug token itself (lowercase).
FORMAT_ALIASES: dict[str, list[str]] = {
    "gif": ["gif", "gifs", "animated gif"],
    "jpg": ["jpg", "jpeg", "jpegs", "jif"],
    "jpeg": ["jpg", "jpeg", "jpegs", "jif"],
    "png": ["png"],
    "pdf": ["pdf"],
    "cbr": ["cbr"],
    "mp4": ["mp4"],
    "avif": ["avif"],
    "webp": ["webp"],
    "video": ["video", "videos"],
}

# When converting animated GIF to a still image, users often say image/picture/photo.
GIF_TO_STILL_TARGETS = ["image", "images", "picture", "pictures", "photo", "photos"]

TOOL_PAGE_DEFAULTS = {
    "max_position": 20,
    "min_volume": 300,
    "min_traffic": 1.0,
    "max_kd": 40,
    "min_cpc": 0.2,
}


def get_credentials() -> tuple[str, str]:
    login = os.environ.get("DATAFORSEO_LOGIN", "")
    password = os.environ.get("DATAFORSEO_PASSWORD", "")
    if not login or not password:
        print(
            "error: DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD not set\n"
            "Run: export DATAFORSEO_LOGIN=your_login\n"
            "     export DATAFORSEO_PASSWORD=your_password",
            file=sys.stderr,
        )
        sys.exit(1)
    return login, password


def normalize_url(raw: str) -> tuple[str, str | None]:
    """
    Return (domain, relative_url_or_None).
    Root domain / path '/' => no relative_url filter.
    """
    text = raw.strip()
    if not text:
        raise ValueError("target_url is empty")

    if "://" not in text:
        text = "https://" + text

    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        raise ValueError(f"cannot parse domain from: {raw}")

    path = parsed.path or ""
    if path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")

    if not path or path == "/":
        return host, None

    if not path.startswith("/"):
        path = "/" + path
    return host, path


def slug_from_path(path: str | None) -> str | None:
    if not path or path == "/":
        return None
    return path.rstrip("/").split("/")[-1].lower()


def parse_tool_pair_from_slug(slug: str | None) -> tuple[str, str] | None:
    """Parse `{source}-to-{target}` from URL slug. Returns None if not matched."""
    if not slug:
        return None
    match = re.fullmatch(r"(.+)-to-(.+)", slug)
    if not match:
        return None
    source, target = match.group(1).strip(), match.group(2).strip()
    if not source or not target:
        return None
    return source, target


def parse_tool_pair_override(raw: str) -> tuple[str, str]:
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    if len(parts) != 2:
        raise ValueError("--tool-pair must be SOURCE,TARGET (e.g. gif,jpg)")
    return parts[0], parts[1]


def aliases_for_format(token: str) -> list[str]:
    token = token.lower()
    aliases = list(FORMAT_ALIASES.get(token, [token]))
    if token not in aliases:
        aliases.insert(0, token)
    # dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for alias in aliases:
        if alias not in seen:
            seen.add(alias)
            out.append(alias)
    return out


def build_pair_aliases(source: str, target: str) -> tuple[list[str], list[str]]:
    source_aliases = aliases_for_format(source)
    target_aliases = aliases_for_format(target)
    if source in {"gif", "gifs"} and target in {"jpg", "jpeg", "jif"}:
        for extra in GIF_TO_STILL_TARGETS:
            if extra not in target_aliases:
                target_aliases.append(extra)
    return source_aliases, target_aliases


def _contains_alias(keyword: str, aliases: list[str]) -> bool:
    kw = keyword.lower()
    for alias in aliases:
        if " " in alias:
            if alias in kw:
                return True
        elif re.search(rf"\b{re.escape(alias)}\b", kw):
            return True
    return False


def is_reverse_keyword(keyword: str, source_aliases: list[str], target_aliases: list[str]) -> bool:
    """Reject keywords describing the opposite conversion (e.g. jpg to gif)."""
    kw = keyword.lower()
    for target in target_aliases:
        for source in source_aliases:
            patterns = (
                rf"\b{re.escape(target)}\b.*\bto\b.*\b{re.escape(source)}\b",
                rf"\b{re.escape(target)}\b.*\b2\b.*\b{re.escape(source)}\b",
                rf"\b{re.escape(target)}\b.*\binto\b.*\b{re.escape(source)}\b",
            )
            for pattern in patterns:
                if re.search(pattern, kw):
                    return True
    return False


def matches_tool_pair(
    keyword: str,
    source_aliases: list[str],
    target_aliases: list[str],
) -> bool:
    if not _contains_alias(keyword, source_aliases):
        return False
    if not _contains_alias(keyword, target_aliases):
        return False
    if is_reverse_keyword(keyword, source_aliases, target_aliases):
        return False
    return True


def filter_tool_page_rows(
    rows: list[dict[str, Any]],
    *,
    tool_pair: tuple[str, str] | None,
    max_position: int,
    min_volume: int,
    min_traffic: float,
    max_kd: int,
    min_cpc: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_aliases: list[str] = []
    target_aliases: list[str] = []
    if tool_pair:
        source_aliases, target_aliases = build_pair_aliases(tool_pair[0], tool_pair[1])

    filtered: list[dict[str, Any]] = []
    for row in rows:
        position = row.get("position")
        volume = row.get("volume")
        traffic = row.get("traffic")
        kd = row.get("kd")
        cpc = row.get("cpc")

        if position is None or int(position) > max_position:
            continue
        if volume is None or int(volume) < min_volume:
            continue
        if traffic is None or float(traffic) < min_traffic:
            continue
        if kd is None or int(kd) >= max_kd:
            continue
        if cpc is None or float(cpc) < min_cpc:
            continue
        if tool_pair and not matches_tool_pair(
            row.get("keyword") or "", source_aliases, target_aliases
        ):
            continue
        filtered.append(row)

    meta = {
        "mode": "tool-page",
        "tool_pair": f"{tool_pair[0]}→{tool_pair[1]}" if tool_pair else None,
        "max_position": max_position,
        "min_volume": min_volume,
        "min_traffic": min_traffic,
        "max_kd": max_kd,
        "min_cpc": min_cpc,
        "before_count": len(rows),
        "after_count": len(filtered),
    }
    return filtered, meta


def api_post(payload: list[dict[str, Any]]) -> dict[str, Any]:
    login, password = get_credentials()
    auth = base64.b64encode(f"{login}:{password}".encode()).decode()
    req = urllib.request.Request(
        API_ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"error: HTTP {e.code} - {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def extract_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = response.get("tasks") or []
    if not tasks:
        return []
    task = tasks[0]
    if task.get("status_code") != 20000:
        print(
            f"error: {task.get('status_message', 'Unknown error')}",
            file=sys.stderr,
        )
        return []
    results = task.get("result") or []
    if not results:
        return []
    return results[0].get("items") or []


def map_row(item: dict[str, Any]) -> dict[str, Any]:
    kd = item.get("keyword_data") or {}
    info = kd.get("keyword_info") or {}
    props = kd.get("keyword_properties") or {}
    intent_info = kd.get("search_intent_info") or {}
    serp = ((item.get("ranked_serp_element") or {}).get("serp_item")) or {}

    intent = intent_info.get("main_intent") or ""
    return {
        "keyword": kd.get("keyword") or "",
        "intent": intent,
        "position": serp.get("rank_group"),
        "volume": info.get("search_volume"),
        "kd": props.get("keyword_difficulty"),
        "cpc": info.get("cpc"),
        "traffic": serp.get("etv"),
        "competition": info.get("competition"),
    }


def sort_rows(rows: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    if sort_by == "intent":
        return sorted(
            rows,
            key=lambda r: (
                INTENT_RANK.get(str(r.get("intent") or "").lower(), 99),
                -(r.get("volume") or 0),
            ),
        )
    return sorted(rows, key=lambda r: -(r.get("volume") or 0))


def fmt_num(value: Any, digits: int | None = None) -> str:
    if value is None or value == "":
        return "—"
    try:
        if digits is not None:
            return f"{float(value):.{digits}f}"
        if isinstance(value, float):
            if value == int(value):
                return str(int(value))
            return f"{value:.2f}"
        return str(value)
    except (TypeError, ValueError):
        return str(value)


def to_markdown(
    rows: list[dict[str, Any]],
    domain: str,
    path: str | None,
    filter_meta: dict[str, Any] | None = None,
) -> str:
    scope = f"{domain}{path}" if path else domain
    lines = [f"## Ranked keywords: `{scope}`", ""]
    if filter_meta:
        pair = filter_meta.get("tool_pair")
        pair_text = pair if pair else "未解析（仅 position/volume/traffic 筛选）"
        lines.extend(
            [
                f"Mode: **tool-page** | pair: `{pair_text}` | "
                f"position ≤ {filter_meta['max_position']}, "
                f"volume ≥ {filter_meta['min_volume']}, "
                f"traffic ≥ {filter_meta['min_traffic']}, "
                f"KD < {filter_meta['max_kd']}, "
                f"CPC ≥ {filter_meta['min_cpc']}",
                "",
                f"Filtered: **{filter_meta['before_count']} → {filter_meta['after_count']}**",
                "",
            ]
        )
    lines.extend(
        [
            f"Total: **{len(rows)}**",
            "",
            "| Keyword | Intent | Position | Volume | KD % | CPC | Traffic | Competition |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for r in rows:
        lines.append(
            "| {keyword} | {intent} | {position} | {volume} | {kd} | {cpc} | {traffic} | {competition} |".format(
                keyword=(r["keyword"] or "").replace("|", "\\|"),
                intent=r["intent"] or "—",
                position=fmt_num(r["position"]),
                volume=fmt_num(r["volume"]),
                kd=fmt_num(r["kd"]),
                cpc=fmt_num(r["cpc"], 2),
                traffic=fmt_num(r["traffic"], 1),
                competition=fmt_num(r["competition"], 2),
            )
        )
    return "\n".join(lines)


def to_csv(rows: list[dict[str, Any]]) -> str:
    header = "Keyword,Intent,Position,Volume,KD %,CPC,Traffic,Competition"
    out = [header]
    for r in rows:
        out.append(
            ",".join(
                [
                    json.dumps(r["keyword"] or "", ensure_ascii=False),
                    str(r["intent"] or ""),
                    "" if r["position"] is None else str(r["position"]),
                    "" if r["volume"] is None else str(r["volume"]),
                    "" if r["kd"] is None else str(r["kd"]),
                    "" if r["cpc"] is None else str(r["cpc"]),
                    "" if r["traffic"] is None else str(r["traffic"]),
                    "" if r["competition"] is None else str(r["competition"]),
                ]
            )
        )
    return "\n".join(out)


def build_payload(
    domain: str,
    relative_url: str | None,
    location_code: int,
    language_code: str,
    limit: int,
    sort_by: str,
) -> list[dict[str, Any]]:
    if sort_by == "intent":
        # API has no intent order_by; we sort client-side. Prefetch by volume.
        order_by = ["keyword_data.keyword_info.search_volume,desc"]
    else:
        order_by = ["keyword_data.keyword_info.search_volume,desc"]

    task: dict[str, Any] = {
        "target": domain,
        "location_code": location_code,
        "language_code": language_code,
        "limit": limit,
        "order_by": order_by,
    }
    if relative_url:
        task["filters"] = [
            "ranked_serp_element.serp_item.relative_url",
            "=",
            relative_url,
        ]
    return [task]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Google ranked keywords for a URL (DataForSEO)"
    )
    parser.add_argument("target_url", help="Page URL or domain")
    parser.add_argument(
        "--location",
        "-loc",
        type=int,
        default=2840,
        help="Location code (default: 2840 = US)",
    )
    parser.add_argument(
        "--language",
        "-lang",
        default="en",
        help="Language code (default: en)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=50,
        help="Max keywords (default: 50)",
    )
    parser.add_argument(
        "--sort",
        choices=("volume", "intent"),
        default="volume",
        help="Sort by volume (default) or intent",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "csv", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--mode",
        choices=("full", "tool-page"),
        default="full",
        help="full: all ranked keywords; tool-page: filter for cloneable tool pages",
    )
    parser.add_argument(
        "--tool-pair",
        help="Override SOURCE,TARGET (e.g. gif,jpg). Default: parse from URL slug",
    )
    parser.add_argument(
        "--max-position",
        type=int,
        help="tool-page: max SERP position (default: 20)",
    )
    parser.add_argument(
        "--min-volume",
        type=int,
        help="tool-page: min monthly search volume (default: 300)",
    )
    parser.add_argument(
        "--min-traffic",
        type=float,
        help="tool-page: min estimated traffic etv (default: 1)",
    )
    parser.add_argument(
        "--max-kd",
        type=int,
        help="tool-page: max keyword difficulty, exclusive (default: 40, i.e. KD < 40)",
    )
    parser.add_argument(
        "--min-cpc",
        type=float,
        help="tool-page: min CPC (default: 0.2)",
    )
    args = parser.parse_args()

    max_position = args.max_position
    min_volume = args.min_volume
    min_traffic = args.min_traffic
    max_kd = args.max_kd
    min_cpc = args.min_cpc
    if args.mode == "tool-page":
        if max_position is None:
            max_position = TOOL_PAGE_DEFAULTS["max_position"]
        if min_volume is None:
            min_volume = TOOL_PAGE_DEFAULTS["min_volume"]
        if min_traffic is None:
            min_traffic = TOOL_PAGE_DEFAULTS["min_traffic"]
        if max_kd is None:
            max_kd = TOOL_PAGE_DEFAULTS["max_kd"]
        if min_cpc is None:
            min_cpc = TOOL_PAGE_DEFAULTS["min_cpc"]

    try:
        domain, relative_url = normalize_url(args.target_url)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    payload = build_payload(
        domain=domain,
        relative_url=relative_url,
        location_code=args.location,
        language_code=args.language,
        limit=args.limit,
        sort_by=args.sort,
    )
    response = api_post(payload)
    items = extract_items(response)
    rows = sort_rows([map_row(i) for i in items], args.sort)

    filter_meta: dict[str, Any] | None = None
    if args.mode == "tool-page":
        tool_pair: tuple[str, str] | None = None
        if args.tool_pair:
            try:
                tool_pair = parse_tool_pair_override(args.tool_pair)
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            slug = slug_from_path(relative_url)
            tool_pair = parse_tool_pair_from_slug(slug)

        rows, filter_meta = filter_tool_page_rows(
            rows,
            tool_pair=tool_pair,
            max_position=max_position,
            min_volume=min_volume,
            min_traffic=min_traffic,
            max_kd=max_kd,
            min_cpc=min_cpc,
        )

    if not rows:
        print(EMPTY_MESSAGE)
        sys.exit(0)

    if args.format == "csv":
        print(to_csv(rows))
    elif args.format == "json":
        payload_out: dict[str, Any] = {
            "target": domain,
            "relative_url": relative_url,
            "count": len(rows),
            "keywords": rows,
        }
        if filter_meta:
            payload_out["filter"] = filter_meta
        print(json.dumps(payload_out, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(rows, domain, relative_url, filter_meta))


if __name__ == "__main__":
    main()
