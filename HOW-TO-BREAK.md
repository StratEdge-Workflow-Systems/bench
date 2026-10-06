# Bench — How to Break the Gate

Public reference from StratEdge Workflow Systems. A small **floor** (Requester, Clerk, Beneficiary, Adversary, Auditor) narrates one payment attempt. The **gate** returns a disposition and a receipt: who stopped it (if anyone), seat votes, and which **chair** spoke.

**Dispositions:** `ALLOW` · `ALLOW WITH LIMITS` · `REQUIRE APPROVAL` · `ESCALATE` · `HOLD` · `BLOCK`

**Baseline case (clean):** `PAY-100`, $4,200 to Northline Custodial, known payee, authority on file, limit $25,000, evidence complete.

**v0 facts:** Runs the published **control rule** in `bench/gate.py` locally. It does **not** call a model API. It does **not** move money. It does **not** predict markets. Output is **not** a customer result. **`open-weight-chair`** is used only on a clean or near-limit allow (`ALLOW`, `ALLOW WITH LIMITS`). **`frontier-chair`** is used when the floor is not clean (all other dispositions in this build).

Run all commands from the **`bench`** directory (the folder that contains the `bench` Python package).

---

## Commands

- **`python3 -m bench`**  
  Runs two worlds on the same intent: **CLEAN** (Northline Custodial, known payee) then **SAME CASE, ONE FACT CHANGED** (Harbor Relay LLC, new payee).  
  - CLEAN → **ALLOW**, stopped by —, **open-weight-chair**, Adversary **QUIET**.  
  - Changed payee → **ESCALATE**, stopped by **Adversary**, **frontier-chair**, Counterparty **FAIL**, Adversary **PRESSURE**.  
  Prints a flip line when dispositions differ.

- **`python3 -m bench --inject counterparty_known=false`**  
  Single run: clean facts except **new payee** on Northline Custodial.  
  → **ESCALATE**, **Adversary**, **frontier-chair** (same votes as the “one fact changed” case above).

- **`python3 -m bench --inject amount=50000`**  
  Known payee, amount above $25,000 limit.  
  → **HOLD**, stopped by **Limit**, **frontier-chair**, Limit **FAIL**, Adversary **PRESSURE**.

- **`python3 -m bench --inject amount=50000 --inject counterparty_known=false`**  
  New payee and $50,000 (≥ $10,000 triggers counterparty block before limit hold).  
  → **BLOCK**, stopped by **Counterparty**, **frontier-chair**.

- **`python3 -m bench --inject authority=false`**  
  No authority on file; amount still within limit.  
  → **REQUIRE APPROVAL**, stopped by **Identity**, **frontier-chair**, Identity **FAIL**, Adversary **PRESSURE**.

- **`python3 -m bench --inject evidence_complete=false`**  
  Evidence missing; otherwise clean.  
  → **HOLD**, stopped by **Evidence**, **frontier-chair**, Evidence **FAIL**, Adversary **QUIET**.

- **`python3 -m bench --inject amount=21000`**  
  Known payee, within limit, above 80% of limit ($20,000).  
  → **ALLOW WITH LIMITS**, stopped by **Limit**, **open-weight-chair**, all seat votes **PASS**, Adversary **QUIET**.

---

## What you are testing

- Change **one fact** (`--inject FIELD=VALUE`) on the clean payment and read whether the gate **flips** disposition or **stopped_by** seat.  
- Compare **chair** label: open-weight only on allow paths; frontier when identity, counterparty, limit, evidence, or adversary pressure stops a clean allow.  
- Optional: `--json` for machine-readable receipts; `--suite` for extra cases if `bench/extra_cases.py` exists.
