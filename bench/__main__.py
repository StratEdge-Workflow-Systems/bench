"""Watch the floor, then read the receipt.

  python3 -m bench
  python3 -m bench --inject amount=50000
  python3 -m bench --inject counterparty_known=false --inject amount=50000
"""

import argparse
import json

from bench.floor import play
from bench.gate import receipt
from bench.scenarios import CLEAN, NEW_PAYEE, apply_inject


BANNER = """BENCH — a rehearsal you can run. Not a live product. Not a customer result.
Local control rule. No model API. Does not move money. Does not predict markets.
StratEdge Workflow Systems"""


def why(rec) -> str:
    if rec.disposition == "ESCALATE" and rec.stopped_by == "Adversary":
        return "ESCALATE: the Adversary pushed, and Counterparty had already failed."
    if rec.stopped_by:
        return f"{rec.disposition}: stopped by {rec.stopped_by}."
    return f"{rec.disposition}: nothing failed."


def render(action, rec) -> str:
    bar = "─" * 64
    rows = [bar, f"{action.case_id}  {action.counterparty}  ${action.amount:,}", bar]
    for line in rec.lines:
        rows.append(f"  {line.round_n}. {line.speaker:<12} {line.text}")
    rows.append(bar)
    rows.append(f"  DISPOSITION   {rec.disposition}")
    rows.append(f"  STOPPED BY    {rec.stopped_by or '—'}")
    rows.append(f"  WHY           {why(rec)}")
    rows.append(f"  CHAIR         {rec.chair}  (local rule label, not a live model call)")
    rows.append("  VOTES         " + "  ".join(f"{k}={v}" for k, v in rec.votes.items()))
    rows.append(bar)
    return "\n".join(rows)


def run_one(action):
    lines, pressure = play(action)
    return receipt(action, lines, pressure)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bench — try to break the gate.")
    parser.add_argument(
        "--inject",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="Change one fact on the clean payment and rerun.",
    )
    parser.add_argument("--json", action="store_true", help="Print receipts as JSON.")
    parser.add_argument("--suite", action="store_true", help="Also run extra cases, if present.")
    args = parser.parse_args()

    if args.inject:
        inject = {}
        for item in args.inject:
            if "=" not in item:
                raise SystemExit(f"Bad inject: {item}")
            key, value = item.split("=", 1)
            inject[key] = value
        worlds = [("INJECTED", apply_inject(CLEAN, inject))]
    else:
        worlds = [("CLEAN", CLEAN), ("SAME CASE, ONE FACT CHANGED", NEW_PAYEE)]
        if args.suite:
            try:
                from bench.extra_cases import CASES
            except ImportError:
                CASES = []
            worlds.extend(CASES)

    receipts = []
    actions = []
    for title, action in worlds:
        rec = run_one(action)
        receipts.append(rec)
        actions.append((title, action))

    if args.json:
        print(json.dumps([rec.to_dict() for rec in receipts], indent=2))
        return

    print(BANNER)
    if len(receipts) >= 2 and not args.inject:
        a0, r0 = actions[0][1], receipts[0]
        a1, r1 = actions[1][1], receipts[1]
        print()
        print(f"SAME PAYMENT  ${a0.amount:,}  intent unchanged")
        print(f"  {a0.counterparty:<28} {r0.disposition}")
        print(f"  {a1.counterparty:<28} {r1.disposition}   stopped by {r1.stopped_by}")
        print(f"One fact changed: the payee. {r0.disposition} → {r1.disposition}.")
        print(why(r1))
        print()
    for (title, action), rec in zip(actions, receipts):
        print(title)
        print(render(action, rec))
        print()


if __name__ == "__main__":
    main()
