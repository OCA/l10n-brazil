<!-- GERADO por docs/scripts/gerar_index.py a partir de docs/; nao editar a mao -->

# Índice das especificações

Gerado a partir de `docs/`. Para atualizar: `python docs/scripts/gerar_index.py`.

## Módulos

| Módulo | Specs | Capacidades |
| --- | --- | --- |
| `l10n_br_base` | [SPEC-CAD-cnpj-alfanumerico](specs/CAD/SPEC-CAD-cnpj-alfanumerico.md) (planejado) | [CAP-CAD-identificacao-cnpj](capacidades/CAD/CAP-CAD-identificacao-cnpj.md) (planejado) |
| `l10n_br_cnpj_search` |  | [CAP-CAD-identificacao-cnpj](capacidades/CAD/CAP-CAD-identificacao-cnpj.md) (planejado) |
| `l10n_br_fiscal` | [SPEC-CAD-cnpj-alfanumerico](specs/CAD/SPEC-CAD-cnpj-alfanumerico.md) (planejado) | [CAP-CAD-identificacao-cnpj](capacidades/CAD/CAP-CAD-identificacao-cnpj.md) (planejado) |
| `l10n_br_fiscal_dfe` | [SPEC-CAD-cnpj-alfanumerico](specs/CAD/SPEC-CAD-cnpj-alfanumerico.md) (planejado) | [CAP-CAD-identificacao-cnpj](capacidades/CAD/CAP-CAD-identificacao-cnpj.md) (planejado) |
| `l10n_br_nfe` | [SPEC-CAD-cnpj-alfanumerico](specs/CAD/SPEC-CAD-cnpj-alfanumerico.md) (planejado) | [CAP-CAD-identificacao-cnpj](capacidades/CAD/CAP-CAD-identificacao-cnpj.md) (planejado) |

## Specs

| Spec | Título | Status | Capacidade | Requisitos por estado |
| --- | --- | --- | --- | --- |
| [SPEC-CAD-cnpj-alfanumerico](specs/CAD/SPEC-CAD-cnpj-alfanumerico.md) | CNPJ alfanumérico no cadastro, na validação e na chave de acesso | em-revisao | [CAP-CAD-identificacao-cnpj](capacidades/CAD/CAP-CAD-identificacao-cnpj.md) | pr: 5, nada: 2 |

## Capacidades

### CAD - Cadastro

| Capacidade | Título | Status | Specs |
| --- | --- | --- | --- |
| [CAP-CAD-identificacao-cnpj](capacidades/CAD/CAP-CAD-identificacao-cnpj.md) | Identificação de pessoa jurídica pelo CNPJ | ativa | [SPEC-CAD-cnpj-alfanumerico](specs/CAD/SPEC-CAD-cnpj-alfanumerico.md) |

## Normas

| Norma | Título | Tipo | Status | Confiança | Trechos | Artefatos |
| --- | --- | --- | --- | --- | --- | --- |
| [N-IN-RFB-2229-2024](normas/N-IN-RFB-2229-2024.yaml) | Instrução Normativa RFB nº 2.229, de 15 de outubro de 2024: número de inscrição no CNPJ em formato alfanumérico | instrucao-normativa | norma | oficial | 1 | 0 |
| [N-NT-2026.004](normas/N-NT-2026.004.yaml) | Nota Técnica 2026.004: atualização do schema da NF-e e da NFC-e para o CNPJ alfanumérico | nota-tecnica | nt | secundaria | 2 | 0 |
| [N-NT-CONJUNTA-2025.001](normas/N-NT-CONJUNTA-2025.001.yaml) | Nota Técnica Conjunta 2025.001: CNPJ alfanumérico nos documentos fiscais eletrônicos (NF-e, NFC-e, CT-e, CT-e OS, GTV-e, MDF-e, BP-e, NF3e, NFCom) | nota-tecnica | nt | oficial | 2 | 0 |
| [N-RFB-PR-CNPJ-ALFANUMERICO](normas/N-RFB-PR-CNPJ-ALFANUMERICO.yaml) | Perguntas e Respostas: CNPJ alfanumérico | perguntas-e-respostas | nt | oficial | 4 | 1 |

## Marcos

| Data | Marco | O que muda | Status da data |
| --- | --- | --- | --- |
| 2026-07-01 | [M-2026-07-01-cnpj-alfanumerico](marcos/M-2026-07-01-cnpj-alfanumerico.yaml) | A Receita passa a inscrever CNPJs com letras nas 12 primeiras posições. A partir daqui qualquer cadastro, documento fisc... | norma |

## Casos de QA

| Caso | Título | Módulo | Estado | Requisitos |
| --- | --- | --- | --- | --- |
| BR-BASE-CNPJALFA-001 | O cadastro aceita um CNPJ alfanumérico válido e mostra a máscara | `l10n_br_base` | pendente | REQ-cnpj-alfanumerico-01 |
| BR-BASE-CNPJALFA-002 | Um CNPJ alfanumérico com dígito verificador errado é recusado | `l10n_br_base` | pendente | REQ-cnpj-alfanumerico-02 |

## Decisões

| Decisão | Título | Data | Status |
| --- | --- | --- | --- |
| [ADR-0001-specs-em-docs-por-branch](decisoes/ADR-0001-specs-em-docs-por-branch.md) | Especificações vivem em docs/ na raiz de cada branch e viajam com o módulo | 2026-10-04 | proposta |
