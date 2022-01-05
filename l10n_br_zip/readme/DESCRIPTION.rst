Permite consultar o endereço através do CEP e preencher o campos do endereço com as informações consultadas, esse módulo também permite utilizar os seguintes serviços para consulta de CEP:

* [API CEP](https://apicep.com/api-de-consulta/)
* [Via CEP](https://viacep.com.br/)
* [Correios](http://www.buscacep.correios.com.br/sistemas/buscacep/buscaCepEndereco.cfm)

Para otimizar as buscas este módulo salva o resultado das consultas de cep na tabela l10n_br_zip, por padrão a cada 365 dias o registro de cep na tabela é atualizado em uma nova consulta de cep nos cadastros do Odoo.
