Verifique se o Banco e o tipo CNAB usado 240 ou 400 possuem os Códigos de Instrução do Movimento e os Códigos de Retorno do Movimento em:  
- Faturamento \> Configurações \> Administração \> CNAB Código de
  Movimento de Instrução
- Faturamento \> Configurações \> Administração \> CNAB Código de
  Retorno do Movimento

Caso seja preciso cadastrar por favor considere fazer um PR nesse modulo
acrescentando em
l10n_br_account_payment_order/data/cnab_codes/banco_X_cnab_Y_Z.xml assim
em proximas implementações já não será preciso cadastra-los.

Informe os dados do CNAB usado no cadastro do:

> - Faturamento \> Configurações \> Administração \> Modos de Pagamento

Verifique as permissões de acesso dos usuários que vão utilizar o CNAB,
existe o Usuário e o Gerente CNAB.

IMPORTANTE: Como o CNAB envolve dinheiro e o caixa da empresa a
segurança e a rastreablidade são fundamentais e como as configurações
especificas de cada CNAB estão no Modo de Pagamento/account.payment.mode
foi incluído nele o objeto mail.thread que registra alterações feitas em
campos importantes, porém campos many2many não estão sendo registrados
pelo track_visibility( ver detalhes aqui
l10n_br_account_payment_order/models/account_payment_mode.py#L59), e um
campo especifico e importante que armazena os Codigos de Retorno do CNAB
que devem gerar Baixa/Liquidação é desse tipo, portanto as alterações
referentes a esse campo não estão sendo registradas. No repositorio
<https://github.com/OCA/social/tree/12.0> da OCA existe um modulo para
corrigir isso o
<https://github.com/OCA/social/tree/12.0/mail_improved_tracking_value> ,
por isso considere e é RECOMENDADO incluir esse modulo na implementação
para corrigir esse problema. A inclusão da dependencia desse modulo aqui
está pendente de aprovação.
