---
id: CAP-CAD-identificacao-cnpj
dominio: CAD
titulo: Identificação de pessoa jurídica pelo CNPJ
descricao: >-
  Cadastrar, validar, formatar e comparar o CNPJ de empresas e parceiros,
  numérico ou alfanumérico, e levá-lo correto aos documentos fiscais, aos
  arquivos bancários e às declarações.
status: ativa
normas:
  - N-IN-RFB-2229-2024
  - N-RFB-PR-CNPJ-ALFANUMERICO
  - N-NT-CONJUNTA-2025.001
marcos:
  - M-2026-07-01-cnpj-alfanumerico
depende_de: []
modulos: []
modulos_planejados:
  - l10n_br_base
  - l10n_br_cnpj_search
  - l10n_br_fiscal
  - l10n_br_nfe
  - l10n_br_fiscal_dfe
---

# Identificação de pessoa jurídica pelo CNPJ

O CNPJ é a chave que liga o cadastro ao fisco, aos bancos e aos documentos
eletrônicos. A capacidade cobre o ciclo inteiro do número: entrada (digitação,
importação de XML, consulta à Receita), validação do dígito verificador,
formatação com máscara, comparação para evitar duplicidade, e uso em chave de
acesso, consultas e eventos. Desde julho de 2026 o número pode conter letras,
e todo ponto que o trata como inteiro ou como sequência só de dígitos quebra.

Nesta branch nenhum módulo está mesclado ainda: os módulos listados como
planejados estão em migração (ver os PRs de migração abertos para a 20.0).

## Specs

- SPEC-CAD-cnpj-alfanumerico: aceitar, validar, normalizar e propagar o CNPJ
  alfanumérico.

## Fora desta capacidade

CPF, inscrição estadual e consulta de cadastro na Receita têm capacidades
próprias.
