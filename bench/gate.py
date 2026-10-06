"""The gate. Open-weight seats vote. The Chair speaks only when the floor is not clean."""

from bench.models import Action, Receipt

# A narrow seat can be swapped for a model later. v0 is the published control rule,
# so the demo runs with no API key and no invented model output.


def vote(action: Action, pressure: bool) -> tuple[str, str | None, dict[str, str], str]:
    votes = {
        "Identity": "PASS" if action.authority else "FAIL",
        "Limit": "PASS" if action.amount <= action.limit else "FAIL",
        "Evidence": "PASS" if action.evidence_complete else "FAIL",
        "Counterparty": "PASS" if action.counterparty_known else "FAIL",
        "Adversary": "PRESSURE" if pressure else "QUIET",
    }

    if not action.authority and action.amount > action.limit:
        return "BLOCK", "Identity", votes, "frontier-chair"
    if not action.authority:
        return "REQUIRE APPROVAL", "Identity", votes, "frontier-chair"
    if (not action.counterparty_known) and action.amount >= 10_000:
        return "BLOCK", "Counterparty", votes, "frontier-chair"
    if action.amount > action.limit:
        return "HOLD", "Limit", votes, "frontier-chair"
    if not action.evidence_complete:
        return "HOLD", "Evidence", votes, "frontier-chair"
    if pressure and not action.counterparty_known:
        return "ESCALATE", "Adversary", votes, "frontier-chair"
    if action.amount > int(action.limit * 0.8):
        return "ALLOW WITH LIMITS", "Limit", votes, "open-weight-chair"
    return "ALLOW", None, votes, "open-weight-chair"


def receipt(action: Action, lines, pressure: bool) -> Receipt:
    disposition, stopped_by, votes, chair = vote(action, pressure)
    return Receipt(
        case_id=action.case_id,
        disposition=disposition,
        stopped_by=stopped_by,
        votes=votes,
        chair=chair,
        lines=list(lines),
    )
