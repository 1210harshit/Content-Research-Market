"""Optional HTML report — a light wrapper that renders the markdown body."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment

_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ topic }} — Market Validation</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 920px;
         margin: 2rem auto; padding: 0 1rem; line-height: 1.5; color: #1b1f24; }
  h1 { border-bottom: 3px solid #2d6cdf; padding-bottom: .3rem; }
  .verdict { display: inline-block; padding: .3rem .8rem; border-radius: 6px;
             font-weight: 700; color: #fff; }
  .strong_go { background:#1a7f37 } .conditional_go { background:#bf8700 }
  .hold_research_more { background:#9a6700 } .no_go { background:#cf222e }
  table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
  th, td { border: 1px solid #d0d7de; padding: .5rem; text-align: left; }
  th { background:#f6f8fa; }
  .scorecard { display:flex; gap:1rem; flex-wrap:wrap; }
  .score { background:#f6f8fa; border-radius:8px; padding:1rem; text-align:center; min-width:120px; }
  .score b { font-size:1.6rem; display:block; color:#2d6cdf; }
  pre { background:#f6f8fa; padding:.2rem .4rem; border-radius:4px; }
</style>
</head>
<body>
<h1>{{ topic }}</h1>
<p><strong>{{ recommended_title }}</strong> &middot; Generated {{ generated_at }}</p>
<p>Verdict: <span class="verdict {{ go_no_go }}">{{ go_no_go | upper }}</span>
   &middot; Confidence: {{ confidence }}</p>

<div class="scorecard">
  <div class="score"><b>{{ scores.demand }}</b>Demand</div>
  <div class="score"><b>{{ scores.competition_risk }}</b>Competition risk</div>
  <div class="score"><b>{{ scores.gap }}</b>Gap</div>
  <div class="score"><b>{{ scores.revenue }}</b>Revenue</div>
  <div class="score"><b>{{ scores.overall }}</b>Overall</div>
</div>

<h2>Executive summary</h2>
<p>{{ summary }}</p>

<h2>Revenue scenarios</h2>
<table>
<tr><th>Scenario</th><th>Enrollments</th><th>Realized price</th><th>B2B deals</th><th>Annual revenue</th></tr>
{% for name, s in revenue.scenarios.items() %}
<tr><td>{{ name }}</td><td>{{ s.enrollments }}</td><td>${{ s.realized_price }}</td><td>{{ s.b2b_deals }}</td><td>${{ "%.0f"|format(s.annual_revenue) }}</td></tr>
{% endfor %}
</table>

<h2>Top gaps</h2>
<ul>
{% for g in gaps[:8] %}<li><strong>[{{ g.priority }}]</strong> {{ g.gap }} — {{ g.why_it_matters }}</li>{% endfor %}
</ul>

<h2>Recommendation</h2>
<p>{{ recommendation_narrative }}</p>

<p style="color:#57606a;font-size:.85rem">Revenue figures are modelled estimates,
not verified competitor revenue. Sources used: {{ sources_used | length }};
skipped (per compliance): {{ sources_skipped | length }}.</p>
</body>
</html>
"""


def write_html(report: dict, out_dir: Path, slug: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)
    template = env.from_string(_HTML)
    path = out_dir / f"{slug}_report.html"
    path.write_text(template.render(**report), encoding="utf-8")
    return str(path)
