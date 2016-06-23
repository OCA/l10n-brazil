.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

================================================
Ponto de Venda adaptado a Localização Brasileira
================================================

* Adapta o ponto de venda a legislação Brasileira;
* Serve de base para os modulos de nfce e sat;

TODO:
=====
* Add Fields:
    - number;
    - district;
    - l10n_br_city;
    - res.country;
* Solicitar o cnpj/cpf;
  - Colocar o campo de cpf na tela
  - Tentar linkar o cpf na venda a um cliente ja cadastrado
  - Pos.config adicionar cliente ao banco de dados ao inserir o cpf novo*
  - Pop-up solicitando o cpf ao inicar uma nova venda
* Payment.Mode;(oca/pos)
* Data e hora;
* Save response of sat and nfc-e in pos.order
* Armazenar a chave do documento fiscal;
* Cancelamento;
* Devolução;

Instalação
==========

Para instalar este modulo é preciso instalar:

* point_of_sale (Odoo addon)
* l10n_br_base

Configuração
============

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-brazil/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-brazil/issues/new?body=module:%20l10n_br_pos%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Licença
=======

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/agpl-3.0-standalone.html>.


Credits
=======

Contributors
------------

* Luis Felipe Miléo <mileo@kmee.com.br>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
