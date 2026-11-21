- **Validação do NIRE no Odoo.** O NIRE da empresa vai para o termo de
  abertura (I030) e liga o indicador do 0000, mas só o validador da Receita
  confere o dígito e a UF (regras REGRA_VALIDA_NIRE e REGRA_NIRE_UF). Falta a
  mesma conferência no cadastro da empresa.
- **Aglutinação com grupos que têm contas e subgrupos.** O balanço e a DRE são
  aglutinados pelos grupos do plano: o grupo que só reúne contas é a linha de
  detalhe e os grupos acima são os totais. A conta lançada diretamente num
  grupo que também tem subgrupos sai como linha de detalhe própria, e um grupo
  com contas do ativo e do passivo ao mesmo tempo não é separado. A DRE sai sob
  uma linha do resultado líquido do exercício.
- **Demonstrações intermediárias e período anterior.** Sai uma demonstração
  (J005) para o período da escrituração. Faltam as demonstrações de períodos
  intermediários, o valor do período anterior na DRE (VL_CTA_INI_ do J150), as
  notas explicativas e as demais demonstrações (J210, DLPA e DMPL).
- **Recuperação da ECD anterior.** O validador avisa quando a escrituração do
  ano anterior não foi recuperada; isso se faz no próprio programa da Receita.
- **Livros e registros não gerados.** Livros auxiliares (I012), centros de custo
  (I100), subcontas correlatas (I053), escrituração de SCP e balancetes diários
  (I300) seguem preenchíveis pela interface ou por importação.
