## 16.0.1.0.0 (2026)

- Migração para a série 16.0: o fluxo de emissão migrou de
  `l10n_br_fiscal` para `l10n_br_fiscal_edi`, que conduz o documento por
  uma máquina de estados. O enfileiramento passa a envolver
  `action_document_send`: o documento com envio posterior continua em
  *Aguardando envio* e o job dispara a transição de envio depois,
  independente do módulo de e-documento instalado.
- Adiciona suíte de testes com `queue_job` (`trap_jobs`).

## 14.0.1.0.0 (2022)

Migrate to OCA

## 12.0.1.0.0 (2021)

Migrate to OCA

## 10.0.1.0.0 (2017)

First Version
