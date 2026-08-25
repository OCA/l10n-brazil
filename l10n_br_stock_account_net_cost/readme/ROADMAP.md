- A cascata de Operação Fiscal padrão do picking
  (`_get_default_fiscal_operation`) só é acionada pelo `onchange` de
  `invoice_state`. Pickings criados programaticamente (importação de NF-e, API,
  ajustes) não recebem operação fiscal e portanto continuam valorizados pelo
  bruto na entrada - o custo só é corrigido na fatura.
- Sem testes automatizados.
