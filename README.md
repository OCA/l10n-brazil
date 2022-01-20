Core da localização Brasileira do Odoo (novo OpenERP)
=====================================================

[![Build Status](https://travis-ci.org/OCA/l10n-brazil.svg?branch=12.0)](https://travis-ci.org/OCA/l10n-brazil)
[![Coverage Status](https://coveralls.io/repos/OCA/l10n-brazil/badge.png?branch=12.0)](https://coveralls.io/r/OCA/l10n-brazil?branch=8.0)


Escopo desse repo
-----------------

Este projeto contêm os principais módulos da localização brasileira do Odoo, estes módulos são a base dos recursos:

* Fiscais
* Contábil
* Sped

Sobre
-----

Como a grande maioria dos módulos da OCA, esse projeto é open source sob licença [AGPL v3](http://www.gnu.org/licenses/agpl-3.0.html).
A licença AGPL é derivada da licença GPL e acrescenta para os usuários a garantia de poder baixar o codigo desse projeto assim como dos módulos de extenções, mesmo quando o accesso a oferecido na nuvem. Vale a pena lembrar que a Odoo SA mudou da licença do core do OpenERP de GPL para AGPL durante 2009 e mudou de novo a licença do core para LGPL em 2015 enquanto maioria do ecosistema de modulos eram feitos sob licença AGPL e não poderiam mudar de licença mais devido à diversidade das contribuições.

Esse projeto [segue se aperfeiçoando desde o início de 2009](https://github.com/openerpbrasil/l10n_br_core/network). O código era [inicialmente desenvolvido no Launchpad](https://code.launchpad.net/openerp.pt-br-localiz). Esse projeto é gerenciado pela fundação [OCA](https://odoo-community.org/) com a liderança do projeto:

* steering committee [Renato Lima](https://github.com/renatonlima) [AKRETION](http://www.akretion.com.br)
* core OCA reviewer [Raphaël Valyi](https://github.com/rvalyi) [AKRETION](http://www.akretion.com.br)

Esse projeto foi iniciado e principalmente desenvolvido pela AKRETION mas conta hoje com os outros contribuidores importantes:

* [Luis Mileo](https://github.com/mileo) [KMEE](http://kmee.com.br)
* [Danimar Ribeiro](https://github.com/danimaribeiro) [TRUSTCODE](http://trustcode.com.br/)
* Fabio Negrini e [varios outros contribuidores](https://github.com/OCA/l10n-brazil/graphs/contributors).


Contexto e extensões significativas desse projeto
-------------------------------------------------

![estrutura do projeto](https://raw.githubusercontent.com/akretion/l10n-brazil-assets/master/l10n-brazil.png)


* [odoo-brazil-eletronic-documents](https://github.com/odoo-brazil/odoo-brazil-eletronic-documents): os módulos do l10n-brazil definem a estrutura de dados das NFe's, porém a transmissão (exportação e importação) é plugável com tecnologias específicas. Hoje a forma mais madura de transmitir as NFe's é com a biblioteca pysped atraves do projeto odoo-brazil-eletronic-documents.
* [odoo-brazil-banking](https://github.com/odoo-brazil/odoo-brazil-banking): a transmissão de boletos, CNAB e a importacão de extratos bancários usando os projetos OCA l10n-brazil e bank-statement-import.
* [odoo-brazil-sped](https://github.com/odoo-brazil/odoo-brazil-sped): o projeto visando a implementar o SPED no Odoo.

Esses projetos ja estão sendo desenvolvidos de forma colaborativa com processos semelhantes aos da OCA (menos burocráticos e mais ágeis porem). A medida que eles amadurescem é provavel que eles ou parte deles integram a OCA tambem.

Esse projeto l10-brazil tambem depende do projeto [account-fiscal-rules](https://github.com/OCA/account-fiscal-rule) que foi extraido do l10n-brazil desde 2012 e integrado na OCA e esta hoje utilizado por outras localizões.

Fora do escopo desse repo
-------------------------

* Extender ou modificar as funcionalidades do Odoo não vinculadas à localização brasileira. Outros módulos em outros projetos são perfeitos para isso.
* De uma forma geral, reimplementar aqui o que ferramentas terceiras já fazem bem.
* Quando há uma quantidade razoável de soluções técnicas para resolver um problema, o projeto do core da localização não quer impor uma dependência importante. Outros módulos e projetos são bem-vindos nesse caso. Esse projeto é por exemplo agnostico de tecnologia de transmissão das notas fiscais.
* Implementar o PAF-ECF no PDV web do Odoo. Se trata de um trabalho muito burocrático que iria requerer modificar muito o PDV do Odoo, enquanto se conectar com PDV’s do mercado é uma alternativa razoável.
* Manter dados para a folha de pagamento legal no Brasil.
* Ter a responsabilidade de manter dados fiscais em geral. Em geral esse tipo de serviço requer uma responsabilidade jurídica que se negocia caso a caso.

Aviso importante
----------------

Apesar do código ser livremente disponível para baixar, implementar o Odoo de forma sustentável nao é algo fácil (a menos que seja apenas gestao de projeto ou CRM). E muito comum ver empresas achando que sabe mas que acaba desistindo a medida que descobre a dificuldade quando já é tarde demais. Um fator importante de dificuldade é a velocidade de evolução do core feito pela Odoo SA que nem sempre acontece de forma conectada com a comunidade. Isso obriga quem pretende implementar a trabalhar com branches em evolução em vez de pacotes estáveis por varios anos como em alguns outros projetos open source mais maduros. Por isso, é melhor você trabalhar com profisionais altamente especializados nisso (o aprendizado leva anos). O Odoo não foi projetado para o Brasil inicialmente, apenas tornamos isso possível com todo esses modulos. O Odoo pode também não ser tão maduro quanto se pretende. Isso não quer dizer que não serve. Serve sim, mas não para qualquer empresa e deve se observar muitos cuidados. Por fim, muitas vezes o valor aggregado vem mais da possibilidade de ter customizações do que das funcionalidades padrões; apesar de elas estarem sempre melhorando.

Contribuindo com o código
-------------------------

Você pode resolver umas das issues cadastradas no Github ou implementar melhorias em geral, nos enviando um pull request com as suas alterações.
Deve hoje se seguir os fluxos de trabalho padrão da OCA: [https://odoo-community.org/page/Contribute](https://odoo-community.org/page/Contribute)
Se você for votado como core OCA reviewer pelos outros reviewers, você tera os direitos de commit no projeto. Você também pode ganhar esse direito só nesse projeto fazendo um esforço de contribuições no tempo comparável aos outros committers.

lista de discussão: [https://groups.google.com/forum/#!forum/openerp-brasil](https://groups.google.com/forum/#!forum/openerp-brasil)

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[l10n_br_account](l10n_br_account/) | 12.0.12.0.1 |  | Brazilian Localization Account
[l10n_br_account_bank_statement_import_cnab](l10n_br_account_bank_statement_import_cnab/) | 12.0.1.0.0 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) | Importação de Extrato Bancário CNAB 240 - Segmento E
[l10n_br_account_due_list](l10n_br_account_due_list/) | 12.0.2.0.0 |  | Brazilian Account Due List
[l10n_br_account_payment_brcobranca](l10n_br_account_payment_brcobranca/) | 12.0.3.1.0 |  | L10n Br Account Payment BRCobranca
[l10n_br_account_payment_order](l10n_br_account_payment_order/) | 12.0.7.0.0 |  | Brazilian Payment Order
[l10n_br_base](l10n_br_base/) | 12.0.4.0.1 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | Customization of base module for implementations in Brazil.
[l10n_br_coa](l10n_br_coa/) | 12.0.4.0.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) | Base do Planos de Contas brasileiros
[l10n_br_coa_complete](l10n_br_coa_complete/) | 12.0.2.0.0 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Plano de Contas Completo para empresas Simples, Presumido, Real, SA, Consolidação
[l10n_br_coa_generic](l10n_br_coa_generic/) | 12.0.5.0.0 |  | Plano de Contas para empresas do Regime normal (Micro e pequenas empresas)
[l10n_br_coa_simple](l10n_br_coa_simple/) | 12.0.3.0.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Plano de Contas ITG 1000 para Microempresas e Empresa de Pequeno Porte
[l10n_br_contract](l10n_br_contract/) | 12.0.5.0.0 |  | Customization of Contract module for implementations in Brazil.
[l10n_br_crm](l10n_br_crm/) | 12.0.1.0.1 |  | Brazilian Localization CRM
[l10n_br_currency_rate_update](l10n_br_currency_rate_update/) | 12.0.2.0.0 |  | Update exchange rates using OCA modules for Brazil
[l10n_br_delivery](l10n_br_delivery/) | 12.0.3.0.0 |  | This module changes the delivery model strategy to match brazilian standards.
[l10n_br_delivery_nfe](l10n_br_delivery_nfe/) | 12.0.1.0.0 |  | Brazilian Localization Delivery NFe
[l10n_br_fiscal](l10n_br_fiscal/) | 12.0.21.1.1 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Brazilian fiscal core module.
[l10n_br_hr](l10n_br_hr/) | 12.0.1.0.0 |  | Brazilian Localization HR
[l10n_br_hr_contract](l10n_br_hr_contract/) | 12.0.1.1.0 |  | Brazilian Localization HR Contract
[l10n_br_mis_report](l10n_br_mis_report/) | 12.0.1.3.0 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) | Templates de relatórios contábeis brasileiros: Balanço Patrimonial e DRE
[l10n_br_nfe](l10n_br_nfe/) | 12.0.4.0.1 |  | Brazilian Eletronic Invoice NF-e .
[l10n_br_nfe_spec](l10n_br_nfe_spec/) | 12.0.3.0.0 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | nfe spec
[l10n_br_nfse](l10n_br_nfse/) | 12.0.5.5.0 | [![gabrielcardoso21](https://github.com/gabrielcardoso21.png?size=30px)](https://github.com/gabrielcardoso21) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) | NFS-e
[l10n_br_nfse_ginfes](l10n_br_nfse_ginfes/) | 12.0.3.0.0 | [![gabrielcardoso21](https://github.com/gabrielcardoso21.png?size=30px)](https://github.com/gabrielcardoso21) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) | NFS-e (Ginfes)
[l10n_br_nfse_issnet](l10n_br_nfse_issnet/) | 12.0.3.1.0 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | NFS-e (ISSNet)
[l10n_br_nfse_paulistana](l10n_br_nfse_paulistana/) | 12.0.1.1.0 | [![gabrielcardoso21](https://github.com/gabrielcardoso21.png?size=30px)](https://github.com/gabrielcardoso21) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) | NFS-e (Nota Paulistana)
[l10n_br_portal](l10n_br_portal/) | 12.0.1.2.0 |  | Campos Brasileiros no Portal
[l10n_br_product_contract](l10n_br_product_contract/) | 12.0.1.0.0 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Criação de contratos através dos Pedidos de Vendas
[l10n_br_purchase](l10n_br_purchase/) | 12.0.4.4.0 |  | Brazilian Localization Purchase
[l10n_br_purchase_stock](l10n_br_purchase_stock/) | 12.0.2.1.0 |  | Brazilian Localization Purchase Stock
[l10n_br_repair](l10n_br_repair/) | 12.0.8.0.0 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Brazilian Localization Repair
[l10n_br_resource](l10n_br_resource/) | 12.0.1.1.0 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![hendixcosta](https://github.com/hendixcosta.png?size=30px)](https://github.com/hendixcosta) [![lfdivino](https://github.com/lfdivino.png?size=30px)](https://github.com/lfdivino) | This module extend core resource to create important brazilian informations. Define a Brazilian calendar and some tools to compute dates used in financial and payroll modules
[l10n_br_sale](l10n_br_sale/) | 12.0.6.1.1 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Brazilian Localization Sale
[l10n_br_sale_stock](l10n_br_sale_stock/) | 12.0.5.4.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | Brazilian Localization Sales and Warehouse
[l10n_br_stock](l10n_br_stock/) | 12.0.1.0.0 |  | Brazilian Localization Warehouse
[l10n_br_stock_account](l10n_br_stock_account/) | 12.0.4.0.0 |  | Brazilian Localization WMS Accounting
[l10n_br_website_sale](l10n_br_website_sale/) | 12.0.1.2.0 |  | Website sale localização brasileira.
[l10n_br_website_sale_delivery](l10n_br_website_sale_delivery/) | 12.0.2.1.0 | [![DiegoParadeda](https://github.com/DiegoParadeda.png?size=30px)](https://github.com/DiegoParadeda) | Implements Brazilian freight values for delivery.
[l10n_br_zip](l10n_br_zip/) | 12.0.3.0.1 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Brazilian Localisation ZIP Codes
[payment_cielo](payment_cielo/) | 12.0.3.2.1 | [![DiegoParadeda](https://github.com/DiegoParadeda.png?size=30px)](https://github.com/DiegoParadeda) | Payment Acquirer: Cielo Implementation
[spec_driven_model](spec_driven_model/) | 12.0.1.2.0 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | Tools for specifications driven mixins (from xsd for instance)

[//]: # (end addons)
