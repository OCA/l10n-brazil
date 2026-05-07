Este módulo é a base comum para os planos de contas da localização brasileira.

## Herança

Assim como na [localização espanhola](<https://github.com/OCA/l10n-spain>),
que já permitia carregar vários planos de contas, este módulo define um plano
de contas básico que é depois estendido pelos planos de contas específicos
(ITG 1000, empresas do regime normal de determinados setores...). Isso permite
compartilhar configurações entre os planos, especialmente para carregar o
plano customizado de uma determinada empresa. Por exemplo, no
repositório da localização, este módulo é herdado pelos módulos `l10n_br_coa_simples`,
`l10n_br_coa_generic`, entre outros customizados.

```
l10n_br_coa
  ├── l10n_br_coa_simples
  ├── l10n_br_coa_generic
  ├── ...
  └── seu_plano_de_contas_customizado
```

Em particular, são definidos aqui os tipos de contas usados na DRE e no
Balanço Patrimonial (módulo `l10n_br_mis_report`) para facilitar a adaptação
desses relatórios para os diversos planos de contas.

## Contas contábeis para impostos

Uma outra característica é que, ao contrário do que acontece na Europa (o
primeiro mercado focado pelo Odoo), no Brasil existem muitas
alíquotas, pelo menos para as empresas do regime normal. Sendo assim,
não é viável ter um objeto `account.tax` para cada alíquota como o
Odoo nativo espera (fazíamos isso até a versão 10.0, mas era muito
trabalhoso para manter). Em vez disso, temos tabelas específicas para
armazenar todas as alíquotas no módulo `l10n_br_fiscal` e temos
registros `account.tax` apenas para alíquotas de cada família. O módulo
`l10n_br_account` faz a ligação entre o `account.tax` do Odoo e os
registros `l10n_br_fiscal.tax` para cada alíquota da localização. Vale a
pena notar que nos EUA o Odoo também não usa um registro `account.tax`
por alíquota; em vez disso, eles geralmente usam conectores e serviços
(como AvaTax) para obter as alíquotas de uma determinada operação.

Neste caso, a configuração contábil não podia ser carregada nem pelo
`account.tax` nem pelo `l10n_br_fiscal.tax` (já que o módulo
`l10n_br_fiscal` não depende do módulo `account`). Então, estendemos o
objeto `account.tax.group` para carregar as informações contábeis,
inclusive das taxas dedutíveis.

A partir da versão 17.0, existe também no template o método
`populate_default_br_tax_accounts`, que permite injetar em qualquer plano
de contas essas contas de impostos. Existem 2 padrões de numeração das
contas para escolher: o padrão ITG ou CFC. Uma vez geradas as contas,
elas podem ser identificadas pelo sufixo `.GEN` e modificadas manualmente.
Esse método de geração das contas de impostos é agora usado pelos módulos
`l10n_br_coa_simples` e `l10n_br_coa_generic` da localização.

## Impostos dedutíveis

No Odoo nativo, um imposto é considerado dedutível (como, por exemplo, uma
compra em outro país europeu) se o registro `account.tax` tiver uma
alíquota negativa. Porém, como mencionado anteriormente, aqui é preferível não
gerenciar um `account.tax` por alíquota. Por isso, temos um flag
adicional no `account.tax` e `account.tax.template` através do
`account.tax.mixin` para identificar se é um imposto dedutível.

## Template

Foi ainda necessário sobrescrever a função que instancia um plano de
contas a partir de um template para propagar essas informações.
