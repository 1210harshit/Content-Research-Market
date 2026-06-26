"""Markdown market-validation report generator (Jinja2)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment

_TEMPLATE = """# Course Market Validation Report

**Topic:** {{ topic }}
**Recommended title:** {{ recommended_title }}
**Generated:** {{ generated_at }}
**Depth:** {{ depth }} | **Regions:** {{ regions | join(', ') }}

> Compliance note: This report uses only compliant sources (official/affiliate
> APIs, search APIs, approved SEO/trend data, manual uploads, and public metadata
> after robots.txt + ToS checks). Data is labelled exact / estimated / unavailable.

---

## Section 1 — Summary Table

| Field | Value |
|---|---|
| Proposed title | {{ recommended_title }} |
| Target learner | {{ target_learner }} |
| Demand | {{ scores.demand }}/100 |
| Competition (risk) | {{ scores.competition_risk }}/100 |
| Market gap | {{ scores.gap }}/100 |
| AI angle | {{ ai_angle_strength }} |
| Revenue potential | {{ scores.revenue }}/100 |
| Overall | {{ scores.overall }}/100 |
| Key differentiation | {{ differentiation }} |
| **Go / No-Go** | **{{ go_no_go }}** |
| Confidence | {{ confidence }} |

---

## Section 2 — Detailed Narrative

### 1. Executive summary
{{ summary }}

**Top opportunities**
{% for o in top_opportunities %}- {{ o }}
{% endfor %}
**Top risks**
{% for r in top_risks %}- {{ r }}
{% endfor %}

### 2. Course positioning
- **Primary title:** {{ positioning.primary_recommended_title }}
- **Value proposition:** {{ positioning.value_proposition }}
- **Differentiation:** {{ positioning.differentiation_strategy }}
- **B2C:** {{ positioning.b2c_positioning }}
- **B2B:** {{ positioning.b2b_positioning }}

Title options:
{% for t in positioning.title_options %}- {{ t }}
{% endfor %}

### 3. Demand and search behavior
Demand score **{{ scores.demand }}/100**. Drivers:
{% for r in scores_rationale.demand %}- {{ r }}
{% endfor %}
Top keywords ({{ keywords | length }} generated):
{% for k in keywords[:15] %}- `{{ k.keyword }}` — intent: {{ k.intent }}, volume: {{ k.volume_bucket }}, use: {{ k.recommended_use }}
{% endfor %}

### 4. Trend and seasonality analysis
- **Direction:** {{ trends.trend_direction }} (confidence: {{ trends.confidence }})
- **Growth estimate:** {{ trends.growth_rate_estimate }}
- **Best launch window:** {{ trends.best_launch_window or 'unknown' }}
{% if trends.emerging_related_terms %}- **Emerging terms:** {{ trends.emerging_related_terms | join(', ') }}{% endif %}

### 5. Competitor analysis
- **Competition level:** {{ competition.competition_level }}
- **Avg rating:** {{ competition.average_rating }} | **Avg reviews:** {{ competition.average_review_count }} | **Avg duration (h):** {{ competition.average_duration_hours }}
- **Common price bands:** {{ competition.common_price_bands | join('; ') }}

Closest competitors:
{% for c in competition.closest_competitors %}- {{ c.title }} ({{ c.platform }}) — rating {{ c.rating }}, reviews {{ c.review_count }}
{% endfor %}

Competitor weaknesses (your openings):
{% for w in competition.competitor_weaknesses %}- {{ w }}
{% endfor %}

### 6. Market gap analysis
Gap score **{{ scores.gap }}/100**. Highest-value gaps:
{% for g in gaps[:8] %}- **[{{ g.priority }}] {{ g.gap }}** ({{ g.gap_type }}) — {{ g.why_it_matters }}
{% endfor %}

### 7. Job-market relevance
- **Demand bucket:** {{ jobs.estimated_job_posting_demand_bucket }}
- **Related roles:** {{ jobs.related_job_titles | join(', ') if jobs.related_job_titles else 'n/a' }}
- **Top skills:** {{ jobs.skill_frequency.keys() | list | join(', ') if jobs.skill_frequency else 'n/a' }}
- **CV positioning:** {{ jobs.recommended_cv_positioning }}

### 8. AI angle
- **Strength:** {{ ai_angle_strength }}
- {{ ai_angle.rationale }}
{% for m in ai_angle.recommended_modules %}- {{ m }}
{% endfor %}

### 9. Pricing and revenue scenarios
- **Recommended Udemy list price:** ${{ revenue.recommended_udemy_list_price }}
- **Expected realized price:** ${{ revenue.expected_realized_udemy_price }}
- **B2B licensing band:** {{ revenue.recommended_b2b_licensing_band }}

| Scenario | Enrollments | Realized price | B2B deals | Annual revenue |
|---|---|---|---|---|
{% for name, s in revenue.scenarios.items() %}| {{ name }} | {{ s.enrollments }} | ${{ s.realized_price }} | {{ s.b2b_deals }} | ${{ "%.0f"|format(s.annual_revenue) }} |
{% endfor %}

_Revenue figures are explicitly modelled estimates, not verified competitor revenue._

### 10. Recommended course blueprint
- **Duration:** {{ blueprint.recommended_total_duration_hours }}h across {{ blueprint.recommended_number_of_modules }} modules

{% for m in blueprint.modules %}**{{ loop.index }}. {{ m.title }}** — {{ m.objective }}
{% for l in m.lessons %}  - {{ l.title }}
{% endfor %}{% endfor %}

Capstone: {{ blueprint.capstone_projects | join('; ') }}
Learning outcomes:
{% for o in blueprint.learning_outcomes %}- {{ o }}
{% endfor %}

### 11. SEO and marketplace optimization
Ad / landing keywords: {{ positioning.ad_landing_keywords | join(', ') }}

### 12. Risks and limitations
{% for l in limitations %}- {{ l }}
{% endfor %}

### 13. Final recommendation
**{{ go_no_go }}** (overall {{ scores.overall }}/100, confidence {{ confidence }}).

{{ recommendation_narrative }}

### 14. Next actions
{% for a in next_actions %}- {{ a }}
{% endfor %}

---

## Source audit
Sources used: {{ sources_used | length }} | Sources skipped: {{ sources_skipped | length }}

{% for s in source_audit %}- [{{ s.decision }}] {{ s.domain }} via {{ s.mode }} — {{ s.reason }}
{% endfor %}
"""


def write_markdown(report: dict, out_dir: Path, slug: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
    template = env.from_string(_TEMPLATE)
    rendered = template.render(**report)
    path = out_dir / f"{slug}_report.md"
    path.write_text(rendered, encoding="utf-8")
    return str(path)
