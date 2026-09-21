On the company form, open the **DeRE** tab and set:

1. Main tax regime (`regTribPrinc`) and optional secondary regime
2. Activities from official tables 21, 31 or 41
3. Referential chart (`planoCtaRef`) and closing frequency (`freqEncerr`)
4. Receita Integra environment. Restricted production uses
   `https://api.receitafederal.gov.br/prr-dere` with
   `POST /v1/recepcao/lotes` and `GET /v1/consulta/lotes/{protocol}`.
   Override the base URL and paths only when production is published.
   Token requests use HTTP Basic (`client_id` / `client_secret`) and
   `grant_type=client_credentials`. The access token is cached per company.
5. An ICP-Brasil A1 certificate on the Fiscal tab (NFe or e-CNPJ). Generation
   does not need it; sending does.
6. Leave the scheduled action **DeRE: consult sent batch results** enabled
   (every 2 minutes). It only consults batches whose backoff window is due.

7. If the taxpayer must send D-1106, enable **Subject to D-1106**, map at
   least one PGCC account to an official D-1106 `codTrib`, mark the
   investment accounts as technical-reserve and register each `idAtivo`.
   The flag only records the intention: generation, closing and the send
   order require that PGCC mapping (MS1135 / MS1147). Keep one asset per
   account so **Generate D-1106** can fill amounts from posted journal
   items. Optionally set **DeRE reserve income account** for cash coupons
   that never hit the investment account.
8. If the taxpayer must send D-1121, enable **Subject to D-1121** and mark
   inbound fiscal operations as DeRE deductible. Accounts whose `codTrib` is
   in the official D-1121 list also require the event.

On **Fiscal → DeRE → Table Periods**, create the validity that covers the
months you will declare. D-1001, D-1011 and the PGCC snapshot live there and
are reused by every monthly declaration in force. Edit the snapshot only on
the table period, and only before D-1011 is accepted. The monthly form shows
the same accounts as read-only context for D-1101.

On each **account group** used as a synthetic DeRE node, fill the **DeRE**
tab (`cCtaRef`, nature) when the official referential code differs from the
prefix. Ancestor groups of mapped analytic accounts are exported
automatically; an empty `cCtaRef` uses the prefix and the first-digit nature.
Level and parent come from the prefix hierarchy.

On each **analytic account** used in the declaration, fill the **DeRE** tab:

- internal code and 3-digit mixed-account split (`cDbrMista`)
- referential code, nature and **required** `codTrib` (empty referential
  values inherit from the prefix group). The many2one shows `code - name`.
- parent group only when the chart is not prefix-based

After remapping `codTrib` on an account that already belongs to an
accepted D-1011, use **Replace Tables** on the table period. The snapshot
row is updated and the new code goes in the next D-1011; monthly lines
that already point to that row are kept.

Do not reuse the ECD/ECF field `l10n_br_sped_referential_code` for DeRE.
