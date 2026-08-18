#!/usr/bin/env python3
"""
Extract high-quality competitor backlinks via DataForSEO.

Usage:
  python3 scripts/extract_backlink_gap.py https://www.uwarp.design/
  python3 scripts/extract_backlink_gap.py https://www.uwarp.design/ --own uwarp.design
  python3 scripts/extract_backlink_gap.py https://www.uwarp.design/ --limit 300
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

BACKLINKS_ENDPOINT = "https://api.dataforseo.com/v3/backlinks/backlinks/live"
TRAFFIC_ENDPOINT = (
    "https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_traffic_estimation/live"
)

EMPTY_MESSAGE = (
    "未查询到符合条件的高质量外链。"
    "可能该目标外链过少，或源站权重/流量未达到阈值。"
)

DEFAULT_LIMIT = 300
DEFAULT_MIN_RANK = 30
DEFAULT_MIN_ETV = 300


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


def api_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    login, password = get_credentials()
    auth = base64.b64encode(f"{login}:{password}".encode()).decode()
    req = urllib.request.Request(
        url,
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


def extract_task_result(response: dict[str, Any]) -> dict[str, Any] | None:
    tasks = response.get("tasks") or []
    if not tasks:
        return None
    task = tasks[0]
    if task.get("status_code") != 20000:
        print(
            f"error: {task.get('status_message', 'Unknown error')}",
            file=sys.stderr,
        )
        return None
    results = task.get("result") or []
    if not results:
        return None
    return results[0]


def normalize_target(raw: str) -> str:
    """Domain without protocol/www; page URLs kept absolute."""
    text = raw.strip()
    if not text:
        raise ValueError("target is empty")

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
        return host

    if not path.startswith("/"):
        path = "/" + path
    return f"https://{host}{path}"


def host_from_target(target: str) -> str:
    if "://" in target:
        host = (urlparse(target).hostname or "").lower()
    else:
        host = target.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def referring_host(domain_from: str) -> str:
    host = (domain_from or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def quality_filters(min_rank: int) -> list[Any]:
    return [
        ["is_lost", "=", False],
        "and",
        ["is_broken", "=", False],
        "and",
        ["attributes", "has_not", "ugc"],
        "and",
        ["domain_from_rank", ">", min_rank],
    ]


def base_filters() -> list[Any]:
    return [
        ["is_lost", "=", False],
        "and",
        ["is_broken", "=", False],
        "and",
        ["attributes", "has_not", "ugc"],
    ]


def link_attributes(item: dict[str, Any]) -> list[str]:
    attrs = item.get("attributes") or []
    if isinstance(attrs, str):
        return [attrs.lower()]
    if isinstance(attrs, list):
        return [str(a).lower() for a in attrs if a]
    return []


def is_ugc_link(item: dict[str, Any]) -> bool:
    return "ugc" in link_attributes(item)


def fetch_backlinks(
    target: str,
    *,
    limit: int,
    min_rank: int,
    mode: str,
    apply_rank_filter: bool,
) -> list[dict[str, Any]]:
    task: dict[str, Any] = {
        "target": target,
        "limit": limit,
        "mode": mode,
        "backlinks_status_type": "live",
        "rank_scale": "one_hundred",
        "exclude_internal_backlinks": True,
        "order_by": ["domain_from_rank,desc"],
        "filters": (
            quality_filters(min_rank)
            if apply_rank_filter
            else base_filters()
        ),
    }
    result = extract_task_result(api_post(BACKLINKS_ENDPOINT, [task]))
    if not result:
        return []
    return result.get("items") or []


def fetch_organic_etv(domains: list[str]) -> dict[str, float]:
    unique: list[str] = []
    seen: set[str] = set()
    for domain in domains:
        host = referring_host(domain)
        if not host or host in seen:
            continue
        seen.add(host)
        unique.append(host)
    if not unique:
        return {}

    etv_by_host: dict[str, float] = {}
    for i in range(0, len(unique), 1000):
        chunk = unique[i : i + 1000]
        payload = [
            {
                "targets": chunk,
                "location_code": 2840,
                "language_code": "en",
                "item_types": ["organic"],
            }
        ]
        result = extract_task_result(api_post(TRAFFIC_ENDPOINT, payload))
        items = (result or {}).get("items") or []
        for item in items:
            host = referring_host(item.get("target") or "")
            metrics = ((item.get("metrics") or {}).get("organic")) or {}
            etv = metrics.get("etv")
            if host:
                etv_by_host[host] = float(etv or 0)
    return etv_by_host


def rel_label(item: dict[str, Any]) -> str:
    if item.get("dofollow"):
        return "dofollow"
    attrs = link_attributes(item)
    if attrs:
        return ",".join(attrs)
    return "nofollow"


def map_row(item: dict[str, Any], etv: float | None, competitor: str) -> dict[str, Any]:
    return {
        "competitor": competitor,
        "from_domain": referring_host(item.get("domain_from") or ""),
        "from_url": item.get("url_from") or "",
        "to_url": item.get("url_to") or "",
        "anchor": item.get("anchor") or "",
        "rel": rel_label(item),
        "rank": item.get("domain_from_rank"),
        "etv": etv,
        "first_seen": item.get("first_seen") or "",
    }


def fmt_num(value: Any, digits: int | None = None) -> str:
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
        if digits is not None:
            if number >= 1000:
                return f"{number:,.0f}"
            return f"{number:.{digits}f}"
        if number == int(number):
            return f"{int(number):,}"
        return f"{number:.1f}"
    except (TypeError, ValueError):
        return str(value)


def to_markdown(
    rows: list[dict[str, Any]],
    *,
    title: str,
    own_host: str | None,
    min_rank: int,
    min_etv: int,
) -> str:
    lines = [
        f"## {title}",
        "",
        f"Filters: live, not UGC, not broken, rank > {min_rank} (0–100), US etv > {min_etv}; nofollow allowed"
        + (f", gap vs `{own_host}`" if own_host else ""),
        "",
        f"Total: **{len(rows)}**",
        "",
        "| From domain | From URL | To URL | Anchor | Rel | Rank | ETV | First seen |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {from_domain} | {from_url} | {to_url} | {anchor} | {rel} | {rank} | {etv} | {first_seen} |".format(
                from_domain=(row["from_domain"] or "").replace("|", "\\|"),
                from_url=(row["from_url"] or "").replace("|", "\\|"),
                to_url=(row["to_url"] or "").replace("|", "\\|"),
                anchor=(row["anchor"] or "—").replace("|", "\\|")[:80],
                rel=row["rel"] or "—",
                rank=fmt_num(row["rank"]),
                etv=fmt_num(row["etv"], 0),
                first_seen=(row["first_seen"] or "—")[:10],
            )
        )
    return "\n".join(lines)


def to_csv(rows: list[dict[str, Any]]) -> str:
    header = "Competitor,From domain,From URL,To URL,Anchor,Rel,Rank,ETV,First seen"
    out = [header]
    for row in rows:
        out.append(
            ",".join(
                [
                    json.dumps(row.get("competitor") or "", ensure_ascii=False),
                    json.dumps(row["from_domain"], ensure_ascii=False),
                    json.dumps(row["from_url"], ensure_ascii=False),
                    json.dumps(row["to_url"], ensure_ascii=False),
                    json.dumps(row["anchor"], ensure_ascii=False),
                    json.dumps(row["rel"], ensure_ascii=False),
                    "" if row["rank"] is None else str(row["rank"]),
                    "" if row["etv"] is None else str(row["etv"]),
                    json.dumps(row["first_seen"], ensure_ascii=False),
                ]
            )
        )
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract high-quality competitor backlinks (DataForSEO)"
    )
    parser.add_argument("targets", nargs="+", help="Competitor domain(s) or page URL(s)")
    parser.add_argument("--own", help="Our domain for gap analysis")
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=DEFAULT_LIMIT,
        help="Max backlinks per target (default: 300, max: 1000)",
    )
    parser.add_argument(
        "--min-rank",
        type=int,
        default=DEFAULT_MIN_RANK,
        help="Min domain_from_rank on 0-100 scale (default: 30)",
    )
    parser.add_argument(
        "--min-etv",
        type=int,
        default=DEFAULT_MIN_ETV,
        help="Min referring-domain US organic etv (default: 300)",
    )
    parser.add_argument(
        "--mode",
        choices=("one_per_domain", "as_is"),
        default="one_per_domain",
        help="Backlink grouping (default: one_per_domain)",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "csv", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    try:
        targets = [normalize_target(t) for t in args.targets]
        own = normalize_target(args.own) if args.own else None
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    own_host = host_from_target(own) if own else None
    competitor_items: list[tuple[str, dict[str, Any]]] = []
    for target in targets:
        for item in fetch_backlinks(
            target,
            limit=min(args.limit, 1000),
            min_rank=args.min_rank,
            mode=args.mode,
            apply_rank_filter=True,
        ):
            competitor_items.append((target, item))

    own_hosts: set[str] = set()
    if own:
        for item in fetch_backlinks(
            own,
            limit=min(max(args.limit, 1000), 1000),
            min_rank=args.min_rank,
            mode="one_per_domain",
            apply_rank_filter=False,
        ):
            own_hosts.add(referring_host(item.get("domain_from") or ""))

    referring_domains = [item.get("domain_from") or "" for _, item in competitor_items]
    etv_by_host = fetch_organic_etv(referring_domains)

    rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for target, item in competitor_items:
        host = referring_host(item.get("domain_from") or "")
        if not host:
            continue
        if own_host and host == own_host:
            continue
        if own_hosts and host in own_hosts:
            continue
        if is_ugc_link(item):
            continue
        etv = etv_by_host.get(host, 0.0)
        if etv <= args.min_etv:
            continue
        key = (host, item.get("url_from") or "", item.get("url_to") or "")
        if key in seen_keys:
            continue
        seen_keys.add(key)
        rows.append(map_row(item, etv, target))

    rows.sort(key=lambda r: (-(r.get("etv") or 0), -(r.get("rank") or 0)))

    if not rows:
        print(EMPTY_MESSAGE)
        sys.exit(0)

    title = "Backlink gap" if own else "Competitor backlinks"
    scope = ", ".join(f"`{t}`" for t in targets)
    title = f"{title}: {scope}"

    if args.format == "csv":
        print(to_csv(rows))
    elif args.format == "json":
        print(
            json.dumps(
                {
                    "targets": targets,
                    "own": own,
                    "min_rank": args.min_rank,
                    "min_etv": args.min_etv,
                    "count": len(rows),
                    "backlinks": rows,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(
            to_markdown(
                rows,
                title=title,
                own_host=own_host,
                min_rank=args.min_rank,
                min_etv=args.min_etv,
            )
        )


if __name__ == "__main__":
    main()
