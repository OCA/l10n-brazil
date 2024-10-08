Ao criar e Confirmar uma **Fatura** que tem um **Modo de Pagamento** que tenha uma **Configuração CNAB** definida deverá aparecer o botão de **Imprimir Boleto**, caso esteja marcado no Modo de Pagamento a opção de **Adicionar automaticamente ao validar a fatura** será criada ou adicionada em uma **Ordem de Pagamento** as linhas de pagamentos do CNAB, se a opção não estiver marcada será preciso fazer isso manualmente podendo ser feito tanto na Fatura quanto na Ordem de Pagamento.

Ao Confirmar essa **Ordem de Pagamento** será possível gerar o **Arquivo de Remessa CNAB** a ser enviado ao Banco, é importante confirmar o envio do arquivo alterando o status da ordem para **Arquivo Enviado**, essa informação é usada para validar se existe uma instrução CNAB pendente antes de se poder criar outra.

Alterações de CNAB como Alteração da Data de Vencimento, Protesto, Conceder Abatimento e etc podem ser feitas na própria Fatura em:

**Faturamento > Clientes > Faturas**

Na aba **Recebimentos** na última coluna existe o botão **Atualizar Informação CNAB** ao clicar em uma linha essa opção também aparece, ao fazer uma alteração é criada ou adicionada em uma Ordem de Pagamento a **Instrução de Movimento CNAB** selecionada.

A importação do **Arquivo CNAB de Retorno** pode ser feita em:

**Faturamento > Financeiro > CNAB > Importar Arquivo de Lote**

ou no próprio Diário em:

**Faturamento > Configurações > Financeiro > Diários**

Na aba **Informações Referentes a Importação** no botão **Arquivo de lote de importação**.

Toda importação de arquivo de retorno cria um **LOG** que pode ser consultado em:

**Faturamento > Financeiro > CNAB > Registro de Retorno de CNAB**

Caso o **Código de Retorno CNAB** recebido seja um dos **Códigos de Liquidação do Retorno do Movimento**, definidos na **Configuração CNAB** usada no **Modo de Pagamento**, será criada uma **Entrada de Diário** com os valores, quando existirem de **Desconto, Juros/Mora, Tarifa Bancária, Abatimento** e o **Valor Recebido** a ser reconciliado com a linha da **Fatura** referente, os lançamentos são separados de acordo com as **Contas Contabéis** definidas na **Configuração CNAB**, a linha para reconciliar a Fatura precisam ser iguais por isso o valor é:

**valor_recebido_calculado = valor_recebido + valor_desconto + valor_abatimento - valor_juros_mora**

Quando marcada a opção de **Reconciliação Automática** a **Entrada de Diário** será movida para o status **Lançado** automaticamente ao importar o arquivo, se essa opção não estiver marcada isso deverá ser feito manualmente.
