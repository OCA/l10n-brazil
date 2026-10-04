---
id: ADR-0001-specs-em-docs-por-branch
titulo: Especificações vivem em docs/ na raiz de cada branch e viajam com o módulo
data: 2026-10-04
status: proposta
specs_afetadas: []
---

# Especificações vivem em docs/ na raiz de cada branch e viajam com o módulo

## Contexto

O repositório tem código, PRs e revisores, mas nenhuma camada comum que ligue
a norma ao comportamento esperado, ao teste que o prova e ao estado em cada
série. Cada contribuidor trabalha pelo interesse do próprio cliente e a
referência normativa fica no corpo de cada PR. Na OCA a série é a branch, e o
código atravessa as séries por migração e por forward-port com o oca-port.

Quatro lugares foram considerados para as especificações:

- Repositório próprio: afasta a spec do código e de quem abre a branch para
  trabalhar; exige repositório novo pela configuração da OCA.
- Branch órfã no mesmo repositório: uma cópia só, mas quem abre a 16.0 não a vê.
- Dentro de cada addon: viaja de graça com o oca-port, mas espalha a
  documentação por mais de cem pastas, dificulta referência cruzada e exige
  regra de âncora para módulo que ainda não existe.
- Wiki: sem revisão por PR, sem validação, sem histórico útil.

## Decisão

1. As especificações, casos de QA, capacidades e decisões ficam em `docs/` na
   raiz de cada branch ativa. A branch é a série: a spec na 20.0 descreve a
   20.0 e não há tabela "por série" dentro dela. A comparação entre séries é
   uma visão gerada lendo `docs/` de todas as branches, publicada fora delas.
2. Normas, marcos, glossário e skills são independentes da série e existem
   só na branch mais nova; as outras apontam para ela em `docs/README.md`.
3. Cada módulo aponta para as suas specs em `readme/DEVELOP.md`. O validador
   confere o link: módulo migrado sem a spec chega com link quebrado.
4. Mudança de comportamento muda a spec no mesmo PR, em commit separado do
   código. Quem porta ou migra leva a spec junto, por passo explícito, porque
   o oca-port re-enraíza cada caminho dentro do addon e não leva `docs/`.
5. Um validador roda como hook do pre-commit, sem Odoo: esquema, ids únicos,
   vocabulários, links, módulos citados existentes ou planejados, e a regra de
   que `pronto` exige evidência e SHA.

## Consequências

- PR que só toca `docs/` roda o CI completo da série; mudanças pequenas devem
  ser agrupadas, e um filtro de caminho pode ser proposto ao template da OCA
  quando a estrutura tiver provado valor.
- `docs/` fica fora do prettier, pelo mesmo motivo de `readme/*.md`.
- Spec para módulo que ainda não existe usa `modulos_planejados`; quando o
  módulo nasce, o primeiro PR dele acrescenta o ponteiro em `readme/DEVELOP.md`.
- Divergência entre séries é informação, não erro: a visão gerada mostra
  requisito pronto numa série e ausente noutra, o que serve de fila de porte.
