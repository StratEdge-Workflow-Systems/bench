from bench.models import Action

CASES: list[tuple[str, Action]] = [
    (
        "Delegated signer, within limit (expect REQUIRE APPROVAL)",
        Action(
            case_id="PAY-201",
            kind="payment",
            requester="treasury-bot",
            authority=False,
            counterparty="Meridian Office Supply Co.",
            counterparty_known=True,
            amount=4_200,
            limit=25_000,
            evidence_complete=True,
            intent="pay an approved vendor invoice",
        ),
    ),
    (
        "Known payee, invoice packet incomplete (expect HOLD)",
        Action(
            case_id="PAY-202",
            kind="payment",
            requester="treasury-bot",
            authority=True,
            counterparty="Cascade Data Hosting Inc.",
            counterparty_known=True,
            amount=4_200,
            limit=25_000,
            evidence_complete=False,
            intent="pay an approved vendor invoice",
        ),
    ),
    (
        "Known payee at 84% of limit (expect ALLOW WITH LIMITS)",
        Action(
            case_id="PAY-203",
            kind="payment",
            requester="treasury-bot",
            authority=True,
            counterparty="Redwood Analytics Partners",
            counterparty_known=True,
            amount=21_000,
            limit=25_000,
            evidence_complete=True,
            intent="pay an approved vendor invoice",
        ),
    ),
    (
        "First-time payee, large wire (expect BLOCK)",
        Action(
            case_id="PAY-204",
            kind="payment",
            requester="treasury-bot",
            authority=True,
            counterparty="Vantage Relay Holdings",
            counterparty_known=False,
            amount=50_000,
            limit=25_000,
            evidence_complete=True,
            intent="pay an approved vendor invoice",
        ),
    ),
]
