Este módulo permite a emissão de NF-e.

Mais especificamente ele:  
- mapea os campos de NF-e do módulo `l10n_br_nfe_spec` com os campos
  Odoo em especial os campos dos módulos `l10n_br_base` e
  `l10n_br_fiscal`
- usa a logica do módulo `spec_driven_model` para realizar esse
  mapeamento de forma dinâmica, em especial ele usa o sistema de modelos
  com várias camadas, ou `StackedModel`, com os modelos
  `l10n_br_fiscal.document`, `l10n_br_fiscal.document.line` e
  `l10n_br_fiscal.document.related` que tem varios niveis hierarquicos
  de elementos XML que estão sendo denormalizados dentro desses modelos
  Odoo 
- permite a exportação e importação de XML de NF-e
- tem wizards para implementar a comunicação SOAP de NF-e com a SEFAZ
  (Autorização, Cancelamento, Inutilização...)
- implementa a autorização, inutilização e contingência de documentos
  NFC-e

Módulos relacionados:  
- este módulo não depende do módulo `account` do Odoo. A integração com
  o financeiro do módulo `account` é realizada no módulo
  `l10n_br_account_nfe` (tags dup e pag em especial)
- existe também o módulo `l10n_br_delivery_nfe` que faz a integração do
  módulo `l10n_br_nfe` com o módulo `delivery` do Odoo (tags de
  transportadora e de frete em especial)

O módulo também imprime a **DANFE Simplificado - Etiqueta** de uma NF-e
autorizada: a DANFE simplificada em formato de etiqueta de envio (NT
2020.004; MOC 7.0 Anexo II, item 3.12), para colar no pacote entregue a
serviços de entrega como Correios ou JadLog. A etiqueta é renderizada
pela biblioteca
[BrazilFiscalReport](https://github.com/Engenere/BrazilFiscalReport),
por padrão no papel térmico usual de 100 x 150 mm.
