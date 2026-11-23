# RTC tables sync

Generates the `l10n_br_fiscal_rtc` data files from the official Receita Federal
Calculadora de Tributos (regime regular).

## Why

The official repository is a Spring Boot API whose rules live in a SQLite database built
by 60 Flyway migrations. The rules are not in the Java code: each tax treatment stores
its formulas as expressions (`TRTR_EXPRESSAO_*`). Copying them by hand guarantees drift;
replaying the migrations guarantees the data is exactly the published one.

## Usage

The output directory and the cClassTrib CSV of `l10n_br_fiscal` default to the sibling
modules, so only the source clone is required:

```bash
python3 l10n_br_fiscal_rtc/tools/sync_rtc_tables.py \
    --src /path/to/calculadora-rtc-regime-regular
```

Then review the diff: `git diff l10n_br_fiscal_rtc/data`.

In CI, check that the committed data matches the source:

```bash
python3 l10n_br_fiscal_rtc/tools/sync_rtc_tables.py --src ... --check
```

`--check` exits 1 and lists the stale files.

## What is generated

| file                                        | content                                                             |
| ------------------------------------------- | ------------------------------------------------------------------- |
| `l10n_br_fiscal.rtc.treatment.csv`          | 43 tax treatments with their expressions                            |
| `l10n_br_fiscal.rtc.legal.basis.csv`        | legal basis (LC 214/2025 and annexes)                               |
| `l10n_br_fiscal.rtc.rate.csv`               | official reference rates per period (2026: CBS 0.9%, IBS 0.1% / 0%) |
| `l10n_br_fiscal.tax.classification.csv`     | enrichment of the existing cClassTrib records (`rtc_*` fields only) |
| `l10n_br_fiscal.tax.classification.rtc.xml` | cClassTrib codes missing from `l10n_br_fiscal`                      |
| `l10n_br_fiscal.rtc.nomenclature.csv`       | NCM/NBS accepted per cClassTrib (annexes)                           |
| `SYNC_REPORT.md`                            | source version, counts, and the cClassTrib drift                    |

## Rules the script implements

- **One row per cClassTrib.** The official table has two current rows for 14 codes: one
  for CBS/IBS, one for the Imposto Seletivo. Only the first is exported, selected
  through `TRIBUTO_SITUACAO_TRIBUTARIA`.
- **Enrich, never overwrite.** A cClassTrib already shipped by `l10n_br_fiscal` is
  updated only on the `rtc_*` fields: its name, rate type, dates and
  `tax_ibs_id`/`tax_cbs_id` are left untouched.
- **Duplicates dropped.** The official annexes contain exact duplicate rows; they are
  collapsed on the generated id.
- **No invented rate.** Only `ALIQUOTA_REFERENCIA` is exported. There is no 2027+ value
  in the official base yet (the Senate has not set the CBS rate), so the engine fails
  loudly instead of using a made-up rate.

## Notes

The official data has no rate for 2027+: from 2027 the nominal rates are an input of the
operation (`aliquotasNominais` in the official API), which is why
`l10n_br_fiscal.rtc.rate` is a per-year table to be filled when the Senate and the CGIBS
publish the values.
