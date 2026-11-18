# AGENTS.md

Repositório OCA/l10n-brazil, branch 20.0. Cada branch é uma série do Odoo; esta é a mais
nova e por isso a **canônica** de `docs/normas/`, `docs/marcos/`, `docs/GLOSSARIO.md` e
`skills/`. Este arquivo vale igual para agentes e para gente; muda só o número da série
de uma branch para outra.

## Antes de escrever código

1. Leia `docs/README.md` e o `docs/INDEX.md` do módulo que vai tocar. A spec do módulo é
   o contrato: requisitos, seams (onde o teste encosta) e invariantes (o que nunca pode
   quebrar). O módulo aponta para a spec em `<modulo>/readme/DEVELOP.md`.
2. Instale as skills de `skills/` junto com as do Odoo (`odoo/odoo`, branch 20.0, pasta
   `skills/`): `odoo-guidelines`, `odoo-review`, `odoo-security`, `odoo-web-guidelines`,
   `l10n-brazil-guidelines`, `l10n-brazil-review` (quando existir), `l10n-brazil-spec`.
   Elas se referenciam, instale todas.
3. Confirme que a API que vai usar existe nesta série (`git grep` no código desta
   branch, não na memória). Sintaxe da série nova em branch antiga passa no CI e entrega
   feature inerte.

## Ao mudar comportamento

- A spec muda no mesmo PR, em commit separado do código: `Estado`, `Evidência` (teste
  nomeado) e `Visto em` (SHA em que o teste passou aqui). Sem spec para o comportamento?
  Crie uma a partir de `docs/_template/spec.md` (skill `l10n-brazil-spec`). Não marque
  `pronto`: quem mescla marca.
- Um teste que falha antes e passa depois, pelo motivo esperado, no seam público. Erro
  esperado dentro de `mute_logger`.
- Sem bump de versão no manifest; sem README gerado em módulo existente;
  `external_dependencies` por nome de pacote.
- Commit: `[FIX] modulo: o que muda`, sem a série no título do commit (ela vai no título
  do PR), pontuação ASCII, e o trailer `Assisted-by: <ferramenta>` em todo commit com
  assistência de IA (política da OCA).

## O que um agente não faz aqui

- Não decide questão legal, não cria norma, não muda `confianca` para `oficial` sem a
  fonte do órgão. Dúvida vira `TODO(mantenedor)` ou questão aberta na spec.
- Não mescla, não comenta `/ocabot merge`, não aprova PR. Revisão termina em achados com
  arquivo, linha, cenário de falha e a guideline aplicada.
- Não publica texto com travessão, aspas curvas ou reticências como caractere único.
  Acentos do português, sim.
- Não cita cliente, infraestrutura ou branch interna de empresa em texto público.

## Antes de abrir o PR

`pre-commit run --all-files` verde (inclui `docs-validar`), e
`python docs/scripts/gerar_index.py` se tocou em `docs/`. PR só de documentação roda o
CI inteiro da série: agrupe mudanças pequenas.
