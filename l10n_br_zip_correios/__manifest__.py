# -*- coding: utf-8 -*-
# Copyright (C) 2015 KMEE (http://www.kmee.com.br)
# @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Address from Brazilian Localization ZIP by Correios',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'version': '10.0.1.0.0',
    'website': 'http://odoo-brasil.org',
    'depends': [
        'l10n_br_zip',
    ],
    'category': 'Localization',
    'installable': True,
    'external_dependencies': {
        'python': ['zeep'],
    }
}
