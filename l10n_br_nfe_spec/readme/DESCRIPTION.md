Este módulo contem a estrutura de dados da Nota Fiscal Electrônica
(NF-e). Um módulo que usa ele é o módulo l10n_br_nfe que permite
transmitir as NF-e's.

## Geração

O código dos mixins Odoo desse módulo é 100% gerado a partir dos últimos
esquemas xsd da Fazenda usando xsdata e essa extensão dele:

<https://github.com/akretion/xsdata-odoo>

Para accessar aos schemas xsd, pode ser mais facil fazer um clone da lib
nfelib e gerar o codigo dentro da pasta:

``` bash
git clone https://github.com/akretion/nfelib
cd nfelib
export XSDATA_SCHEMA=nfe; export XSDATA_VERSION=40; export XSDATA_SKIP="^ICMS.ICMS\d+|^ICMS.ICMSSN\d+"
xsdata generate nfelib/nfe/schemas/v4_0  --package nfelib.nfe.odoo.v4_0 --output=odoo
mv nfelib/odoo/nfe/v4_0 <caminho_do_odoo>/l10n_br_nfe_spec/models/v4_0
```

## Prefixo dos campos e versão

Com até uns 800 campos fiscais apenas na NF-e, com uma meia dúzia de
documentos fiscais complexos, com 3000 módulos OCA, existiria um risco
real de conflito com os nomes de campos vindo dos esquemas. Além disso,
temos várias versões da NFe, a 3.1, a 4.0 etc...

Nisso foi decidido que cada campo tem um prefixo composto do nome do
schema e de alguns dígitos da versão do esquema. No caso nfe40\_. A
escolha de 2 dígitos permite que uma atualização menor do esquema use os
mesmos campos (e dados no banco então) e que um simples update Odoo
(--update=...) consiga resolver a migração. Enquanto que para uma
mudança maior como de 3.1 para 4.0, seria assumido de usar novos campos
e novas tabelas (para os objetos não Odoo) e que a lib nfelib iria
trabalhar com os campos da versão maior do documento fiscal considerado.

## Casos das tags de ICMS e ICMSSN

Para facilitar a validação das tags de ICMS e ICMSSN, o esquema contem
tags especificas para cada tipo desses impostos. Porem, Depois no Odoo o
modelo é diferente com uma class apenas. Se a gente injectasse todos
esses mixins de ICMS e ICMSSN na mesma class Odoo a gente teria colisão
de campos, com campos com o mesmo nome e seleções diferentes... Para
evitar esses problemas, filtramos as classes desses tags (usando o
export XSDATA_SKIP antes de chamar xsdata generate). De qualquer forma,
já que o Odoo e o módulo l10n_br_fiscal tem modelos proprios para os
impostos temos que assumir que o mapping das tags de impostos nao pode
ser tão automatizada.
