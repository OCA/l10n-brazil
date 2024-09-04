Este módulo é comum entre os planos de contas da localização brasileira.

## Herança

Assim como na localização espanhola
(<https://github.com/OCA/l10n-spain>) que já permitia carregar vários
planos de contas, este módulo define um plano de conta básico que é
depois estendido pelos planos de contas específicos (ITG 1000, empresas
do regime normais de determinados setores...). Isso permite mutualizar
um pouco a configuração entre os planos, especialmente para carregar o
plano customizado de uma determinada empresa. Por exemplo, no
repositório da localização este módulo é herdado por 2 módulos:

``` text
l10n_br_coa
/         \
l10n_br_coa_simples     l10n_br_coa_generic
```

Em particular, definir aqui os tipos de contas usados na DRE e no
Balanço Patrimonial (módulo ´´l10n_br_mis_report´´) facilita a adaptação
desses relatorios para esses diversos planos de contas.

## Contas contábeis

Uma outra característica é que ao contrário do que acontece na Europa, o
primeiro mercado que foi alvejado pelo Odoo, no Brasil tem muitas
alíquotas, pelo menos para as empresas do regime normal. Sendo assim,
não é bem viável ter um objeto `account.tax` para cada alíquota como o
Odoo nativo espera (fazíamos isso até a versão 10.0 mas era muito
trabalhoso para manter). Em vez disso temos tabelas específicas para
armazenar todas as alíquotas no módulo `l10n_br_fiscal` e temos
registros `account.tax` apenas para alíquotas de cada família. O módulo
`l10n_br_account` faz a ligação entre o `account.tax` do Odoo e os
registros `l10n_br_fiscal.tax` para cada alíquota da localização. Vale a
pena notar que nos EUA o Odoo também não usa um registro `account.tax`
por alíquota, em vez disso eles geralmente usam conectores e serviços
(como AvaTax) para pegar as alíquotas de uma determinada operação.

Neste caso a configuração contábil não podia ser carregada nem pelo
`account.tax` nem pelo `l10n_br_fiscal.tax` (já que o módulo
`l10n_br_fiscal` não depende do módulo `account`). Então estendemos o
objeto `account.tax.group` para carregar as informações contábeis,
inclusive das taxas dedutíveis.

## Taxas dedutíveis

No Odoo nativo, uma taxa é considerada dedutível (como por exemplo uma
compra em outro outro país Europeu) se o registro `account.tax` tem uma
alíquota negativa. Porém já que como falamos aqui é preferível de não
gerenciar um `account.tax` por alíquota. Por isso temos um flag
adicional no `account.tax` e `account.tax.template` através do
`account.tax.mixin` para saber se é uma taxa dedutível.

## Template

Foi ainda necessário sobrescrever a função que instancia um plano de
contas a partir de um template para propagar essas informações.
