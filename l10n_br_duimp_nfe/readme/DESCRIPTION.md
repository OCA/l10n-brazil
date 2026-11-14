Glue module between `l10n_br_duimp` and `l10n_br_nfe`.

When an inbound fiscal document line is linked to a DUIMP item, this
module automatically fills the NF-e import-declaration group
(`DI`/`adi`, tags `nfe40_DI`/`nfe40_adi`) required when re-issuing an
inbound NF-e (nota fiscal de entrada) for imported goods. The NF-e `DI`
group covers "DI, DSI, DIRE and DUImp"; for a DUIMP the number goes into
`nfe40_nDI` and each item becomes an `adi` sequence.

It is kept separate from the core `l10n_br_duimp` so companies that do
not re-issue their own inbound NF-e are not forced to depend on
`l10n_br_nfe`.
