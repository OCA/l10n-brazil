As fases seguintes, na ordem em que dependem uma da outra:

1. **Códigos de receita.** A tabela `l10n_br_reinf.revenue.code` não tem dados:
   o mapeamento do Anexo I traz os 90 códigos que as naturezas usam, mas não a
   denominação oficial de cada um, e inventar descrição de código de DARF não
   serve. Falta a tabela oficial de códigos de receita para popular nome e
   vigência e transformar o `revenue_code` do mapeamento em `many2one`.

1. **R-1000: alteração e exclusão.** As pernas `alteracao` (com
   `novaValidade`) e `exclusao` do choice de `infoContri` ficaram fora, e com
   elas os grupos opcionais `softHouse` e `infoEFR`, que existem como campo mas
   não são populados a partir do Odoo.
2. **Transporte REST assíncrono.** Implementar `_transport_send()` e
   `_transport_query()` (recepção de lote e consulta por protocolo), o cron de
   polling e a trava anti-transmissão de produção em banco restaurado. Depende
   de assinatura **rsa-sha256**, que a `erpbrasil.assinatura` ainda não faz (só
   sha1).
3. **Dados de retenção por linha.** Natureza de rendimento e código de receita
   por linha fiscal, e as **duas datas** de cada origem: crédito/competência e
   liquidação. O fato gerador é por tributo: o IR pelo crédito quando anterior
   ao pagamento, o PCC pelo pagamento. Enquanto os campos não estiverem no
   `l10n_br_fiscal` e no `l10n_br_account_withholding`, eles moram aqui como
   `_inherit`, e migram quando os PRs de origem forem mesclados.
4. **Apuração por competência e tela de conferência.** Empresa x período, com
   unicidade, agregando estabelecimento x beneficiário x natureza, e a tela de
   conferência com divergências enumeradas, exceções com motivo, agregados
   armazenados, exportação e confronto com os totalizadores devolvidos pela
   Receita.
5. **R-4020** (pagamentos a PJ), em quatro tabelas (evento, `idePgto`,
   `infoPgto`, `infoProcRet`), com acumulação mensal por estabelecimento e
   beneficiário, o colapso do PCC agregado e o split quando estourar os limites
   do leiaute (100 `idePgto`, 999 `infoPgto`, 50 `infoProcRet`).
6. **R-4010** (aluguel de pessoa física, serviços de autônomos, dividendos),
   **R-2010** (retenção previdenciária de cessão de mão de obra), totalizadores
   **R-900x**, calendário da obrigação, fechamento e reabertura
   (**R-2099/R-4099**, e a série R-4000 reabre pelo próprio R-4099 com
   `fechRet` = 1), retificação e **R-9000**.

Limitações conhecidas desta fase:

- O colapso do agregado segue o parecer fiscal: a natureza autoriza pela coluna
  Tributo da Tabela 01, que também diz quais componentes o agregado carrega (a
  15001, cooperativas de trabalho, agrega sem CSLL, em 3,65%), e a parcialidade
  só mantém o agregado quando é da NATUREZA. Parcialidade por isenção ou
  alíquota zero do beneficiário (IN RFB 459/2004, art. 2) e por medida judicial
  (art. 10) vão nos códigos específicos. O que ainda **não** está implementado é
  o grupo `infoProcRet` do caso judicial, que depende do R-1070.

- **A tabela de códigos de receita com a denominação oficial não está no manual
  da EFD-Reinf.** O Anexo I é "natureza de rendimento x código de receita": dá o
  código, nunca o nome dele. A denominação vive na Tabela de Códigos de Receita
  da própria Receita Federal (SICALC / Agenda Tributária), que é outra fonte.
  Por isso `l10n_br_reinf.revenue.code` só traz o 595207, cujo nome vem do art.
  31 da Lei 10.833/2003.

- A Tabela 01 publicada **não lista a natureza 17547**, que a tabela do R-4020
  mapeia em 6 linhas. Ela é recuperada da própria tabela de mapeamento, que traz
  a descrição oficial numa coluna, e o script avisa quando isso acontece: é
  divergência da fonte, não do módulo.

- **Os campos `*_wh_value` da linha fiscal não podem ser preenchidos à mão.**
  Eles pertencem ao motor de imposto do `l10n_br_fiscal`, que os re-deriva de
  `fiscal_tax_ids` a cada escrita na linha: verificado em runtime escrevendo
  antes do post, depois do post e direto na `l10n_br_fiscal.document.line`, e
  nos três casos o banco fica com 0,00 (o cache ainda mostra o valor até a
  invalidação, o que engana). Por isso a apuração lê a retenção em duas fontes:
  os campos fiscais quando o documento foi precificado pelo motor, e as linhas
  de imposto postadas cujo grupo fiscal é de retenção em todo o resto. Na
  mesma linha, valor gravado em campo da linha fiscal de uma nota **sem
  operação fiscal** não sobrevive ao post, e é por isso que a natureza de
  rendimento se resolve em cascata (linha, tipo de serviço, parceiro) em vez de
  depender só do campo da linha.

- A tabela `l10n_br_reinf.revenue.code` só tem o código agregado 595207, que é o
  que o colapso precisa (é o único cujo nome tem lastro: art. 31 da Lei
  10.833/2003). Os outros 89 códigos que o Anexo I usa entram quando a
  tabela oficial de códigos de DARF estiver transcrita, com nome e vigência: o
  mapeamento das naturezas já traz o código, e é dele que a apuração lê.

- O rateio da retenção entre várias linhas de base é proporcional ao subtotal.
  A base declarada vem do `tax_base_amount` do imposto (correta com redução de
  base), mas quando **um mesmo imposto cobre linhas com reduções diferentes** a
  divisão entre elas fica aproximada.

- Exportação XLSX da conferência usa a exportação padrão de lista do Odoo. A
  planilha formatada depende do `report_xlsx` do reporting-engine.

- `infoProcRet` (retenção suspensa por decisão judicial) gera exceção e não o
  grupo no XML: depende do R-1070, que é da fase seguinte.

- A apuração cobre a série R-4000 de pessoa jurídica. IRPF e RRA não têm campo
  próprio na localização e entram com o R-4010.

- `classTrib` é `Char` de 2 posições na empresa, e não uma seleção com os
  valores oficiais da tabela de classificações do manual, que ainda não foi
  transcrita.

- Escrever CNPJ alfanumérico em empresa **já existente** falha no
  `l10n_br_base` (o inverso de `cnpj_cpf` passa pelo `erpbrasil.base`, que
  descarta as letras e valida o resto como CPF). Criar já funciona. Por isso os
  testes de banco leem a inscrição da empresa em vez de escrever uma
  alfanumérica, e o CNPJ alfanumérico é coberto nos testes unitários do
  identificador, que não precisam de banco.

- O envelope do lote assíncrono e a consulta de recibos não têm mixins no
  `l10n_br_reinf_spec` (são outra família de esquema, com versão própria) e vão
  ser montados diretamente com os bindings da `nfelib`.
- Os bindings da `nfelib` degradam o elemento `Signature` do evento para uma
  string simples, e ele é **obrigatório**: desserializar um evento sem
  assinatura levanta `TypeError`. A assinatura é aplicada sobre o XML
  serializado, e o teste de round-trip carrega um valor de marcação.
- O `nfelib.CommonMixin._get_schema_path()` não conhece o pacote `reinf`, então
  a validação contra XSD pela biblioteca ainda não funciona sem passar o caminho
  do esquema à mão.
- Natureza de rendimento e código de receita são únicos por código, como o CFOP
  e o NCM do `l10n_br_fiscal`: a vigência do `data.abstract` diz quando o código
  vale, e não versiona o conteúdo. Quando a alíquota ou a composição de um
  código mudar por lei (é o que acontece com o agregado de PIS/COFINS/CSLL na
  extinção dos dois tributos), o versionamento pede uma tabela filha com
  vigência, no mesmo desenho do `l10n_br_fiscal.tax.definition`, e não linhas
  repetidas com o mesmo código.

- Estabelecimento (`ideEstab`) é assumido igual à empresa. Multiestabelecimento
  (filial como `res.company` filha) é decisão em aberto.
