1. Create a monthly declaration (`perApur` = `YYYY-MM`).
2. Generate table events: D-1001 then D-1011. Send them in their own batch.
3. After the D-9001 receipt, generate the trial balance (D-1101) from posted
   `account.move.line` records.
4. Close the period with D-1199 (`tpOper` inclusion only). Send periodics in a
   separate batch. Table and periodic events in the same batch are rejected.

Receipt (`nrRecibo`) and batch protocol are stored separately on each event.
D-1106 and D-1121 are only flagged on the company in this version; they are
not generated yet.

## Homologation checklist (Wave 1)

Use a company whose chart already maps at least one administration-fee account
(`codTrib` 120110006) and one pass-through liability (no `codTrib`). Posted
journal items in the assessment month must split **own fee** vs **operator
remittance**. The trial balance is never typed: it is rebuilt from those
moves.

1. Switch to the company and open **Fiscal → DeRE → Declarations**.
2. Open (or create) the month. Confirm `perApur` is `YYYY-MM` and `iniValid`
   matches the first day of the table validity.
3. **Generate Tables**. Events D-1001 and D-1011 must exist with XML.
   - D-1001: `regTribPrinc` = 2 and `tpAtividade` = `02A` for a benefit
     administrator. No `servFinanc` / `prognosticos` unless a secondary
     regime requires them.
   - D-1011: `planoCtaRef` and `freqEncerr` present; `cDbrMista` has three
     digits; fee account has `codTrib` 120110006; pass-through has no
     `codTrib`.
4. **Generate Trial Balance**. Footer totals need the hidden `brl_currency_id`.
   - Fee line: credit = own revenue and `vApur` equals that net amount.
   - Pass-through line: movement present and `vApur` = 0.00 (no `natVApur`).
5. Open each event form and check the XML: `id` is 42 characters; dates use
   `YYYY-MM-DD`; `perApur` uses `YYYY-MM`.
6. **Close Period** (D-1199). Leave *Declare no deductions* unset unless the
   company is subject to D-1121.
7. Do **not** send tables and periodics in the same batch. Do not send D-1011
   before D-1001 is accepted, nor D-1199 before D-1101 has a processing
   receipt.

D-3201, D-1106 and D-1121 are out of this checklist.
