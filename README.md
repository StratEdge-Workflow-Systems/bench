# Bench

StratEdge Workflow Systems · public reference

A floor of agents tries to move one payment. A gate decides. The receipt is the score. Change the payee and the disposition flips.

```bash
python3 -m bench
```

Requires Python 3.10+. No API key.

```bash
python3 -m bench --inject amount=50000 --inject counterparty_known=false
python3 -m unittest tests/test_gate.py
python3 -m bench --suite
```

Six dispositions: ALLOW, ALLOW WITH LIMITS, REQUIRE APPROVAL, ESCALATE, HOLD, BLOCK.

The first screen is the flip. The lines under it are the floor. This build runs the control rule locally. It does not call a model. It does not move money. It does not predict markets. It is not a customer result and it is not a live StratEdge product.

The research page, once published: https://www.stratedgeworkflow.com/research/bench

MIT License.
