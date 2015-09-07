Core da localização Brasileira do Odoo (novo OpenERP)
=====================================================
 
[![Build Status](https://travis-ci.org/OCA/l10n-brazil.svg?branch=8.0)](https://travis-ci.org/OCA/l10n-brazil)
[![Coverage Status](https://coveralls.io/repos/OCA/l10n-brazil/badge.png?branch=8.0)](https://coveralls.io/r/OCA/l10n-brazil?branch=8.0)
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/odoo-brazil/odoo-brazil?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=body_badge)
 
 
Goal
----
 
*This project contains the main modules for using Odoo in Brazil. These modules extend the main core addons as well as a few very important other OCA modules. However, this project doesn't depend on a specific electronic invoice transmission lib as the existing ones are far from OCA standards and we prefer delegate the transmission technology to other sub-projects.*
 
Este projeto contêm os principais módulos da localização brasileira do Odoo, estes módulos são a base dos recursos:
 
* Fiscais
* Contábil
* Sped
 
Sobre
-----
 
Este projeto é open source sob licença AGPL v3 http://www.gnu.org/licenses/agpl-3.0.html
Essa licença derivada da licença GPL accrescenta para os usuarios a garantia de poder baixar o codigo desse projeto assim como do codigo derivado, mesmo quando o accesso a oferecido na nuvem. Vale a pena lembrar que a Odoo SA mudou da licença do core do OpenERP de GPL para AGPL durante 2009 e mudou de novo a licença do core para LGPL em 2015 enquanto maioria do ecosistema de modulos eram feitos sobe licença AGPL e não poderiam mudar de licença mais devido à diversidade das contribuições.
 
Esse projeto [segue se aperfeiçoando desde o início de 2009](https://github.com/openerpbrasil/l10n_br_core/network). O código era [inicialmente desenvolvido no Launchpad](https://code.launchpad.net/openerp.pt-br-localiz). Esse projeto é gerenciado pela fundação [OCA](https://odoo-community.org/) com a liderança do projeto steering committee Renato Lima [AKRETION](http://www.akretion.com.br) e o core OCA reviewer Raphaël Valyi [AKRETION](http://www.akretion.com.br). Esse projeto foi iniciado e principalmente desenvolvido pela AKRETION mas conta com outros contribuidores como Luis Mileo [KMEE](http://kmee.com.br), Danimar Ribeiro, Fabio Negrini e varios outros [https://github.com/OCA/l10n-brazil/graphs/contributors](https://github.com/OCA/l10n-brazil/graphs/contributors).
 
Além de desenvolver as funcionalidades da localização, os profissionais por trás desse projeto interagem com o core do projeto Odoo para propor melhorias para que a localização se integre da forma mais suave possível dentre do ecosistema do Odoo. Assim, graças a esse projeto, dezenas de “merge proposals” já foram feitas e integradas no core do Odoo e uma dezena de modulos foi extraido em outras camadas mais genéricas da OCA.
 
Non goal
--------
 
* Extender ou modificar as funcionalidades do Odoo não vinculadas à localização brasileira. Outros módulos em outros projetos são perfeitos para isso.
* De uma forma geral, reimplementar aqui o que ferramentas terceiras já fazem bem.
* Quando há uma quantidade razoável de soluções técnicas para resolver um problema, o projeto do core da localização não quer impor uma dependência importante. Outros módulos e projetos são bem-vindos nesse caso. Esse projeto é por exemplo agnostico de tecnologia de transmissão de nota fiscal. Existe por exemplo um projeto de transmissão com a biblioteca open source PySPED aqui [https://github.com/odoo-brazil/odoo-brazil-eletronic-documents](https://github.com/odoo-brazil/odoo-brazil-eletronic-documents).
* Implementar o PAF-ECF no PDV web do Odoo. Se trata de um trabalho muito burocrático que iria requerer modificar muito o PDV do Odoo, enquanto se conectar com PDV’s do mercado é uma alternativa razoável.
* Manter dados para a folha de pagamento legal no Brasil.
* Ter a responsabilidade de manter dados fiscais em geral. Em geral esse tipo de serviço requer uma responsabilidade jurídica que se negocia caso a caso.
 
Aviso
-----
 
Apesar do código ser livramente disponível para baixar, implementar o Odoo de forma sustentável nao é algo facil (a menos que seja apenas gestao de projeto ou CRM). E muito comum ver empresas achando que sabe mas que acaba desistindo a medida que descobre a dificuldade quando já é tarde demais. E melhor você trabalhar com profisionais altamente especializados nisso (o aprendizado leva anos). O Odoo não foi projetado para o Brasil inicialmente, apenas tornamos isso possível com todo esses modulos. O Odoo pode também não ser tão maduro quanto se pretende. Isso não quer dizer que não serve. Serve sim, mas não para qualquer empresa e deve se observar muitos cuidados. Por fim, muitas vezes o valor aggregado vem mais da possibilidade de ter customizações do que das funcionalidades padrões; apesar de elas estar sempre melhorando.
 
Contribuindo com o código
-------------------------
 
Você pode resolver umas das issues cadastradas no Github ou implementar melhorias em geral, nos enviando um pull request com as suas alterações.
Deve hoje se seguir os fluxos de trabalho padrão da OCA: [http://www.slideshare.net/afayolle/contributing-to-the-odoo-community-association](http://www.slideshare.net/afayolle/contributing-to-the-odoo-community-association)
Se você for votado como core OCA reviewer pelos outros reviewers, você tera os direitos de commit no projeto. Você também pode ganhar esse direito só nesse projeto fazendo um esforço de contribuições no tempo comparável aos outros committers.
 
lista de discussão: [https://groups.google.com/forum/#!forum/openerp-brasil](https://groups.google.com/forum/#!forum/openerp-brasil)

