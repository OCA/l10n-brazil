## 16.0.1.0.0 (2026)

- Migração para a série 16.0: o fluxo de emissão migrou de
  `l10n_br_fiscal` para `l10n_br_fiscal_edi`. O enfileiramento passa a
  envolver `_document_send` (que nenhum módulo de transmissão
  sobrescreve), mantendo o MRO limpo e independente do módulo de
  e-documento instalado.
- Adiciona suíte de testes com `queue_job` (`trap_jobs`).

## 14.0.1.0.0 (2022)

Migrate to OCA

## 12.0.1.0.0 (2021)

Migrate to OCA

## 10.0.1.0.0 (2017)

First Version
