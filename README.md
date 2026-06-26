# course-market-intelligence-mcp

A **compliance-first** MCP (Model Context Protocol) server that helps a course
team validate whether a proposed online course topic is worth creating in
today's market. Given a topic, it researches demand, trends, competition,
job-market relevance, learner pain points and market gaps **across compliant
sources only**, then returns a decision-ready market validation report with a
**go / no-go verdict, transparent scores and confidence levels**.

It is designed for use inside Claude (Desktop, or any MCP client) over **stdio**.

---

## 1. What this MCP does

For a manager-assigned course topic it answers:

1. Is the topic trending right now?
2. Is there learner demand?
3. Is there job-market / professional upskilling demand?
4. How competitive is the marketplace?
5. What are competitor prices, ratings, reviews, durations, enrollments, positioning?
6. Which subtopics are valuable and commonly covered?
7. Which valuable subtopics are **missing**?
8. What is the likely revenue potential?
9. What title, outline, duration, projects and outcomes should we build?
10. Should we **create, delay, modify or reject** the course?

It produces `report.md`, `report.json`, an optional `report.html`, and CSV
exports (competitors, keywords, SEO metrics, trends, job-market, gaps, revenue,
source audit).

Target platforms considered: **Udemy, Coursera, LinkedIn Learning, Go1, edX,
FutureLearn, Edflex, Class Central, YouTube, corporate/B2B LMS marketplaces**,
and other public discovery platforms — each only through allowed modes.

## 2. What this MCP does NOT do

It is built to **refuse** anything non-compliant. It never:

- bypasses logins, paywalls, CAPTCHAs or anti-bot protections;
- uses proxy rotation, stealth fingerprinting, or any evasion;
- steals cookies/sessions or automates logins for scraping;
- scrapes private, paid or restricted content;
- copies course videos, transcripts, assignments, quizzes, certificates or paid assets;
- collects personal data about learners or instructors;
- violates `robots.txt` or known platform restrictions.

If a source can't be collected compliantly, the run **skips it** and records why
in the source audit.

## 3. Compliance-first data collection

Every fetch passes through a compliance gate driven by [`source_policy.yaml`](./source_policy.yaml):

| Mode | Meaning |
|---|---|
| `official_api` | Official / approved vendor API |
| `affiliate_api` / `partner_api` | Affiliate or approved partner programs (e.g. Udemy Affiliate) |
| `search_api` | Compliant search APIs (Google CSE, Bing, SerpAPI, DataForSEO SERP) |
| `seo_api` | Approved SEO/trend APIs or exports (Semrush, Ahrefs, DataForSEO, …) |
| `public_metadata` | Allowed public page metadata — **only** after `robots.txt` + ToS checks pass |
| `manual_csv` | User-uploaded CSV/XLSX export from restricted platforms |
| `internal_data` | Company-owned internal data upload |

- Unknown domains default to **least privilege** (`search_api`, `manual_csv`, `internal_data`).
- `linkedin.com`, `youtube.com`, `google.com`, `bing.com` never allow public scraping.
- `coursera.org` public scraping is blocked **unless written permission is confirmed**.
- Public-metadata fetches additionally check `robots.txt` for our user agent before any request.

## 4. Setup

```bash
# clone, then from the repo root:
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"          # or: uv sync

cp .env.example .env             # fill in whatever API keys you have (all optional)
```

Run the test suite:

```bash
pytest -q
ruff check src tests
```

> The server works with **zero API keys** — it degrades gracefully to estimated
> buckets and clearly labels everything as estimated/unavailable. Add keys and/or
> manual CSV exports to raise confidence.

## 5. Environment variables

See [`.env.example`](./.env.example). All are optional; missing keys cause the
relevant connector to be skipped (recorded in the source audit).

Search: `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ENGINE_ID`, `BING_SEARCH_API_KEY`,
`SERPAPI_KEY`, `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` ·
SEO/trend: `SEMRUSH_API_KEY`, `AHREFS_API_KEY`, `MOZ_API_KEY`, `SIMILARWEB_API_KEY` ·
Platform: `YOUTUBE_API_KEY`, `UDEMY_CLIENT_ID`, `UDEMY_CLIENT_SECRET`,
`COURSERA_API_KEY`, `GO1_API_KEY` · Social: `REDDIT_CLIENT_ID`,
`REDDIT_CLIENT_SECRET` · Jobs: `JOBS_API_KEY` (+ optional `JOBS_API_URL`).

Runtime: `CACHE_TTL_HOURS=72`, `MAX_RESULTS_PER_SOURCE=25`,
`DEFAULT_RATE_LIMIT_SECONDS=2`, `EXPORT_DIR=data/exports`,
`DATABASE_URL=sqlite:///data/research_cache.sqlite`.

## 6. Claude Desktop configuration

Add to `claude_desktop_config.json` (full example in
[`examples/claude_desktop_config.json`](./examples/claude_desktop_config.json)):

```json
{
  "mcpServers": {
    "course-market-intelligence": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/course-market-intelligence-mcp",
               "run", "course-market-intelligence"],
      "env": {
        "GOOGLE_CSE_API_KEY": "your_key_here",
        "BING_SEARCH_API_KEY": "your_key_here",
        "YOUTUBE_API_KEY": "your_key_here"
      }
    }
  }
}
```

Using a plain venv instead of `uv`? Use
`"command": "/ABSOLUTE/PATH/.venv/bin/course-market-intelligence", "args": []`.

## 7. Example usage prompts

Reusable researcher prompt:

```
Validate this course idea:

TOPIC: [Insert topic]
WORKING TITLE: [Insert title if available]
GOAL: [e.g. help learners get entry-level jobs, upskill professionals, train managers, compliance]
TARGET LEARNER:
  Profile:
  Background:
  Motivation:
TARGET REGIONS: [US, UK, EMEA, India, Global, ...]
PLATFORMS: [Udemy, Coursera, LinkedIn Learning, Go1, edX, FutureLearn, internal LMS]
TIMEFRAME: [Launch in 2-3 months, Q4, summer campaign, ...]
DEPTH: [quick, standard, deep]
SPECIAL REQUIREMENTS: [AI angle, B2B angle, certification angle, job-ready focus, short course, ...]

Return: demand analysis, SEO/search behavior, trend analysis, competitor courses,
duration & pricing benchmarks, estimated revenue scenarios, valuable subtopics,
missing market subtopics, course outline, differentiation strategy, final go/no-go.
```

Other handy calls: *"Check source policy for udemy.com with mode affiliate_api"*,
*"Import this competitors CSV for LinkedIn Learning"*, *"Find market gaps for X
given this competitor analysis"*.

## 8. Supported sources

Course marketplaces: Udemy, Coursera, edX, FutureLearn, Class Central · B2B
learning: LinkedIn Learning, Go1, Edflex · Video: YouTube · Search: Google CSE,
Bing, SerpAPI, DataForSEO · SEO/trend: Semrush, Ahrefs, Moz, Similarweb,
DataForSEO, Google-Trends/Exploding-Topics exports · Social: Reddit (API), search
snippets · Jobs: configurable jobs API + manual exports.

## 9. Sources that require API keys

Udemy (affiliate), Coursera (partner), Go1 (partner/customer), YouTube, Google
CSE, Bing, SerpAPI, DataForSEO, Semrush, Ahrefs, Moz, Similarweb, Reddit, jobs
API. Without a key the connector is **skipped** and noted in the audit.

## 10. Platforms that should use manual CSV import

- **LinkedIn Learning** — manual CSV only (scraping restricted).
- **Coursera** — manual CSV / partner API (no scraping without written consent).
- **Edflex** and other aggregators — partner/customer export or manual CSV.
- **Most job boards** — manual export or an approved jobs API.

## 11. How to import manual data

1. Export data from the platform you are authorized to use (CSV/XLSX).
2. Drop it in `data/manual_uploads/` (or pass an absolute path).
3. Call the `import_manual_data` tool, e.g.
   `import_type="competitor_courses", file_path="sample_competitors_udemy.csv"`.

Supported import types: `competitor_courses`, `keyword_metrics`, `seo_metrics`,
`job_market_data`, `platform_pricing`, `course_reviews_summary`,
`internal_sales_data`, `internal_lms_data`, `trend_exports`,
`course_catalog_exports`. Column names are auto-mapped from common aliases; see
[`examples/sample_competitors_udemy.csv`](./examples/sample_competitors_udemy.csv).

To feed manual data into a full run, pass a `manual_data` object to
`research_course_topic`, e.g.:

```json
{
  "topic": "Data Analytics",
  "manual_data": {
    "competitor_courses_by_platform": {"LinkedIn Learning": "data/manual_uploads/li.csv"},
    "seo_metrics": "data/manual_uploads/seo.csv",
    "job_market_data": "data/manual_uploads/jobs.csv"
  }
}
```

## 12. How to read the generated reports

Reports land in `data/exports/<topic-slug>_*`:

- `_report.md` — full narrative (14 sections) + summary table + source audit.
- `_report.json` — the complete machine-readable context.
- `_report.html` — shareable scorecard view.
- `_competitors.csv`, `_keywords.csv`, `_seo_metrics.csv`, `_trend_signals.csv`,
  `_job_market_signals.csv`, `_gaps.csv`, `_revenue_model.csv`, `_source_audit.csv`.

The **summary table** gives the verdict at a glance; the **source audit** shows
exactly which sources were used vs. skipped and why.

## 13. How scoring works

All scores are 0–100 with transparent, fixed weights (see
[`analysis/scoring.py`](./src/course_market_intelligence/analysis/scoring.py)):

- **Demand** = keyword demand 25% · trend growth 20% · job-market 20% ·
  competitor proof-of-demand 15% · B2B relevance 10% · timing 10%.
- **Competition risk** (higher = worse) = strong competitors 25% ·
  review/enrollment concentration 20% · brand strength 20% · saturation 20% ·
  differentiation difficulty 15%.
- **Gap** = missing high-value subtopics 25% · missing job skills 20% ·
  missing AI/tooling 15% · missing projects 15% · regional/B2B 15% · freshness 10%.
- **Revenue** = marketplace demand 25% · B2C pricing 15% · B2B licensing 25% ·
  conversion 15% · repeat/team 10% · competition-adjusted upside 10%.
- **Overall** = demand 35% · gap 25% · revenue 25% · inverse competition risk 15%.

**Decision rules:** `strong_go` (high demand+gap, OK revenue, manageable
competition) · `conditional_go` (viable but needs differentiation) ·
`hold_research_more` (low confidence / unclear signals) · `no_go` (weak
demand+revenue, high competition, no clear gap).

## 14. How confidence works

Every major claim carries a confidence level:

- **high** — directly from an approved API, official source, or clean user CSV.
- **medium** — inferred from multiple public signals.
- **low** — estimated from weak/incomplete/indirect data.

The report clearly labels exact vs. estimated vs. unavailable data, plus
assumptions, skipped sources and compliance limitations. Low overall confidence
biases the verdict toward `hold_research_more`.

## 15. Legal / compliance review checklist

- [ ] Confirm you have rights/keys for each enabled API (Udemy, Coursera, Go1, etc.).
- [ ] For Coursera public access, confirm **written permission** before enabling any non-API mode.
- [ ] Keep `source_policy.yaml` aligned with each platform's current Terms of Service.
- [ ] Verify `robots.txt` checks remain enabled for any `public_metadata` use.
- [ ] Ensure no personal data (learner/instructor) is stored — only aggregates.
- [ ] Ensure no paid/copyrighted course content is copied — only summarized signals/metadata.
- [ ] Review the generated `_source_audit.csv` for every run.
- [ ] Have legal sign off on manual-export sources and internal data usage.

## 16. Troubleshooting

- **"providers skipped"** — expected without keys; add API keys or manual CSVs.
- **Verdict is always `hold_research_more`** — confidence is low; provide verified
  data (Udemy Affiliate API or manual exports + SEO volumes).
- **Claude Desktop shows no tools** — check the absolute path in the config and
  that `uv`/the venv entry point runs; logs go to **stderr** (never stdout).
- **CSV import errors** — ensure a title column exists (`title`/`course_title`)
  for competitors, or `keyword` for SEO; run with `validate_only=true` first.
- **TLS/proxy errors** — this server respects the system proxy; never disable TLS
  verification.

---

## Repository layout

```
course-market-intelligence-mcp/
  README.md  pyproject.toml  .env.example  source_policy.yaml
  data/{cache,exports,manual_uploads}/
  examples/{claude_desktop_config.json, sample_competitors_udemy.csv}
  src/course_market_intelligence/
    server.py config.py schemas.py cache.py source_policy.py rate_limit.py compliance.py
    tools/        # 17 MCP tools
    connectors/   # compliant API + manual-import connectors
    analysis/     # scoring, keyword, trend, competitor, job, gap, revenue, curriculum, ai_angle
    outputs/      # markdown, json, csv, html report writers
  tests/          # source policy, scoring, keyword, gap, revenue, report generation
```

## Tools (17)

`research_course_topic` (full workflow) · `discover_sources` ·
`check_source_policy` · `discover_keywords` · `collect_seo_metrics` ·
`collect_trend_signals` · `collect_competitor_courses` · `analyze_competition` ·
`collect_job_market_signals` · `collect_social_signals` · `find_market_gaps` ·
`estimate_revenue_potential` · `recommend_course_positioning` ·
`design_course_blueprint` · `generate_report` · `import_manual_data` ·
`export_research_assets`.

## License

MIT. Use of third-party APIs and any manual data exports is subject to those
providers' terms — you are responsible for compliance.