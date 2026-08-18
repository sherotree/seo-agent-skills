# SEO Agent Skills

Agent skills for competitor backlink research, ranked-keyword extraction, and keyword-driven tool-page copy.

Skills follow the [Agent Skills](https://agentskills.io/) format.

[![skills.sh](https://skills.sh/b/sherotree/seo-agent-skills)](https://skills.sh/sherotree/seo-agent-skills)

## Installation

```bash
npx skills add sherotree/seo-agent-skills
```

Install one skill:

```bash
npx skills add sherotree/seo-agent-skills --skill url-ranked-keywords-extractor
npx skills add sherotree/seo-agent-skills --skill competitor-backlink-gap-extractor
npx skills add sherotree/seo-agent-skills --skill seo-keyword-content
```

## Available skills

### url-ranked-keywords-extractor

Pull Google ranked keywords for a page or domain via DataForSEO Labs (`ranked_keywords/live`). Returns intent, position, volume, KD, CPC, traffic, and competition.

**Use when:** extracting ranking keywords for a specific URL, cloning a competitor tool page, or filtering `{source}-to-{target}` queries.

```bash
python3 scripts/extract_ranked_keywords.py "https://www.uwarp.design/"
python3 scripts/extract_ranked_keywords.py "https://www.uwarp.design/" --mode tool-page
```

### competitor-backlink-gap-extractor

Extract high-quality competitor backlinks (live, not broken, not UGC, high rank, high US organic traffic). Optionally compute a backlink gap against your own domain.

**Use when:** building an outreach list, finding referring domains, or comparing competitor vs own backlinks.

```bash
python3 scripts/extract_backlink_gap.py https://www.uwarp.design/
python3 scripts/extract_backlink_gap.py https://www.uwarp.design/ --own uwarp.design
```

### seo-keyword-content

Write and normalize SEO-rich tool-directory fields: `title`, `keywords`, `oneLiner`, `longDescription`, `whoItsFor`, `notFor`, `workflows`, `features`, `advantages`, `disadvantages`, `tips`, and `faqs`.

**Use when:** thin tool pages, programmatic SEO records, or keyword-driven copy that must stay specific without stuffing.

## Prerequisites

The two DataForSEO extractors need API credentials. Put them in `.env.local` at the project or git root. Shell `export` still works and takes precedence.

```bash
# .env.local
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
```

Do not commit that file. Add `.env` / `.env.*` to the **consuming** repo's `.gitignore` — installing this pack does not gitignore secrets in your project. Keep credentials out of the skill directory, and do not paste `.env.local` into chat.

`seo-keyword-content` is markdown-only and does not call an API.

## License

MIT
