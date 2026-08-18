---
name: seo-keyword-content
description: Build and normalize SEO-rich tool directory content using keyword-driven rules, including long-tail phrase patterns and modifier vocabulary, for oneLiner, longDescription, whoItsFor, notFor, workflows, features, advantages, disadvantages, tips, and faqs.
---

# SEO Keyword Content Skill

Use this skill when a user asks to improve thin content for tool pages, expand programmatic SEO fields, or make data entries "keyword-driven."

**When to use**: thin or missing `longDescription` / `faqs`, generic `oneLiner`, repetitive bullets, keyword lists that lack intent mix, bulk normalization of tool JSON/TS data, or reviews of SEO field coverage before ship.

This skill is optimized for tool-directory style records. **Primary SEO-facing fields**:

- `title`
- `keywords`
- `oneLiner`
- `longDescription`
- `whoItsFor`
- `notFor`
- `workflows`
- `features`
- `advantages`
- `disadvantages`
- `tips`
- `faqs`

---

## Goal

Turn short, generic entries into useful, indexable, and differentiated content while avoiding keyword stuffing and repetitive template output.

---

## Core Principle

Keywords are a **writing anchor**, not a stuffing target.

- Use `keywords` to guide scope and search intent.
- Distribute terms naturally across sections.
- Prioritize clarity, specificity, and real decision value.

---

## Long-tail keywords (vocabulary and patterns)

Long-tail phrases are **specific, multi-word queries** (often 3–8 words) with clearer intent than head terms. Use them to anchor `keywords`, shape FAQ questions, and keep `oneLiner` / `longDescription` aligned with how people actually search—without stuffing the same string everywhere.

### When to prefer long-tail

- The tool serves a **narrow audience**, regulated workflow, or named integration.
- Head terms are **generic** and would not differentiate the page (`AI writer`, `image generator`).
- You need **commercial or evaluation intent** (pricing, migration, compliance, production readiness).

### Intent buckets (pick phrases that match real demand)

| Intent        | Typical long-tail signals                          | Good for fields                          |
| ------------- | -------------------------------------------------- | ---------------------------------------- |
| Informational | how to, what is, guide, tutorial, meaning          | `longDescription`, `faqs`, `tips`        |
| Commercial    | best for, vs, alternative, compare, pricing, ROI | `keywords`, `faqs`, `advantages`         |
| Transactional | free trial, sign up, demo, download, API key   | sparingly in copy; often landing CTAs    |
| Navigational  | brand + login, brand + docs, official            | usually not primary for tool-directory SEO |

### Reusable phrase patterns (templates)

Use `{tool}`, `{category}`, `{competitor}`, `{role}`, `{platform}`, `{constraint}` as placeholders. Mix **2–4 patterns** per record in `keywords` or related copy—not every pattern every time.

1. **Fit**: `{category} for {role}` · `{tool} for {role} workflows` · `{category} for {industry or team type}`
2. **Comparison**: `{tool} vs {competitor}` · `{tool} alternative` · `{tool} alternative to {competitor}` · `migrate from {competitor} to {tool}`
3. **Capability + context**: `{feature} for {use case}` · `{category} with {integration}` · `{category} without {pain point}` (e.g. watermark, code, lock-in)
4. **How-to / outcome**: `how to {outcome} with {category or tool}` · `{outcome} using {tool}`
5. **Commercial / buying**: `{tool} pricing` · `{category} pricing for teams` · `{tool} API pricing` · `{tool} enterprise` · `{tool} free tier limits`
6. **Trust / production**: `{tool} for production` · `{tool} security` · `{tool} SOC 2` · `{category} GDPR compliance` · `{tool} HIPAA` (only if accurate)
7. **Technical**: `{tool} API` · `{tool} SDK` · `{tool} webhook` · `{tool} SSO` · `{category} self-hosted` · `{tool} on-prem`
8. **Scale / maturity**: `{category} for startups` · `{tool} for enterprise` · `{category} for agencies` · `{tool} pilot checklist`

### Modifier vocabulary (swap in; keep factual)

- **Roles**: developers, marketers, founders, product managers, support teams, legal and compliance, educators, creators, analysts
- **Org size / model**: solo builders, small teams, SMB, mid-market, enterprise, agencies, multi-tenant products
- **Delivery**: cloud-hosted, self-hosted, hybrid, API-first, edge, batch, real-time
- **Product shape**: no-code, low-code, CLI, browser extension, desktop app, mobile app
- **Buying / usage**: usage-based pricing, seat-based, free tier, rate limits, SLAs, annual contract
- **Quality / ops**: audit logs, RBAC, SSO, data residency, retention policies, export, backup, review workflow
- **Industry / vertical** (when accurate): healthcare, finance, e-commerce, education, media, developer tooling, customer support, sales operations

### Question-shaped long-tail (map to `faqs`)

Mirror natural questions; keep answers specific.

- `What is {tool} best for?`
- `Can {tool} replace {competitor or category default}?`
- `Is {tool} suitable for {production / compliance / regulated context}?`
- `Does {tool} support {integration or file format}?`
- `Who should use {tool} first?`
- `How does {tool} pricing work for {teams / API / enterprise}?`

### Anti-patterns

- **Keyword trains**: one string stacking every modifier (`cheap best AI image generator for teams free no watermark API 2026`).
- **Synonym spam**: `AI writer, writing AI, writer AI, AI writing tool` as separate `keywords` with no new intent.
- **Inaccurate modifiers**: compliance, HIPAA, SOC 2, or integrations the product does not support.
- **Duplicating the title** across every field as the only “SEO” tactic.

---

## Suggested agent workflow

1. Read existing `name`, `slug`, `primaryCategory`, `tags`, and `keywords` (if any); infer primary intent and one differentiator.
2. Normalize or draft `keywords` using the long-tail mix rules; avoid overlapping near-duplicates.
3. Write `title` and `oneLiner` so they do not repeat the same clause; `oneLiner` carries the crisp value prop, `title` carries category + entity clarity.
4. Expand body fields (`longDescription`, lists, `faqs`) with distinct sentence openings and non-repeated templates.
5. Run **Quality gates**; fix any claim that is not supported by the tool’s real scope (integrations, compliance, platforms).

---

## Recommended Field Rules

### 1) `keywords`

- See **Long-tail keywords (vocabulary and patterns)** for phrase templates, intent buckets, and anti-patterns.
- Target: `3-6` hand-curated items for clarity; automated fallbacks may synthesize a longer list from `name` / `tags` / `platforms`.
- Mix:
  - Brand/entity keyword
  - Category keyword
  - Use-case keyword
  - Comparison keyword (`alternatives`, `vs`)
  - Commercial keyword (`pricing`, `best for`)
- Keep phrases concise and intent-bearing.

### 2) `title`

- Target: **`50-60` characters** when the same string feeds page metadata (`<title>`, Open Graph); if the surface is shorter, keep the **differentiator in the first ~45 characters** and do not go below **~35** characters if that would drop category signal.
- Structure: `Primary keyword + brand/tool name` (or reverse if brand-led query demand is stronger).
- Must be specific enough to differentiate from generic category pages.
- Avoid hype modifiers like "best", "ultimate", "top-tier" unless query intent explicitly requires comparison language.

### 3) `oneLiner`

- Target: `80-120` characters.
- Must include category + differentiator.
- Avoid vague phrases like "powerful AI tool."

### 4) `longDescription`

- Target: `120-220` words in `2` paragraphs.
- Paragraph 1: what it is + best-fit context.
- Paragraph 2: boundaries, rollout caveats, governance/review guidance.
- Prefer meeting depth manually: thin bodies may be padded by shared enrichers with generic copy—specific beats long.

### 5) `whoItsFor`

- Target: minimum `3` bullets.
- Each bullet should map role + scenario.
- Example pattern: "Marketing teams shipping weekly localized video updates."

### 6) `notFor`

- Target: minimum `2` bullets.
- State clear disqualifiers (compliance limits, infra mismatch, maturity limits).

### 7) `workflows`

- Target: minimum `4` steps.
- Action-first phrasing.
- Prefer operational sequence over abstract nouns.

### 8) `features`

- Target: minimum `4` bullets.
- Describe practical capabilities, not marketing adjectives.

### 9) `advantages`

- Target: minimum `3` bullets.
- Include concrete operator or team benefit.

### 10) `disadvantages`

- Target: minimum `3` bullets.
- Include realistic trade-offs (control, compliance, maturity, ecosystem lock-in).

### 11) `tips`

- Target: minimum `3` bullets.
- Provide actionable operator guidance (pilots, QA checklist, guardrails).

### 12) `faqs`

- Target: minimum `2` entries.
- Questions should follow search intent:
  - "What is X best for?"
  - "Can X replace Y?"
  - "Who should use X first?"
  - "Is X suitable for production?"
- Answers should be specific and include constraints when needed.

---

## Quality Gates

Before finishing:

1. **Coverage gate**

   - Each required field exists and meets minimum depth.

2. **Intent gate**

   - FAQ and descriptions reflect real query intent (`best for`, `alternatives`, `pricing`, `production fit`, `compliance`).

3. **Duplication gate**

   - Avoid repeating the same sentence structure across fields.

4. **Readability gate**

   - Keep sentence structure clear and factual.
   - Avoid hype wording.

5. **SEO safety gate**

   - No keyword stuffing.
   - Natural term placement and section-level differentiation.

6. **Claims / accuracy gate**

   - Compliance, certifications, integrations, and limits appear only when true for the product.
   - Prefer checkable facts (platforms, file types, auth methods) over broad superlatives.

7. **Cross-field coherence gate**

   - `keywords`, `whoItsFor`, `notFor`, and `faqs` describe the same product scope—no contradictions.
   - `title` / `oneLiner` / first FAQ should not restate the identical sentence.

---

## Implementation Pattern

When filling tool-directory JSON/TS records:

- Prefer shared enrichment logic for defaults.
- Keep hand-written rich entries as higher priority than generated fallback text.
- If you add or change an augmenter, it should:
  - Preserve rich manual fields.
  - Fill only thin/missing sections.
  - Keep tone and formatting consistent across datasets.

---

## Output Style

- English copy for page content fields.
- Concise and factual language.
- No exaggerated claims.
- Operationally useful guidance over generic product praise.
- Prefer **verifiable** scope (integrations, platforms, outputs, review steps) over vague quality claims.
