"""Unit tests for bench.gate vote() — all six dispositions."""

import unittest
from dataclasses import replace

from bench.gate import vote
from bench.models import Action, DISPOSITIONS
from bench.scenarios import CLEAN, NEW_PAYEE, apply_inject


def pressure_for(action: Action) -> bool:
    return (
        (not action.counterparty_known)
        or action.amount > action.limit
        or not action.authority
    )


class TestGateVote(unittest.TestCase):
    def assert_disposition(
        self,
        action: Action,
        expected: str,
        *,
        stopped_by: str | None = None,
        pressure: bool | None = None,
    ) -> None:
        self.assertIn(expected, DISPOSITIONS)
        p = pressure_for(action) if pressure is None else pressure
        disposition, seat, _votes, chair = vote(action, p)
        self.assertEqual(disposition, expected)
        if stopped_by is not None:
            self.assertEqual(seat, stopped_by)
        if expected in {"BLOCK", "REQUIRE APPROVAL", "HOLD", "ESCALATE"}:
            self.assertEqual(chair, "frontier-chair")
        if expected in {"ALLOW", "ALLOW WITH LIMITS"}:
            self.assertEqual(chair, "open-weight-chair")

    def test_block_no_authority_over_limit_stopped_by_identity(self) -> None:
        action = apply_inject(CLEAN, {"authority": "false", "amount": "50000"})
        self.assert_disposition(action, "BLOCK", stopped_by="Identity")

    def test_require_approval_no_authority_within_limit(self) -> None:
        action = apply_inject(CLEAN, {"authority": "false"})
        self.assert_disposition(action, "REQUIRE APPROVAL", stopped_by="Identity")

    def test_block_unknown_counterparty_at_threshold(self) -> None:
        action = apply_inject(
            CLEAN,
            {"counterparty_known": "false", "amount": "10000"},
        )
        self.assert_disposition(action, "BLOCK", stopped_by="Counterparty")

    def test_hold_amount_over_limit_with_authority(self) -> None:
        action = apply_inject(CLEAN, {"amount": "50000"})
        self.assert_disposition(action, "HOLD", stopped_by="Limit")

    def test_hold_evidence_incomplete(self) -> None:
        action = apply_inject(CLEAN, {"evidence_complete": "false"})
        self.assert_disposition(action, "HOLD", stopped_by="Evidence")

    def test_escalate_pressure_unknown_counterparty_under_block_threshold(self) -> None:
        self.assertEqual(NEW_PAYEE.amount, 4_200)
        self.assertFalse(NEW_PAYEE.counterparty_known)
        self.assert_disposition(NEW_PAYEE, "ESCALATE", stopped_by="Adversary")

    def test_allow_with_limits_above_eighty_percent_of_limit(self) -> None:
        action = apply_inject(CLEAN, {"amount": "21000"})
        self.assertGreater(action.amount, int(action.limit * 0.8))
        self.assertLessEqual(action.amount, action.limit)
        self.assert_disposition(action, "ALLOW WITH LIMITS", stopped_by="Limit")

    def test_allow_clean_payment(self) -> None:
        self.assert_disposition(CLEAN, "ALLOW", stopped_by=None, pressure=False)

    def test_escalate_requires_pressure_true(self) -> None:
        """Unknown payee with pressure=False cannot reach ESCALATE (open-weight path)."""
        action = replace(NEW_PAYEE)
        disposition, _, _, _ = vote(action, pressure=False)
        self.assertNotEqual(disposition, "ESCALATE")


if __name__ == "__main__":
    unittest.main()
