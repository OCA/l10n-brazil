Este módulo implementa a gestão da **FCI** (Ficha de Conteúdo de
Importação) exigida pelo [Convênio ICMS
38/2013](https://www.confaz.fazenda.gov.br/legislacao/convenios/2013/CV038_13)
e pelo [Ato COTEPE ICMS
61/2012](https://www.confaz.fazenda.gov.br/legislacao/atos/2012/ac061_12).

Os contribuintes que industrializam mercadorias importadas devem informar à
administração tributária do estado de origem, por meio de um arquivo
digital, a participação da parcela importada no total da mercadoria
resultante (Conteúdo de Importação). Para cada mercadoria do arquivo
transmitido a administração tributária gera um número de controle da FCI,
que deve ser informado no campo `nFCI` da NF-e das operações interestaduais
com essa mercadoria.

O módulo oferece:

- o registro da *FCI* (`l10n_br_fiscal.fci.file`), com os dados de um
  arquivo digital, e as suas mercadorias (`l10n_br_fiscal.fci`), o registro
  5020 do leiaute;
- a geração do arquivo TXT no leiaute do Ato COTEPE ICMS 61/2012, pronto
  para ser validado e transmitido com o Validador/Transmissor da SEFAZ;
- o cálculo do Conteúdo de Importação com a regra de arredondamento exigida
  pelo leiaute;
- um assistente para ler o arquivo de retorno baixado do sistema web da
  FCI, que preenche o número de controle da FCI de cada mercadoria;
- o número de controle da última FCI de cada produto, na aba *Fiscal* do
  produto.
