**Português**
Para configurar esse modulo é preciso:

* Rodar a biblioteca BRCobranca como um micro-serviço https://github.com/akretion/boleto_cnab_api .
* Informar a variável de ambiente **BRCOBRANCA_API_URL** no arquivo de configuração do Odoo ou se estiver usando o docky na seção enviroment https://github.com/akretion/docky-odoo-brasil/blob/12.0/docker-compose.yml#L3 , exemplo:
  **BRCOBRANCA_API_URL=http://boleto_cnab_api:9292**
* Verifique se os Códigos de Movimento do CNAB a ser usado existem em Faturamento > Configurações > Administração > Códigos de Instrução do Movimento CNAB, se for necessário criar considere fazer um PR para adicionar como dados aqui https://github.com/OCA/l10n-brazil/blob/12.0/l10n_br_account_payment_order/data/l10n_br_cnab_mov_instruction_code_data.xml .
* Verifique se os Códigos de Retorno do Movimento do CNAB a ser usado existem em Faturamento > Configurações > Administração > Códigos de Retorno de Movimento CNAB, se for necessário criar considere fazer um PR para adicionar como dados aqui https://github.com/OCA/l10n-brazil/blob/12.0/l10n_br_account_payment_order/data/l10n_br_cnab_return_move_code_data.xml .
* Criar a Conta Bancária referente ao CNAB em Faturamento > Configurações > Contabilidade > Contas Bancárias .
* Automaticamente será criado um Diário Contábil referente a conta bancária em Faturamento > Configurações > Contabilidade > Diários na aba **Informações Referentes a Importação** informe as configurações de Retorno do CNAB nos campos "Tipo de Importação", "Conta de Recebimento/Pagamento", "Criação de Contra-Partida" e se deve ser feita a reconciliação automática ao importar o arquivo em "Reconciliar Automaticamente o Retorno de Pagamento".
* Em Faturamento > Configurações > Administração > Modos de Pagamento criar um Modo de Pagamento com as informações do CNAB, no campo "Diário de Banco Fixo" informar o Diário Contábil da conta bancária e se for o caso, e é recomendado, marcar a opção "Adicionar automaticamente ao validar a fatura" para não ser preciso fazer manualmente.
* Caso o CNAB e Banco escolhidos possua um campo especifico que seja preciso implementar considere fazer um PR no modulo l10n_br_account_payment_order aqui https://github.com/OCA/l10n-brazil/blob/12.0/l10n_br_account_payment_order/models/l10n_br_cnab_boleto_fields.py#L307 .
* Configure as permissões de acesso dos usuários, as opções são CNAB "Usuário" e "Gerente".

**English**
To configure this module, you need to:

* Run BRCobranca as micro-service https://github.com/akretion/boleto_cnab_api.
* Inform the envoriment variable BRCOBRANCA_API_URL in the config odoo file or if are use docky in the section enviroment https://github.com/akretion/docky-odoo-brasil/blob/12.0/docker-compose.yml#L3 , example:
  **BRCOBRANCA_API_URL=http://boleto_cnab_api:9292**
* Check if the CNAB Instruction Movement Code to be use exist in Invoicing > Configuration > Management > CNAB Movement Instruction Code if necessary create please consider make PR to add as data in https://github.com/OCA/l10n-brazil/blob/12.0/l10n_br_account_payment_order/data/l10n_br_cnab_mov_instruction_code_data.xml .
* Check if the CNAB Return Move Code to be use exist in Invoicing > Configuration > Management > CNAB Return Move Code if necessary create please consider make PR to add as data in https://github.com/OCA/l10n-brazil/blob/12.0/l10n_br_account_payment_order/data/l10n_br_cnab_return_move_code_data.xml .
* Create an Bank Account referent of CNAB in Invoicing > Configuration > Accounting > Bank Accounts .
* Automatic will be create an Account Journal refer to bank account in Invoicing > Configuration > Accounting > Journals in tab **Import related infos** inform parameters of CNAB Return in fields "Type of Import", "Receivable/Payable Account", "Create Counterpart", and if should make automatic reconciliation when import the file in "Automatic Reconcile payment returns".
* In Invoicing > Configuration > Management > Payment Modes create an Payment Mode with CNAB information, in the field "Fixed Bank Journal" inform the Account Journal of bank account and mark if "Automatically add when validating the invoice" so that you don't have to do it manually.
* Configure user access permissions, CNAB options are "User" and "Manager".
