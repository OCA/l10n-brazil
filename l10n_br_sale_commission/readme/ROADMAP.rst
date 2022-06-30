* Verificar erro ao retornar os campos padrões/default diferenças entre usar o search e o browse:
      l10n_br_fiscal.document.type(39,)
      l10n_br_fiscal.document.type('39',)
  No caso do browse com aspas '39' retorna erro na tela ao abrir o wizard:
      Database fetch misses ids (('39',)) and has extra ids ((39,)),
      may be caused by a type incoherence in a previous request
  Testar na migração.
* Para resolver o problema de não gerar comissão quando o CFOP Não Gera Financeiro o ideal seria usar o objeto 'sale.commission.mixin' para assim não precisar repetir código nos objeto mas por alguma razão não funcionou.
