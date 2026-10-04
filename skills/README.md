# Skills do l10n-brazil

Documentação estruturada para agentes de desenvolvimento trabalharem na localização
brasileira com menos adivinhação, no mesmo formato que o Odoo publica em `odoo/odoo`
(pasta `skills/`, branch 20.0 e master). Formato: https://agentskills.io

| Skill                     | Para quê                                                                                                                                                                                                              |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `l10n-brazil-guidelines/` | Regras da casa que o core não cobre: lastro normativo, rejeição do fisco como dado, CNPJ e chave como texto, convenções da OCA (bump, README, dependências, `Assisted-by`), testes com mock do fisco e `mute_logger`. |
| `l10n-brazil-spec/`       | Como criar e atualizar spec, capacidade, norma, marco, caso de QA e ADR em `docs/`; o passo de porte entre séries; o que o agente não decide.                                                                         |

As skills do Odoo (`odoo-guidelines`, `odoo-review`, `odoo-security`,
`odoo-web-guidelines`) continuam valendo e são referenciadas daqui como irmãs; instale
todas juntas.

## Instalação

Copie esta pasta e a pasta `skills/` do `odoo/odoo` (branch 20.0) para o lugar que o seu
harness lê, em geral `.claude/skills/` ou `.agents/skills/` na raiz do diretório de onde
o agente é lançado. Instalação global depende do harness.

## Uso

Reinicie a sessão do agente. Ao pedir "revise este PR" ou "atualize a spec do módulo", o
agente carrega a skill correspondente sozinho. Esta pasta existe só na branch canônica
(a série mais nova); as skills valem para trabalhar em qualquer série, porque são
instaladas no harness e não na branch.
