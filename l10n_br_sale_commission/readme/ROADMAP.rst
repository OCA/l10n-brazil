* Adicionar testes de geração de NFS-e para pagamento de comissões
* Verificar erro ao retornar os campos padrões/default diferenças entre usar o search e o browse:
      l10n_br_fiscal.document.type(39,)
      l10n_br_fiscal.document.type('39',)
  No caso do browse com aspas '39' retorna erro na tela ao abrir o wizard:
      Database fetch misses ids (('39',)) and has extra ids ((39,)),
      may be caused by a type incoherence in a previous request
  Testar na migração.
