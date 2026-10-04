---
name: l10n-brazil-guidelines
description: >-
  House rules of the Brazilian localization (OCA/l10n-brazil) on top of the Odoo core
  guidelines: fiscal parametrization with normative source, tax authority rejections as
  data, CNPJ and access key as text, OCA conventions (no version bump, generated README,
  external dependencies, Assisted-by trailer), tests with recorded tax authority
  responses and mute_logger. Use when writing or reviewing any file of an l10n_br addon.
---

# Regras da casa do l10n-brazil

Complementam as `odoo-guidelines` (skill irmã, em `../odoo-guidelines/`), que continuam
valendo para tudo. Aqui entra só o que a localização e a OCA acrescentam. Uma seção por
regra em `guidelines/`; nenhuma regra vale mais que outra. Leia as seções que casam com
o que você está tocando.

| Guideline                                                                                                                               | Leia quando                                                                          |
| --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [Parametrização fiscal com lastro normativo](guidelines/fiscal.md#parametrização-fiscal-com-lastro-normativo)                           | criar ou mudar regra que decide CFOP, CST, CEST, NCM, alíquota ou operação fiscal    |
| [Rejeição do fisco é dado, não exceção](guidelines/fiscal.md#rejeição-do-fisco-é-dado-não-exceção)                                      | tratar resposta de webservice (autorização, evento, consulta, inutilização)          |
| [Data e hora do fisco em UTC](guidelines/fiscal.md#data-e-hora-do-fisco-em-utc)                                                         | gravar `dhRecbto`, `dhRegEvento` ou qualquer data de protocolo                       |
| [CNPJ e chave de acesso são texto](guidelines/fiscal.md#cnpj-e-chave-de-acesso-são-texto)                                               | limpar, comparar, formatar ou montar CNPJ, CPF ou chave de acesso                    |
| [Produção e homologação sem comparação frouxa](guidelines/fiscal.md#produção-e-homologação-sem-comparação-frouxa)                       | escolher URL, serviço ou certificado pelo ambiente                                   |
| [Sequência de evento pelo maior número registrado](guidelines/fiscal.md#sequência-de-evento-pelo-maior-número-registrado)               | emitir carta de correção ou outro evento sequenciado                                 |
| [Sem bump de versão no manifest](guidelines/oca.md#sem-bump-de-versão-no-manifest)                                                      | tocar `__manifest__.py`                                                              |
| [README gerado só em módulo novo](guidelines/oca.md#readme-gerado-só-em-módulo-novo)                                                    | tocar `readme/*.md`, `README.rst` ou `static/description/index.html`                 |
| [Dependência externa pelo nome do pacote](guidelines/oca.md#dependência-externa-pelo-nome-do-pacote)                                    | `external_dependencies`, `requirements.txt`                                          |
| [Commit com IA leva Assisted-by](guidelines/oca.md#commit-com-ia-leva-assisted-by)                                                      | escrever qualquer mensagem de commit                                                 |
| [Série no título do PR, nunca no commit](guidelines/oca.md#série-no-título-do-pr-nunca-no-commit)                                       | abrir PR ou escrever commit                                                          |
| [Confirmar que a API existe nesta série](guidelines/oca.md#confirmar-que-a-api-existe-nesta-série)                                      | usar `self.env._`, `/list`, `_compute_terms` ou qualquer API lembrada de outra série |
| [Comentário explica o código, não a conversa](guidelines/oca.md#comentário-explica-o-código-não-a-conversa)                             | escrever comentário ou docstring                                                     |
| [Texto público sem detalhe interno](guidelines/oca.md#texto-público-sem-detalhe-interno)                                                | escrever PR, issue, comentário ou commit                                             |
| [Erro esperado dentro de mute_logger](guidelines/tests.md#erro-esperado-dentro-de-mute_logger)                                          | testar rejeição, exceção ou aviso                                                    |
| [Assertiva compara com valor conhecido de fora](guidelines/tests.md#assertiva-compara-com-valor-conhecido-de-fora)                      | escrever ou revisar qualquer `assert`                                                |
| [Resposta do fisco gravada, não inventada](guidelines/tests.md#resposta-do-fisco-gravada-não-inventada)                                 | mockar webservice de NF-e, CT-e, MDF-e, NFS-e, DF-e                                  |
| [Testar com o usuário que vai usar](guidelines/tests.md#testar-com-o-usuário-que-vai-usar)                                              | testar ação de usuário, job ou API                                                   |
| [Dado demo conferido no fim](guidelines/tests.md#dado-demo-conferido-no-fim)                                                            | tocar `demo/*.xml` ou `post_init_hook`                                               |
| [Teste externo só vê comportamento observável](guidelines/tests.md#teste-externo-só-vê-comportamento-observável)                        | escrever teste E2E ou por RPC                                                        |
| [company_dependent lido com with_company](guidelines/orm.md#company_dependent-lido-com-with_company)                                    | ler campo `company_dependent`                                                        |
| [Fonte em inglês; en.po é inerte](guidelines/orm.md#fonte-em-inglês-enpo-é-inerte)                                                      | escrever string de usuário ou mexer em `i18n/`                                       |
| [Marcador de schema por subpacote](guidelines/orm.md#marcador-de-schema-por-subpacote)                                                  | tocar módulo `*_spec` ou `spec_driven_model`                                         |
| [Registro principal escolhido, não o primeiro do recordset](guidelines/orm.md#registro-principal-escolhido-não-o-primeiro-do-recordset) | guardar anexo, resposta ou arquivo "principal"                                       |
| [Dado montado por script passa pelos onchanges](guidelines/orm.md#dado-montado-por-script-passa-pelos-onchanges)                        | criar empresa, parceiro ou documento fiscal por script ou teste                      |

Para acrescentar ou mudar uma guideline, siga o `AUTHORING.md` das `odoo-guidelines`:
convenção (uma linha) x regra (regra, porquê, exceções); frase checável; alternativa
nomeada; exemplo esquemático; nenhum caminho real.
