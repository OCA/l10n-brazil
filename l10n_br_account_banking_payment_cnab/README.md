.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
:alt: License: AGPL-3


Account Banking Brazillian - Payments Export Infrastructure
=============================================================

This module provide an infrastructure to export payment and debit orders in
Febraban layout.

Installation
============

This module depends on :
* account_banking_payment_export
* account_direct_debit

This modules is part of the odoo-brazil/odoo-brazil-banking suite.

Configuration
=============

    + In a multicompany environment, make sure the sequences payment line and payment order are with the company set to the one you'll use to export the payments and charges.
        If they are not set like this, you'll not be able to add payment lines with regular users.

Usage
=====

This module provides a menu to configure payment order types : Accounting > Configuration > Miscellaneous > Payment Export Types 

For further information, please visit:

 * https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

 * no known issues
 
Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/odoo-brazil/odoo-brazil-banking/issues>`_.  In case of trouble, please
check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/odoo-brazil/odoo-brazil-banking/issues/new?body=module
:%20l10n_br_account_banking_payment_cnab%0Aversion:%208
.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Luis Felipe Mileo <mileo@kmee.com.br>
* Fernando Marcato Rodrigues <fernando.marcato@kmee.com.br>
* Daniel Sadamo <daniel.sadamo@kmee.com.br>


Maintainer
----------

.. image:: https://brasil.odoo.com/logo.png
:alt: Odoo Brazil
   :target: http://brazil.odoo.com

This module is maintained by the Odoo Brazil.

the Odoo Brazil Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://brazil.odoo.com
