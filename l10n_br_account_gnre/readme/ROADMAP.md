O gatilho lê as linhas fiscais, e não as linhas de imposto contábeis. Isso é
deliberado: o DIFAL não gera `account.move.line` com `tax_line_id` próprio, e um
gatilho sobre as linhas de imposto simplesmente não o veria. O DIFAL vem do
`icms_destination_value` e o FCP de destino do `icmsfcp_value`, os mesmos campos
que a NF-e leva em `vICMSUFDest` e `vFCPUFDest`.

A conciliação da baixa depende do parceiro, porque o plano de contas tem uma
única conta de ICMS ST a recolher, sem segregação por UF. Quem precisar separar
por estado pode usar a conta a pagar da regra por UF.

Integração com a ordem de pagamento, para mandar a guia ao lote sem digitação:

- a conta a pagar já leva a referência de pagamento (o nome da guia), que a
  ordem de pagamento exige para confirmar a linha;
- falta um módulo de ligação com o `l10n_br_account_payment_order`: modo de
  pagamento na regra por UF (CNAB 240 com a forma de pagamento 91, GNRE e
  tributos com código de barras, segmento O, do `l10n_br_cnab_structure`), o
  código de barras da guia levado à linha de pagamento pelo
  `_prepare_payment_line_vals` quando o portal processa a guia e, opcionalmente,
  a conta a pagar incluída na ordem rascunho do modo;
- a data limite de pagamento da guia hoje é texto e precisa virar data para
  corrigir o vencimento do título.
