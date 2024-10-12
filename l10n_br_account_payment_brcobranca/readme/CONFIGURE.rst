Para configurar esse módulo é preciso:

Rodar a biblioteca **BRCobranca** como um micro-serviço **Boleto_CNAB_API**.

Informar a variável de ambiente **BRCOBRANCA_API_URL**, existem três opções:

* No arquivo de configuração do **Docker Compose File** na seção **enviroment**, por exemplo https://github.com/akretion/docky-odoo-brasil/blob/12.0/docker-compose.yml#L3 , incluir:
    **BRCOBRANCA_API_URL=http://boleto_cnab_api:9292**
* No arquivo de Configuração do Odoo, incluir:
    **brcobranca_api_url=http://boleto_cnab_api:9292**
* No Odoo crie um Parâmetro de Sistema como:
    **brcobranca_api_url=http://boleto_cnab_api:9292**

Verifique se os Códigos do CNAB do Banco que será usado existem em:

**Faturamento > Configurações > Administração > Códigos CNAB**

Caso seja preciso criar por favor considere fazer um PR acrescentando os Códigos em l10n_br_account_payment_order/data/cnab_codes/banco_X_cnab_Y_Z.xml assim em próximas implementações já não será preciso cadastra-los ajudando também na construção desse banco de conhecimento, você pode ver os casos que já existem hoje no módulo `l10n_br_account_payment_order <https://github.com/OCA/l10n-brazil/tree/14.0/l10n_br_account_payment_order>`_.

Crie uma **Configuração CNAB**, é onde serão armazenadas as informações específicas de cada caso como a Carteira, Convênio, Código do Benificiário, Códigos de Instrução e Retorno do Movimento, etc, em:

**Faturamento > Configuração > Administração > Configurações CNAB**

Verifique se a **Conta Bancária** referente ao CNAB já foi cadastrada em:

**Configurações > Usuários e Empresas > Empresas**

Clique no Contato associado, e na aba Faturamento veja se a **Contas Bancária** referente ao CNAB já existe e se as informações estão corretas, se não existir veja de criar informando os dados Número da Conta, Agencia, etc.

Ao cadastrar a **Conta Bancária** deve ser criado automaticamente um **Diário Contábil**, ou se já havia sido cadastrada o Diário já deve existir, verifique em:

**Faturamento > Configurações > Financeiro > Diários**

Confirme se as informações estão corretas, campo **Tipo** deve estar como Banco, na aba **Lançamentos do Diário** em **Número da Conta Bancária** deve estar preenchido com a **Conta Bancária** do CNAB e na aba **Configuração de Pagamentos** os Metódos que serão usados, 240 ou 400, devem estar marcados.

Na aba **Informações Referentes a Importação** informe as configurações de Retorno do CNAB nos campos **Tipo de Importação**, **Conta de Recebimento/Pagamento**, **Criação de Contra-Partida** e se deve ser feita a reconciliação automática ao importar o arquivo em **Reconciliar Automaticamente o Retorno de Pagamento**.

Crie um **Modo de Pagamento** ou use um existente em:

**Faturamento > Configuração > Administração > Modos de Pagamento**

Informe o **Diário Contábil** referente ao Banco e a **Configuração CNAB** que deverá ser utilizada, no campo **Diário de Banco Fixo** informar o Diário Contábil da Conta Bancária e se for o caso, e é recomendado, marcar a opção **Adicionar automaticamente ao validar a fatura** para não ser preciso fazer manualmente.

Caso o CNAB e Banco escolhidos possua um campo específico que seja preciso implementar considere fazer um PR no módulo **l10n_br_account_payment_order** aqui https://github.com/OCA/l10n-brazil/blob/14.0/l10n_br_account_payment_order/models/l10n_br_cnab_boleto_fields.py#L307 .

Configure as permissões de acesso dos usuários, as opções são CNAB **Usuário** e **Gerente**.
