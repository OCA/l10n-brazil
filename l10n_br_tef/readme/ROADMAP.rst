- Fluxos pendentes

  - Cancelamento de pagamento
      - Fluxo para cancelar um pagamento já realizado pelo TEF
      - Adaptar a tela de lista de pedidos do módulo 'pos_order_mgmt' para ser possível acessar o fluxo de cancelamento
      - O botão e a função assim como os popups auxiliares  para tal funcionalidade já existem no l10n_br_tef, porém a tela em que eles se encontram não foi migrada

  - Pagamento parcelado
      - Verificar se é possível fazer um pagamento parcelado pelo POS
      - Já existem as funções que lidam com esse fluxo no módulo, mas com o POS atual não é possível atingi-las
  - Abortar operação
      - Ao abortar um fluxo de pagamento (“Operação cancelada pelo cliente”) o pinpad fica travado na tela “Operação Cancelada”. É preciso verificar qual a última mensagem deve ser enviada para o TEF para que o fluxo seja abortado por completo.

