Este módulo contem a estrutura de dados da Nota Fiscal Electrônica (NF-e).
Um módulo que usa ele é o módulo `l10n_br_nfe` que permite transmitir as NF-e's.


Geração
~~~~~~~

O código dos mixins Odoo desse módulo é 100% gerado a partir dos últimos esquemas XSD da Fazenda usando generateDS e essa extensão dele:

https://github.com/akretion/generateds-odoo

Depois de baixar os esquemas na pasta /tmp/generated/schemas/nfe/v4_00 basta fazer o comando:

.. code-block:: bash

   python gends_run_gen_odoo.py -f -l nfe -x 4_00 -e '^ICMS\d+|^ICMSSN\d+' -d . -v /tmp/generated/schemas/nfe/v4_00/leiauteNFe_v4.00.xsd


Prefixo dos campos e versão
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Com até uns 800 campos fiscais apenas na NF-e, com uma meia dúzia de documentos fiscais complexos,
com 3000 módulos OCA, existiria um risco real de conflito com os nomes de campos vindo dos esquemas.
Além disso, temos várias versões da NFe, a 3.1, a 4.0 etc...

Nisso foi decidido que cada campo tem um prefixo composto do nome do schema
e de alguns dígitos da versão do esquema. No caso `nfe40_`. A escolha de 2 dígitos permite
que uma atualização menor do esquema use os mesmos campos (e dados no banco então) e que um simples
update Odoo (--update=...) consiga resolver a migração. Enquanto que para uma mudança maior
como de 3.1 para 4.0, seria assumido de usar novos campos e novas tabelas (para os objetos não Odoo)
e que a lib nfelib iria trabalhar com os campos da versão maior do documento fiscal considerado.


Casos das tags de ICMS e ICMSSN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Para facilitar a validação das tags de ICMS e ICMSSN, o esquema contem tags especificas para cada tipo desses impostos.
Porem, Depois no Odoo o modelo é diferente com uma class apenas. Se a gente injectasse todos esses mixins de ICMS e ICMSSN na mesma class Odoo
a gente teria colisão de campos, com campos com o mesmo nome e seleções diferentes... Para evitar esses problemas, filtramos as classes
desses tags (opção -x no generateds-odoo). De qualquer forma, ja que o Odoo e o módulo l10n_br_fiscal tem modelos proprios para os impostos
temos que assumir que o mapping das tags de impostos nao pode ser tão automatizada.
