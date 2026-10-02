Se a **Política de Faturamento de Compras** estiver definida como **Ordem de Recebimento/Stock Picking** é possível criar tanto uma Fatura para uma Ordem de Recebimento quanto uma Fatura para diversas Ordens de Recebimentos:

* Caso uma Fatura para uma Ordem de Recebimento

Na **Ordem de Recebimento**, referente ao **Pedido de Compra**, depois de **Validar** essa Ordem deverá aparecer o botão **Criar Fatura** onde ao clicar será possível criar a Fatura, nesse caso o campo **Grupo** estará **Coleta**.

* Caso uma Fatura para diversas Ordens de Recebimento

Por estender o **l10n_br_stock_account** é possível criar uma **Fatura Agrupada**, para isso é preciso ir na 'Visão Lista/Tree View' selecionar as **Ordens de Recebimentos**, criadas a partir de diversos **Pedidos de Compras** e que possuem o mesmo **Parceiro/Fornecedor**, clicar no botão **Ação** em seguida **Criar rascunho das faturas** e no campo **Grupo** selecionar **Parceiro** para assim criar apenas uma Fatura ou seja N Pedidos de Compras com N Ordens de Recebimento de um mesmo Fornecedor podem ter apenas uma Fatura/Documento Fiscal relacionado.
