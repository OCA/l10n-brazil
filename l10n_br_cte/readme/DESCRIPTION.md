Este módulo permite a emissão de CT-e (Conhecimento de Transporte).

Mais especificamente ele:  
- mapea os campos de CT-e do módulo `l10n_br_cte_spec` com os campos
  Odoo.
- usa a logica do módulo `spec_driven_model` para realizar esse
  mapeamento de forma dinâmica, em especial ele usa o sistema de modelos
  com várias camadas, ou `StackedModel`, com os modelos
  `l10n_br_fiscal.document` e `l10n_br_fiscal.document.related` que tem
  varios niveis hierarquicos de elementos XML que estão sendo
  denormalizados dentro desses modelos Odoo 
- tem wizards para implementar a comunicação SOAP de CT-e com a SEFAZ
  (Autorização, Cancelamento, Encerramento...)
