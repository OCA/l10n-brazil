# -*- coding: utf-8 -*-
#    Address from Brazilian Localization ZIP by Correios to Odoo
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Address from Brazilian Localization ZIP by Correios',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'version': '8.0.1.0.0',
    'website': 'http://odoo-brasil.org',
    'depends': [
        'l10n_br_zip',
    ],
    'test': [
        'test/company_zip.yml',
        'test/partner_zip.yml',
    ],
    'category': 'Localization',
    'installable': True,
    'external_dependencies': {
        'python': ['suds'],
    }
}
