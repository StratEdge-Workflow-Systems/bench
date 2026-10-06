from bench.models import Action

CLEAN = Action(
    case_id="PAY-100",
    kind="payment",
    requester="treasury-bot",
    authority=True,
    counterparty="Northline Custodial",
    counterparty_known=True,
    amount=4_200,
    limit=25_000,
    evidence_complete=True,
    intent="pay an approved vendor invoice",
)

NEW_PAYEE = Action(
    case_id="PAY-100",
    kind="payment",
    requester="treasury-bot",
    authority=True,
    counterparty="Harbor Relay LLC",
    counterparty_known=False,
    amount=4_200,
    limit=25_000,
    evidence_complete=True,
    intent="pay an approved vendor invoice",
)


def apply_inject(action: Action, inject: dict[str, str]) -> Action:
    data = action.__dict__.copy()
    for key, raw in inject.items():
        if key not in data:
            raise SystemExit(f"Unknown inject field: {key}")
        current = data[key]
        if isinstance(current, bool):
            data[key] = raw.lower() in {"1", "true", "yes", "y"}
        elif isinstance(current, int):
            data[key] = int(raw.replace(",", "").replace("$", ""))
        else:
            data[key] = raw
    return Action(**data)
