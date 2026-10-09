This module implements the management of the **FCI** (Ficha de Conteúdo de
Importação) required by the [Convênio ICMS
38/2013](https://www.confaz.fazenda.gov.br/legislacao/convenios/2013/CV038_13)
and by the [Ato COTEPE ICMS
61/2012](https://www.confaz.fazenda.gov.br/legislacao/atos/2012/ac061_12).

Taxpayers which industrialize imported goods must inform the share of the
imported parcel in the total of the resulting goods (Import Content) to the
tax administration of the state of origin, through a digital file. For each
goods of the transmitted file the tax administration generates a FCI control
number, which must be written in the field `nFCI` of the NF-e of the
interstate operations with that goods.

The module provides:

- the *FCI* record (`l10n_br_fiscal.fci.header`), holding the data of one
  digital file, and its goods (`l10n_br_fiscal.fci.line`), the register 5020
  of the layout;
- the generation of the TXT file in the layout of the Ato COTEPE ICMS
  61/2012, ready to be validated and transmitted with the SEFAZ
  Validador/Transmissor;
- the computation of the Import Content with the rounding rule required by
  the layout;
- a wizard to read the return file downloaded from the FCI web system, which
  fills in the FCI control number of each goods;
- the FCI control number of the last FCI of each product, in the *Fiscal*
  tab of the product.
