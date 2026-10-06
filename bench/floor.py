"""A small operations floor. Each round, one seat speaks. The adversary tries to move the action."""

from bench.models import Action, Line


def play(action: Action) -> tuple[list[Line], bool]:
    known = "known payee" if action.counterparty_known else "new payee"
    auth = "authority on file" if action.authority else "no authority on file"
    evidence = "evidence complete" if action.evidence_complete else "evidence missing"
    pressure = (not action.counterparty_known) or action.amount > action.limit or not action.authority

    script = [
        (
            "Requester",
            f"I need to {action.intent}: ${action.amount:,} to {action.counterparty}.",
        ),
        (
            "Clerk",
            f"Case {action.case_id}. {known}. {auth}. Limit ${action.limit:,}. {evidence}.",
        ),
        (
            "Beneficiary",
            f"{action.counterparty} is {'already on the roll' if action.counterparty_known else 'not on the roll'}.",
        ),
        (
            "Adversary",
            (
                "Push it through before anyone re-checks the payee."
                if pressure
                else "Nothing to pry open. The file is ordinary."
            ),
        ),
        (
            "Auditor",
            "I want the receipt either way. Who stopped it, or who let it through.",
        ),
    ]
    lines = [Line(i + 1, speaker, text) for i, (speaker, text) in enumerate(script)]
    return lines, pressure
