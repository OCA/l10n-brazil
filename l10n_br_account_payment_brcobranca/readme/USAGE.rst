**Português**

* Ao criar e Confirmar uma Fatura que tem um Modo de Pagamento que seja CNAB deverá aparecer o botão de "Imprimir Boleto".
* Caso esteja marcado no Modo de Pagamento a opção de "Adicionar automaticamente ao validar a fatura" será criada ou adicionada em uma Ordem de Pagamento as linhas de pagamentos do CNAB, se a opção não estiver marcada será preciso fazer isso manualmente podendo ser feito tanto na Fatura quanto na Ordem de Pagamento.
* Ao Confirmar essa Ordem de Pagamento será possível gerar o arquivo de Remessa CNAB a ser enviado ao Banco, é importante confirmar o envio do arquivo alterando o status da ordem para "Arquivo Enviado", essa informação é usada para validar se existe uma instrução CNAB pendente antes de se poder criar outra.
* Alterações de CNAB como Alteração da Data de Vencimento, Protesto, Conceder Abatimento e etc podem ser feitas na própria Fatura em Faturamento > Clientes > Faturas na aba Recebimentos na última coluna existe o botão "Atualizar Informação CNAB" ao clicar em uma linha essa opção também aparece, ao fazer uma alteração é criada ou adicionada em uma Ordem de Pagamento a Instrução de Movimento CNAB selecionada.
* A importação do arquivo CNAB de Retorno pode ser feita em Pagamentos > Importar arquivo Batch ou no próprio Diário em Faturamento > Configurações > Contabilidade > Diários na aba **Informações Referentes a Importação** o botão Importar arquivo Batch.
* Toda importação de arquivo de retorno cria uma LOG que pode ser consultado em Pagamentos > LOG de Retorno CNAB.
* Caso o Código de Retorno CNAB recebido seja um dos "Códigos de Liquidação do Retorno do Movimento" do Modo de Pagamento será criado uma Entrada de Diário com os valores quando existirem de desconto, juros/mora, tarifa bancaria, abatimento e valor a ser reconciliado com a linha da Fatura referente, os lançamentos são separados de acordo com as Contas Contabéis definidas no Modo de Pagamento, a linha para reconciliar a linha da Fatura precisam ser iguais por isso o valor é:
  valor_recebido_calculado = (valor_recebido + valor_desconto + valor_abatimento) - valor_juros_mora
* Quando marcada a opção de "Reconciliação Automatica" /a Entrada de Diário será movida para o status Lançado automaticamente ao importar o arquivo, se não estiver marcada isso deverá ser feito manualmente.

**English**

* When creating and confirming an Invoice that has a Payment Mode that is CNAB, the button should appear "Print Boleto".
* If the option to "Add automatically when validating the invoice" is marked in the Payment Mode CNAB payment lines will be created or added to a Payment Order, if the option is not marked, you will need to do this manually, which can be done both in the Invoice and in the Payment Order.
* By confirming this Payment Order it will be possible to generate the CNAB Remessa file to be sent to the Bank, it is important to confirm the upload of the file by changing the order status to "File Uploaded", this information is used to validate if there is a pending CNAB instruction before another one can be created.
* CNAB changes such as Change Due Date, Protest, Grant Rebate, etc. can be made in the Invoice itself in Invoicing > Customers > Invoices in the Receivable tab in the last column there is the button "Update CNAB Information" when clicking on a line this option also appears, when making a change it is created or added to a Payment Order the selected CNAB Movement Instruction.
* The import of the Return CNAB file can be done in Payments > Import Batch file or in the same Journal in Invoicing > Configuration > Accounting > Journals in the tab **Import related infos** the Import Batch File button.
* Every return file import creates a LOG that can be consulted in Payments > CNAB Return LOG.
* If the CNAB Return Code received is one of the "CNAB Liquidity Return Move Code" of the Payment Mode, a Journal Entry will be created with the values when there are discount, interest, tariff charge, rebate and amount to be reconciled with the referring Invoice line, entries are separated according to the Accounts defined in the Payment Mode, the line to reconcile the Invoice line need be equal so the value is:
  calculated_value_receive = (receive_amount + discount_amount + rebate_amount) - interest_amount
* When the "Automatic Reconciliation" option is checked, the Entry of Journal will be moved to the status Posted automatically when importing the file, if not checked it should be done manually.
