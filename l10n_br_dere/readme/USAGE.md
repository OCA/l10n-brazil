1. Open **Fiscal → DeRE → Table Periods** and create a company-level validity
   (`iniValid` / optional `fimValid`). Monthly declarations pick the period
   that covers `perApur`.
2. Generate table events D-1001 then D-1011 from the table period. The
   monthly declaration does not create or replace those events. The stored
   XML stays unsigned and is checked
   against the official XSD. Sending signs each event (XML-DSig RSA-SHA256),
   validates the signed event and the lote, then posts one type per batch.
   **Replace Tables** updates the existing PGCC snapshot in place (for
   example a new `codTrib`) so D-1101 / D-1106 lines keep their account
   link. Accounts still used by those events cannot be dropped.
3. Sending does **not** consult immediately. Use **Consult Results** or wait
   for the cron (exponential backoff from 2 minutes up to 60) until the
   D-9001 receipt arrives. Then generate the trial balance (D-1101) from
   posted `account.move.line` records. The trial button stays hidden until
   D-1001 and D-1011 are accepted.
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
   before replacing the trial balance (`tpOper` 2 + the last D-1101 receipt).
   A second inclusion (`tpOper` 1) is rejected while that D-1101 is still
   active. Exclude (`tpOper` 3) first if the month must start over. The
   declaration stays *Reopened* through the rework until the new D-1199 is
   accepted.
   **Consult Results** only appears while a lote is still `sent`.
   The blue header button is the next official monthly step: generate the
   trial, send or consult periodics, then D-1106 / D-1121 when the company
   is subject, then close. Table generate / replace / send stay on the
   table period.
   **Generate Trial Balance** stays hidden after D-1101 is sent or accepted.
   While the month is open, **Replace Trial Balance** / **Exclude Trial
   Balance** appear instead (`tpOper` 2/3). After D-1198 is accepted the
   primary action is **Replace Trial Balance**. **Send Periodics** appears
   only while a periodic XML is `generated`.

Receipt (`nrRecibo`) and batch protocol are stored separately on each event.
Do not send a second inclusion of an active event. Replace or exclude it
(`tpOper` 2/3) while the month is open; D-1198/D-1199 stay inclusion-only.
After the first accepted D-1199, D-1121 only admits rectification (`tpOper`
4) on the reopened month. If the company is
subject to D-1106, generate that event after the trial balance (use
`semAplic` when there are no reserve assets). If it is subject to D-1121,
load inbound deductible documents or set *Declare no deductions*.

Every analytic DeRE account must have `codTrib` before D-1011 is generated.
Taxation codes show as `code - name` and can be searched by either value.
`vApur` on D-1101 follows the official movement formula (gross nature-side
amount plus adjustments). Variable-nature accounts (`natCta` V) take
`natVApur` from the period closing side. Reversal moves are reported as
`vAjusteDebt` / `vAjusteCred`. Closing D-1199 is blocked when D-1106 closing
balances do not match D-1101, or when the D-1011 receipt used to build
D-1101 changed. A fiscal document key (`chDFe`) cannot be repeated in the
same `perApur`. Table replacement may change validity only when the new
dates differ from the current period. D-1121 rectification after reopening
requires an explicit `finEvt` and the documents to rectify.

## Return events (D-9xxx)

Each consulted event keeps its own return. The **Return** tab of the event
shows the return type (D-9001, D-9101, D-9106, D-9112, D-9198 or D-9199),
the version sequence (`seqEvento`), reception and processing times, the
D-1011 receipt used by the RFB (`nrReciboPGCC`) and the return XML. The
return is checked against its official XSD: differences are posted on the
event chatter and never undo the RFB decision.

The **RFB Assessment** tab of the declaration lists the D-9101 totals per
`codTrib` / `indTribISS` and the D-9106 total next to the `vApur` sent in
D-1101 / D-1106. A warning banner and a chatter note appear when a total
differs or when D-9101, D-9106 or D-9112 used another PGCC receipt than
the D-1011 in force.

When D-1199 is accepted, the same tab shows the D-9199 assessment: the
IBS/CBS bases per specific regime (`detBC`), the general totals
(`totalTributosGeral`) and the D-1101, D-1106 and D-1121 receipts used by
the closing. The banner also appears when those receipts are not the
events in force. The amounts are recorded for reference only; no journal
entry is created. After D-1198 reopens the period, the previous assessment
stays visible and is replaced by the next D-9199. **Print RFB Assessment**
(and the Print menu) builds a landscape PDF of that tab.

D-9001 carries the RFB validity extract of the table (D-1001 or D-1011):
every validity in force and every month without coverage. The latest
extract of each table replaces the previous one and is shown on the **RFB
Validity Extract** tab of the table periods. Each validity is linked to
the local table period by its receipt. When the RFB cut a period because a
later validity starts after it (`indAjusteAuto` = 1), the period gets an
**Effective validity end** and stops covering later months. A banner
shows the cut and the gaps, and the chatter lists receipts that belong to
no local table period.

## Homologation checklist

Use a company whose chart already maps at least one administration-fee
account (`codTrib` 120110006) and one pass-through liability (also with
`codTrib`). Posted journal items in the assessment month must split **own
fee** vs **operator remittance**. The trial balance is never typed: it is
rebuilt from those moves.

1. Switch to the company and open **Fiscal → DeRE → Table Periods**.
2. Create or reuse the validity that covers the month. Confirm `iniValid`.
3. **Generate Tables**. Events D-1001 and D-1011 must exist with XML.
   - D-1001: `regTribPrinc` = 2 and `tpAtividade` = `02A` for a benefit
     administrator. No `servFinanc` / `prognosticos` unless a secondary
     regime requires them.
   - D-1011: `planoCtaRef` and `freqEncerr` present; `cDbrMista` has three
     digits; every analytic account has `codTrib`.
4. Open the monthly declaration (`perApur` = `YYYY-MM`). After the tables
   are accepted, **Generate Trial Balance**. Footer totals need the hidden
   `brl_currency_id`.
   - Fee line: credit = own revenue and `vApur` equals that gross credit
     minus credit adjustments plus debit adjustments.
   - Pass-through line: movement present and `vApur` follows the same rule
     for the account nature.
5. Open each event form and check the XML: dates use `YYYY-MM-DD`; `perApur`
   uses `YYYY-MM`. Every event `id` follows
   `DeRE` + event code + `1` + zero-padded CNPJ root + Brasília timestamp +
   sequential `QQQQQ`. Generation already rejects XML that fails the official
   XSD.
6. If the company is subject to D-1106, **Generate D-1106** before closing.
   The PGCC must include at least one account with a D-1106 `codTrib`
   (MS1135). The company flag alone does not make D-1106 official: without
   that tax code the event stays hidden and is not required before D-1121
   or D-1199 (MS1147). Register technical-reserve assets under Fiscal
   configuration, or the event is sent with `semAplic=1` when those accounts
   have no assets in the month. With exactly one asset per account the period
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
9. Repeat with **Consult Results**, or wait for the scheduled job
   **DeRE: consult sent batch results**. The POST only returns a protocol
   (`1.NNNNNN.N` or `2.NNNNNN.N`); acceptance and `nrRecibo` come from the
   later GET. Processing (`cdResposta` 1) leaves the batch sent so the cron
   retries with backoff. Lot errors (`cdResposta` 4, 5, 7 or 9) reject the
   events. A successful D-1199 return sets the declaration to *Closed*.
10. Do **not** send tables and periodics in the same batch. Do not send D-1011
    before D-1001 is accepted, nor D-1199 before D-1101 has a processing
    receipt.
11. **Reopen Period** only after D-1199 is accepted with a receipt
    `1199-YYYYMM-...`. Then send D-1198 and consult. The next D-1101 is a
    replacement (`tpOper` 2 + last active receipt), not a second inclusion.

D-3201 remains out of this checklist. D-1121 `infoImovel` and judicial
exclusions (`motExcl` 1, event D-1021) are not generated yet.
