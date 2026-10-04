---
name: l10n-brazil-spec
description: >-
  How to create and update the living specifications of the Brazilian localization
  (OCA/l10n-brazil) under docs/: specs, capabilities, norms, milestones, QA cases and
  ADRs, with their schemas, vocabularies and validator. Use when a change alters fiscal
  behavior, when porting or migrating a module between series, or when asked to document
  what the localization must do.
---

# Especificações vivas do l10n-brazil

`docs/` é dado validado por máquina, não prosa. Leia `docs/README.md` uma vez; depois
use esta skill como procedimento. O validador é `python docs/scripts/validar.py` (também
roda no pre-commit como `docs-validar`); o índice é
`python docs/scripts/gerar_index.py`.

## Onde cada coisa mora

| Entidade                               | Arquivo                                      | Só na branch canônica? |
| -------------------------------------- | -------------------------------------------- | ---------------------- |
| Norma `N-<slug>`                       | `docs/normas/N-<slug>.yaml`                  | sim                    |
| Marco `M-<data>-<slug>`                | `docs/marcos/M-<data>-<slug>.yaml`           | sim                    |
| Glossário                              | `docs/GLOSSARIO.md`                          | sim                    |
| Capacidade `CAP-<DOM>-<slug>`          | `docs/capacidades/<DOM>/CAP-<DOM>-<slug>.md` | não                    |
| Spec `SPEC-<DOM>-<slug>`               | `docs/specs/<DOM>/SPEC-<DOM>-<slug>.md`      | não                    |
| Caso de QA `BR-<CAMADA>-<FAMILIA>-NNN` | `docs/casos/<familia>.yaml`                  | não                    |
| Decisão `ADR-NNNN-<slug>`              | `docs/decisoes/ADR-NNNN-<slug>.md`           | não                    |

A branch é a série. A spec descreve a série da branch em que está; a comparação entre
séries é gerada fora. Esquemas em `docs/schema/`, vocabulários em `docs/taxonomia/`,
modelos em `docs/_template/`.

## Procedimentos

### Mudança de comportamento (o caso comum)

1. Ache a spec pelo `docs/INDEX.md` (módulo -> specs) ou pelo link em
   `<modulo>/readme/DEVELOP.md`. Não existe? Vá para "Spec nova".
2. Ache o requisito. Não existe? Acrescente `### REQ-<slug>-NN: ...` com o próximo NN;
   nunca renumere nem reaproveite NN de requisito obsoleto.
3. Escreva o comportamento como frase checável com sim ou não, o cenário com números
   reais (datas, códigos, valores) e o teste alvo
   (`modulo/tests/test_arquivo.py::Classe::test_metodo`).
4. Commit separado do código, no mesmo PR: `[IMP] docs: SPEC-...: ...`. Deixe `Estado`
   como está (ou `pr`); quem mescla muda para `pronto` com `Evidência` e `Visto em` (SHA
   em que o teste passou nesta branch).
5. Rode o validador e regenere o índice.

### Spec nova

1. Copie `docs/_template/spec.md` para `docs/specs/<DOM>/SPEC-<DOM>-<slug>.md`. O
   domínio vem de `docs/taxonomia/dominios.yaml`; a capacidade precisa existir (crie a
   partir de `_template/capacidade.md` se não existir).
2. Preencha `seams` (fronteiras públicas onde o teste encosta: ação do usuário, método
   público, cliente do webservice, arquivo importado) e `invariantes` (o que nunca pode
   quebrar). Fora de `rascunho`, os dois são obrigatórios.
3. Módulo que ainda não existe nesta branch vai em `modulos_planejados`. Quando ele
   nascer, o primeiro PR dele acrescenta a linha
   `Especificação: docs/specs/<DOM>/SPEC-<DOM>-<slug>.md` em
   `<modulo>/readme/DEVELOP.md` e move o módulo para `modulos`.
4. Toda norma citada precisa existir em `docs/normas/` com o trecho citado
   (`N-<slug>#<trecho>`). Norma nova só na branch canônica.

### Norma ou marco novo (branch canônica)

1. Copie `docs/_template/norma.yaml`. `confianca: oficial` só com fonte do próprio
   órgão; imprensa e fornecedor são `secundaria`. Trecho descreve o que o texto fixa,
   sem interpretar; interpretação vai em `observacoes` com `TODO(mantenedor)`.
2. Leiaute, XSD, descritor ou PDF oficial entra em `artefatos` com `url`, `sha256` e
   `tamanho`; o arquivo fica fora do git.
3. Marco: a data do id e o campo `data` coincidem; `status_data` diz a firmeza da data.

### Porte e migração entre séries

O `oca-port` aplica o patch dentro da pasta do addon e não leva `docs/`. Depois de
portar o código:

1. `git checkout <serie de origem> -- docs/specs/<DOM>/SPEC-<DOM>-<slug>.md` (e
   `docs/casos/<familia>.yaml`, se houver).
2. Revise `Estado`, `Evidência` e `Visto em` de cada requisito para esta série; o que
   não veio no porte volta a `nada`.
3. Em migração de módulo, a pasta chega com `readme/DEVELOP.md` apontando para a spec:
   sem ela o validador acusa link quebrado.

### Caso de QA

Copie `docs/_template/caso.yaml` ou acrescente ao arquivo da família. Sem campo
`series`. `estado: coberto` exige `visto_em`. Ligue aos requisitos em `requisitos`.

### ADR

Só para decisão de interesse da comunidade (onde um dado mora, qual fonte vale, qual
protocolo se adota). Copie `docs/_template/adr.md`; status começa em `proposta`.

## Regras de autoria

- Requisito, invariante e guideline são frases que se conferem com sim ou não. "Não
  converte CNPJ em inteiro", não "trata o CNPJ corretamente".
- Porquê e exceções vêm depois da regra, nunca no lugar dela. Quem proíbe diz a
  alternativa.
- Sem caminho real de arquivo dentro de spec e guideline (envelhece sem ninguém checar).
  As únicas referências de caminho são o teste alvo e o ponteiro em `readme/DEVELOP.md`,
  que o validador confere.
- Exemplo é esquemático e mínimo; valores fiscais vêm de exemplo oficial ou de caso real
  anonimizado, nunca inventados.
- Histórico e evidência se acrescentam, nunca se reescrevem.
- Pontuação ASCII (sem travessão, aspas curvas nem reticências como caractere único);
  acentos do português são bem-vindos. O validador recusa os tipográficos.

## O que o agente não faz

- Não decide questão legal nem resolve divergência entre fontes: registra em
  `questoes_abertas` com `dono: TODO(mantenedor)`.
- Não cria norma a partir de memória: só com a fonte aberta e lida.
- Não marca `pronto`, não altera `Visto em` de requisito que não testou nesta branch,
  não apaga requisito (vira `obsoleto`).
- Não mistura planejamento (prioridade, prazo, dono, cliente) em `docs/`.

## Checklist antes do PR

- `python docs/scripts/validar.py` sem erro; `python docs/scripts/gerar_index.py`
  rodado.
- Spec em commit separado do código, com `Assisted-by: <ferramenta>` se houve IA.
- Nenhum `TODO(mantenedor)` novo sem dizer o que falta conferir.
