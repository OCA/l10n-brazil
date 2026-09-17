On the company form, open the **DeRE** tab and set:

1. Main tax regime (`regTribPrinc`) and optional secondary regime
2. Activities from official tables 21, 31 or 41
3. Referential chart (`planoCtaRef`) and closing frequency (`freqEncerr`)
4. Receita Integra environment, token URL, OAuth client credentials and the
   batch consult path (`{protocol}` placeholder)
5. An ICP-Brasil A1 certificate on the Fiscal tab (NFe or e-CNPJ). Generation
   does not need it; sending does.
6. Leave the scheduled action **DeRE: consult sent batch results** enabled
   (every 2 minutes). The form button still consults immediately.

7. If the taxpayer must send D-1106, enable **Subject to D-1106**, mark the
   investment accounts as technical-reserve and register each `idAtivo`.
8. If the taxpayer must send D-1121, enable **Subject to D-1121** and mark
   inbound fiscal operations as DeRE deductible.

On each account used in the declaration, fill the **DeRE** tab:

- internal code and 3-digit mixed-account split (`cDbrMista`)
- parent account, referential code, nature and optional `codTrib`

Do not reuse the ECD/ECF field `l10n_br_sped_referential_code` for DeRE.
