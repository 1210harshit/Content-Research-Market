"""Tool: check_source_policy."""

from __future__ import annotations

from ..compliance import ComplianceAuditor, evaluate_gate


async def check_source_policy(url_or_domain: str, intended_collection_mode: str) -> dict:
    """Check whether a source can be collected from with a given mode.

    Performs the full compliance evaluation including a robots.txt check for
    public-metadata modes.
    """
    auditor = ComplianceAuditor()
    decision = await evaluate_gate(
        url_or_domain, intended_collection_mode, auditor=auditor,
        check_robots_for_public=True,
    )
    from ..source_policy import evaluate

    policy = evaluate(url_or_domain, intended_collection_mode)
    return {
        "domain": decision.domain,
        "allowed": decision.allowed,
        "allowed_modes": policy.allowed_modes,
        "blocked_modes": policy.blocked_modes,
        "robots_txt_status": decision.robots_txt_status,
        "terms_status": decision.terms_status,
        "reason": decision.reason,
        "safe_next_step": policy.safe_next_step or (
            f"Proceed using '{intended_collection_mode}'." if decision.allowed
            else "Choose an allowed mode or use a manual CSV export."
        ),
    }
