# RTC tables sync report

- source: `calculadora-rtc-regime-regular`
- database version: `V0059` (2026-09-30)
- flyway scripts applied: 60
- treatments: 43
- legal basis: 193
- rates: 3
- classifications (current): 161 (161 enrich, 0 create)
- nomenclature rows: ncm=1135, nbs=109
- Simples Nacional: activities=15, regimes=3, revenue types=7, transition factors=6

## cClassTrib already in l10n_br_fiscal

- in l10n_br_fiscal and still official: 161
- in l10n_br_fiscal, absent from the official base (12): `000006`, `200055`, `200056`, `220001`, `220002`, `220003`, `400003`, `400004`, `550026`, `550027`, `550028`, `550029`
- official, not in l10n_br_fiscal yet (0): none
