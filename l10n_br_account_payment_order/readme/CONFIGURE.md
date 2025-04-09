Verifique se os **Códigos CNAB** do Banco e da versão 240 ou 400 que serão usados principalmente os de **Instrução e de Retorno do Movimento** do CNAB existem ou se será necessário criar em:

**Faturamento > Configuração > Administração > Códigos CNAB**

Caso seja preciso criar por favor considere fazer um PR nesse módulo acrescentando os Códigos em **l10n_br_account_payment_order/data/cnab_codes/banco_X_cnab_Y_Z.xml** dessa forma nas próximas implementações já não será preciso cadastrar, isso ajuda na construção de um banco de conhecimento, salvando tanto horas de implementação por não ser necessário rever ou refazer o que foi feito como poder usar o que outros fizeram, isso também é importante porque permite testar e avaliar as diferenças entre cada caso tornando a implementação mais robusta, hoje o que temos são:

| Banco     | CNAB    | Instrução | Retorno |
|-----------|---------|-----------|---------|
| AILOS     | 240     |    X      |    X    |
| Bradesco  | 240/400 |    X      |    X    |
| Brasil    | 240/400 |    X      |    X    |
| CEF       | 240     |    X      |    X    |
| Itaú      | 240/400 |    X      |    X    |
| Santander | 240/400 |    X      |    X    |
| Sicred    | 240     |    X      |    X    |
| Unicred   | 240/400 |    X      |    X    |

Crie uma **Configuração CNAB**, é onde será armazenada as informações específicas de cada caso como a Carteira, Convênio, Código do Benificiário, Códigos de Instrução e Retorno do Movimento, etc em:

**Faturamento > Configuração > Administração > Configurações do CNAB**

Verifique se a **Conta Bancária** referente ao CNAB já foi cadastrada em:

**Configurações > Usuários e Empresas > Empresas**

Clique no Contato associado e na aba **Faturamento** veja **Contas Bancárias** se não existir veja de criar informando os dados Número da Conta, Agencia, etc.

Ao cadastrar uma **Conta Bancária** deve ser criado automaticamente um **Diário Contábil**, ou se já havia sido cadastrada o Diário já deve existir, verifique em:

**Faturamento > Configurações > Financeiro > Diários**

Verifique se as informações estão corretas, campo **Tipo** deve estar como Banco, na aba **Lançamentos do Diário** em Número da Conta Bancária deve estar preenchido com a **Conta Bancária** e na aba **Configuração de Pagamentos** os Metódos que serão usados, 240 ou 400, devem estar marcados.

Crie um **Modo de Pagamento** ou use um existente em:

**Faturamento > Configuração > Administração > Modos de Pagamento**

Informe o Diário Contábil referente ao Banco e a Configuração CNAB que deverá ser utilizada.

A partir disso sempre que for informado o **Modo de Pagamento** tanto em um Pedido de Vendas ou na Fatura o programa passa a identificar como um caso CNAB, em casos onde um cliente vai sempre usar o mesmo Modo de Pagamento também é possível deixar isso como padrão no Cadastro de Cliente assim a informação é carregada automaticamente ao informar esse Cliente em um novo Pedido de Venda ou Fatura.

Verifique as permissões de acesso dos usuários que vão utilizar o CNAB, existe o **Usuário** e o **Gerente** CNAB.

**IMPORTANTE:** Como o CNAB envolve dinheiro e o caixa da empresa a segurança e a rastreablidade são fundamentais e como as configurações especificas de cada CNAB estão na **Configuração CNAB/l10n_br_cnab.config** foi incluído nele o objeto **mail.thread** que registra alterações feitas em campos importantes, porém campos **many2many** não estão sendo registrados pelo **track_visibility** (ver detalhes aqui l10n_br_account_payment_order/models/l10n_br_cnab_config.py#L75), e um campo específico e importante que armazena os **Códigos de Retorno do CNAB** que devem gerar **Baixa/Liquidação** é desse tipo, portanto as alterações referentes a esse campo não estão sendo registradas. No repositório https://github.com/OCA/social/tree/16.0 da **OCA** existe um módulo para corrigir isso o [mail_improved_tracking_value](https://github.com/OCA/social/tree/16.0/mail_improved_tracking_value), por isso considere e é RECOMENDADO incluir esse módulo na implementação para corrigir esse problema. A inclusão da dependência desse módulo aqui está pendente de aprovação.
