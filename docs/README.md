# Especificações vivas da localização brasileira

Esta pasta liga a norma (lei, nota técnica, leiaute, pronunciamento contábil)
ao comportamento que a localização deve ter, ao teste que o prova e ao estado
disso **nesta série**. É dado, não prosa: cada arquivo tem esquema e vocabulário
fechado, e `docs/scripts/validar.py` roda no pre-commit.

## Como ler

- Comece por [`INDEX.md`](INDEX.md) (gerado): módulo -> specs, specs -> normas,
  marcos, casos e decisões.
- Uma **spec** (`specs/<DOM>/SPEC-<DOM>-<slug>.md`) agrupa os requisitos de uma
  capacidade: cada requisito tem norma com trecho, comportamento checável,
  cenário com números, teste alvo, estado nesta série e evidência.
- Uma **capacidade** (`capacidades/<DOM>/CAP-<DOM>-<slug>.md`) diz o que o ERP
  precisa saber fazer, independente de módulo.
- **Normas** (`normas/N-<slug>.yaml`) e **marcos** (`marcos/M-<data>-<slug>.yaml`)
  são o calendário legal: o requisito aponta para eles, nunca o contrário.
- **Casos de QA** (`casos/<familia>.yaml`) são jornadas verificáveis pela
  interface e por RPC, ligadas aos requisitos que cobrem.
- **Decisões** (`decisoes/ADR-NNNN-<slug>.md`) registram escolhas de
  arquitetura de interesse da comunidade.
- [`GLOSSARIO.md`](GLOSSARIO.md): o vocabulário do domínio e o que evitar.

## A branch é a série

A spec desta branch descreve esta série. Não existe tabela "por série" dentro
dela; a comparação entre séries é uma visão gerada lendo `docs/` de todas as
branches ativas e publicada fora delas. Divergência entre séries é informação
(requisito pronto numa e ausente noutra é uma fila de porte), não erro.

O que não depende da série fica só na **branch canônica** (a série mais nova,
hoje 20.0): `normas/`, `marcos/`, `GLOSSARIO.md` e `skills/`. Nas outras
branches esta página aponta para lá. Esquemas, taxonomia e scripts existem em
todas, porque o validador precisa deles.

Esta branch é a canônica.

## Como contribuir

1. Mudou um comportamento? A spec muda no mesmo PR, em commit separado do
   código. Atualize `Estado`, `Evidência` (teste nomeado) e `Visto em` (SHA em
   que o teste passou nesta branch). `pronto` sem evidência é recusado.
2. Comportamento novo sem spec? Crie a spec a partir de `_template/spec.md`
   e a capacidade, se não existir. Módulo que ainda não existe entra em
   `modulos_planejados`; quando nascer, o primeiro PR dele acrescenta o ponteiro
   em `<modulo>/readme/DEVELOP.md`.
3. Norma nova ou alterada? Só na branch canônica, com `confianca` honesta:
   fonte secundária não sustenta `pronto`. Leiaute, XSD ou PDF oficial entra em
   `artefatos` com `sha256`; o arquivo em si fica fora do git.
4. Portou ou migrou um módulo? Traga a spec dele junto
   (`git checkout <serie de origem> -- docs/specs/<spec>`) e ajuste o estado. O
   `oca-port` não leva `docs/`; o link em `readme/DEVELOP.md` quebra e o
   pre-commit acusa se a spec ficar para trás.
5. Antes de abrir o PR: `pre-commit run docs-validar --all-files` (ou
   `python docs/scripts/validar.py`) e `python docs/scripts/gerar_index.py`.

Agentes seguem as mesmas regras, pelas skills em `skills/` e pelo `AGENTS.md`
da raiz; não decidem questão legal, não criam norma e não marcam `pronto`.

## Checklist ao abrir uma série nova

- Copiar `docs/` inteiro da série anterior e revisar o estado de cada
  requisito (o que não foi migrado volta a `nada` ou `desconhecido`).
- A nova série passa a ser a canônica: `normas/`, `marcos/`, `GLOSSARIO.md` e
  `skills/` ficam nela; na anterior, trocar esta seção por um ponteiro.
- Regerar `INDEX.md` e rodar o validador.
