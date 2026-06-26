"""Compliance gate.

Central place that connectors call before doing anything. It refuses disallowed
modes, performs a robots.txt check for public metadata fetches, and provides a
small audit record so every source decision is traceable in the final report.
"""

from __future__ import annotations

import urllib.robotparser
from dataclasses import dataclass, field
from urllib.parse import urlparse

from .rate_limit import guarded_get
from .source_policy import evaluate

USER_AGENT = "course-market-intelligence-mcp (+compliance-first; respects robots.txt)"

# Things this MCP must never attempt. Documented here so the prohibition is in code.
PROHIBITED_BEHAVIORS = (
    "bypassing logins, paywalls, CAPTCHAs or anti-bot protections",
    "proxy rotation or stealth fingerprinting for evasion",
    "stealing cookies/sessions or automating logins for scraping",
    "scraping private, paid, or restricted content",
    "copying course videos, transcripts, assignments, quizzes, certificates or paid assets",
    "collecting personal data about learners or instructors",
    "violating robots.txt or platform restrictions",
)


@dataclass
class AuditEntry:
    domain: str
    mode: str
    decision: str  # allowed | skipped
    reason: str
    robots_txt_status: str = "not_checked"
    terms_status: str = "unknown"


@dataclass
class ComplianceAuditor:
    """Accumulates source decisions over a research run for the source audit."""

    entries: list[AuditEntry] = field(default_factory=list)

    def record(self, entry: AuditEntry) -> None:
        self.entries.append(entry)

    def used(self) -> list[dict]:
        return [e.__dict__ for e in self.entries if e.decision == "allowed"]

    def skipped(self) -> list[dict]:
        return [e.__dict__ for e in self.entries if e.decision == "skipped"]

    def as_rows(self) -> list[dict]:
        return [e.__dict__ for e in self.entries]


async def check_robots(url: str, path: str = "/") -> str:
    """Return 'allowed' | 'disallowed' | 'unknown' for our user agent."""
    parsed = urlparse(url if "://" in url else "https://" + url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = await guarded_get(robots_url, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200 or not resp.text.strip():
            return "unknown"
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(resp.text.splitlines())
        target = path if path.startswith("/") else "/" + path
        return "allowed" if rp.can_fetch(USER_AGENT, target) else "disallowed"
    except Exception:
        return "unknown"


class SourcePolicyDecision:
    def __init__(self, allowed: bool, reason: str, robots_txt_status: str,
                 terms_status: str, domain: str, mode: str):
        self.allowed = allowed
        self.reason = reason
        self.robots_txt_status = robots_txt_status
        self.terms_status = terms_status
        self.domain = domain
        self.mode = mode


async def evaluate_gate(
    url_or_domain: str,
    mode: str,
    *,
    auditor: ComplianceAuditor | None = None,
    check_robots_for_public: bool = True,
) -> SourcePolicyDecision:
    """Full compliance decision for a (domain, mode), with robots check for public modes."""
    policy = evaluate(url_or_domain, mode)
    robots_status = "not_checked"
    public_modes = {"public_metadata", "public_metadata_if_allowed"}

    if policy.allowed and mode in public_modes and check_robots_for_public:
        robots_status = await check_robots(url_or_domain)
        if robots_status == "disallowed":
            policy.allowed = False
            policy.reason = (
                f"{policy.reason} robots.txt disallows automated fetching of this path."
            )

    decision = SourcePolicyDecision(
        allowed=policy.allowed,
        reason=policy.reason,
        robots_txt_status=robots_status if mode in public_modes else "not_applicable",
        terms_status=policy.terms_status,
        domain=policy.domain,
        mode=mode,
    )

    if auditor is not None:
        auditor.record(
            AuditEntry(
                domain=policy.domain,
                mode=mode,
                decision="allowed" if decision.allowed else "skipped",
                reason=policy.reason,
                robots_txt_status=decision.robots_txt_status,
                terms_status=policy.terms_status,
            )
        )
    return decision
