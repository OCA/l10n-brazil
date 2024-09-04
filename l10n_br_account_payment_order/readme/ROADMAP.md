- Verificar a questão do campos many2many que não estão sendo
  registrados pelo track_visibility e se será incluída a dependendecia
  <https://github.com/OCA/social/tree/12.0/mail_improved_tracking_value>
  ( confirmar o problema na v14 ).
- Processo de Alteração de Carteira, falta informações sobre o processo.
- Mapear e incluir os codigos dos bancos de cada CNAB 240 / 400, aqui
  devido a quantidade de possibilidades se trata de um "roadmap"
  constante onde contamos com PRs de outros contribuidores que irão
  implementar um caso que ainda não esteja cadastrado, apesar do codigo
  permitir que o cadastro seja feito na tela nesses casos.
- Processo de "Antecipação do Título junto ao Banco" ou "Venda do Título
  junto a Factoring" ver as alterações feitas na v14
  <https://www.odoo.com/pt_BR/forum/ajuda-1/v14-change-in-payment-behavior-how-do-the-suspense-and-outstanding-payment-accounts-change-the-journal-entries-posted-177592>
  .
- CNAB de Pagamento, verificar a integração com o PR
  <https://github.com/OCA/l10n-brazil/pull/972> e a possibilidade de
  multiplos modos de pagamento na mesma Ordem de Pagamento
  <https://github.com/odoo-brazil/l10n-brazil/pull/112>
- Verificar a possibilidade na v14 de remoção do ondele='restrict' no
  campo "move_line_id" e o campo "related" "ml_maturity_date" do
  account.payment.line no modulo dependente
  <https://github.com/OCA/bank-payment/blob/14.0/account_payment_order/models/account_payment_line.py#L39>
  para permitir o processo de Cancelamento de uma Fatura quando existe
  uma Ordem de Pagamento já confirmada/gerada/enviada( detalhes
  l10n_br_account_payment_order/models/account_payment_line.py#L130 )
- Funcionalidade de Agrupar Por/Group By não funciona em campos do tipo
  Many2Many, aparentemente isso foi resolvido na v15(verfificar na
  migração), isso é usado nos objetos referentes aos Codigos CNAB de
  Instrução e Retorno.
- Confirmar se existem Bancos que usam os mesmos conjuntos de Codigos
  CNAB de Instrução e Retorno para caso não existir remover o many2many
  do Banco e deixar apenas o many2one.
- Na migração remover o objeto bank.payment.line, que está vazio, porém
  é necessário para evitar erro na atualização do modulo ver detalhes em
  l10n_br_account_payment_order/models/account_payment_line.py:291 e
  referencia do problema <https://github.com/odoo/odoo/issues/44767> .
- Verificar a possibilidade de usar o objeto account.payment no caso
  CNAB e o modulo
  <https://github.com/OCA/bank-payment/tree/14.0/account_payment_order_return>
  para tratar o LOG de Retorno do CNAB, RFC
  <https://github.com/OCA/l10n-brazil/issues/2272> .
