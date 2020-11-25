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
addon | version | summary
--- | --- | ---
[l10n_br_account](l10n_br_account/) | 12.0.2.1.1 | Brazilian Localization Account
[l10n_br_account_payment_order](l10n_br_account_payment_order/) | 12.0.1.0.0 | Brazilian Payment Order
[l10n_br_base](l10n_br_base/) | 12.0.1.0.1 | Customization of base module for implementations in Brazil.
[l10n_br_coa](l10n_br_coa/) | 12.0.2.1.0 | Base Brasilian Localization for the Chart of Accounts
[l10n_br_coa_generic](l10n_br_coa_generic/) | 12.0.2.1.0 | Plano de Contas para empresas do Regime normal (Micro e pequenas empresas)
[l10n_br_coa_simple](l10n_br_coa_simple/) | 12.0.2.1.0 | Brazilian Simple Chart of Account
[l10n_br_crm](l10n_br_crm/) | 12.0.1.0.0 | Brazilian Localization CRM
[l10n_br_currency_rate_update](l10n_br_currency_rate_update/) | 12.0.1.0.0 | Update exchange rates using OCA modules for Brazil
[l10n_br_fiscal](l10n_br_fiscal/) | 12.0.5.2.0 | Brazilian fiscal core module.
[l10n_br_hr](l10n_br_hr/) | 12.0.1.0.0 | Brazilian Localization HR
[l10n_br_hr_contract](l10n_br_hr_contract/) | 12.0.1.0.0 | Brazilian Localization HR Contract
[l10n_br_mis_report](l10n_br_mis_report/) | 12.0.1.1.0 | Templates de relatórios contábeis brasileiros: Balanço Patrimonial e DRE
[l10n_br_nfse](l10n_br_nfse/) | 12.0.1.5.0 | NFS-e
[l10n_br_nfse_ginfes](l10n_br_nfse_ginfes/) | 12.0.1.1.0 | NFS-e (Ginfes)
[l10n_br_portal](l10n_br_portal/) | 12.0.1.0.0 | Campos Brasileiros no Portal
[l10n_br_resource](l10n_br_resource/) | 12.0.1.0.0 | This module extend core resource to create important brazilian informations. Define a Brazilian calendar and some tools to compute dates used in financial and payroll modules
[l10n_br_sale](l10n_br_sale/) | 12.0.1.0.1 | Brazilian Localization Sale
[l10n_br_stock](l10n_br_stock/) | 12.0.1.0.0 | Brazilian Localization Warehouse
[l10n_br_stock_account](l10n_br_stock_account/) | 12.0.1.1.0 | Brazilian Localization WMS Accounting
[l10n_br_website_sale](l10n_br_website_sale/) | 12.0.1.0.1 | Website sale localização brasileira.
[l10n_br_zip](l10n_br_zip/) | 12.0.2.0.0 | Brazilian Localisation ZIP Codes
[payment_cielo](payment_cielo/) | 12.0.3.2.0 | Payment Acquirer: Cielo Implementation


Unported addons
---------------
addon | version | summary
--- | --- | ---
[l10n_br_nfe](l10n_br_nfe/) | 12.0.1.0.0 (unported) | Brazilian Eletronic Invoice NF-e .

[//]: # (end addons)
