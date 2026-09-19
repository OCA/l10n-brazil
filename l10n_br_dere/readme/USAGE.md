1. Create a monthly declaration (`perApur` = `YYYY-MM`).
2. Generate table events: D-1001 then D-1011. The stored XML stays unsigned
   and is checked against the official XSD (a placeholder `ds:Signature` is
   attached only for that check). Sending signs each event (XML-DSig
   RSA-SHA256), validates the signed event and the lote, then posts one type
   per batch.
3. Sending already consults the batch once. While the return says the batch is
   still processing, use **Consult Results** or wait for the two-minute cron
   until the D-9001 receipt arrives.
   Then generate the trial balance (D-1101) from posted `account.move.line`
   records.
4. Generate D-1199 with **Close Period** (`tpOper` inclusion only). That only
   stores the XML; the declaration stays in *Trial balance ready*. Use
   **Discard Local Closing** to drop a D-1199 that was never sent. Send
   periodics in a separate batch. Table and periodic events in the same batch
   are rejected. The declaration becomes *Closed* when the D-1199 return is
   accepted.
5. To reopen an officially closed period, wait for the D-1199 receipt, then
   **Reopen Period**. That builds D-1198 (`nrReciboReab`) and keeps the
   declaration *Closed*; use **Discard Local Reopening** to drop a D-1198 that
   was never sent. **Send Periodics** and consult until D-1198 is accepted
   before generating a new trial balance. The declaration stays *Reopened*
   through the rework until the new D-1199 is accepted.
   A closed declaration does not offer send or consult; **Consult Results**
   only appears while a lote is still `sent`.    **Generate Tables** and
   **Send Tables** disappear after D-1001 and D-1011 are sent or accepted.
   The blue header button is the next official step: generate, send or
   consult, then D-1106 / D-1121 when the company is subject, then close.
   **Generate Trial Balance** stays hidden after D-1101 is sent or accepted
   until D-1198 is accepted. **Send Periodics** appears only while a
   periodic XML is `generated`.

Receipt (`nrRecibo`) and batch protocol are stored separately on each event.
Do not regenerate an event that is already sent or accepted unless D-1198
was accepted. Wave 1 only supports inclusion (`tpOper` 1). If the company is
subject to D-1106, generate that event after the trial balance (use
`semAplic` when there are no reserve assets). If it is subject to D-1121,
load inbound deductible documents or set *Declare no deductions*.

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
5. Open each event form and check the XML: dates use `YYYY-MM-DD`; `perApur`
   uses `YYYY-MM`. Table `id` is 42 alphanumeric characters and starts with a
   letter (lote `xs:ID`). D-1101 / D-1106 / D-1121 / D-1198 / D-1199 `id`
   follows `DeRE` + event code + environment + CNPJ + 19 digits. Generation
   already rejects XML that fails the official XSD.
6. If the company is subject to D-1106, **Generate D-1106** before closing.
   Register technical-reserve assets under Fiscal configuration, or the event
   is sent with `semAplic=1`. With exactly one asset per account the period
   amounts come from posted moves: debits become `vVarMensal`, credits become
   `vPrincLiqResg`, and income on the same entry (or on the mapped reserve
   income account) fills `vRendPerReceb` / `vRendLiqResg`. Several assets on
   the same account stay manual. Regenerating rebuilds those 1:1 amounts.
   If it is subject to D-1121, **Load Deductions**
   from inbound operations marked as DeRE deductible, then **Generate D-1121**.
   When the period has no deductible document the load reports the absence and
   sets `indInexistDedu`. **Close Period** stays hidden until the load ran, so
   the month is never closed as deduction-free by accident.
7. **Close Period** generates D-1199 but does not lock the month. Send
   periodics one type at a time: D-1101, then D-1106 (if any), then D-1121
   (if any), then D-1199. Each auxiliary event needs the previous processing
   receipt. If the XML is wrong and still `generated`, **Discard Local
   Closing** and generate again.
8. Confirm the company has an A1 certificate. Sending signs the payload;
   the event form still shows the unsigned XML.
9. Each send consults the batch once. Repeat with **Consult Results**, or wait
   for the scheduled job
   **DeRE: consult sent batch results**. The POST only returns a protocol;
   acceptance and `nrRecibo` come from the later GET. Processing
   (`cdResposta` 1) leaves the batch sent so the cron retries. A successful
   D-1199 return sets the declaration to *Closed*.
10. Do **not** send tables and periodics in the same batch. Do not send D-1011
    before D-1001 is accepted, nor D-1199 before D-1101 has a processing
    receipt.
11. **Reopen Period** only after D-1199 is accepted with a receipt
    `1199-YYYYMM-...`. Then send D-1198 and consult before a new D-1101.

D-3201 remains out of this checklist. `tpOper` 2/3/4 and real-estate
deductions (`infoImovel`) are not generated yet.
