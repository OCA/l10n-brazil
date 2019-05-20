# Copyright (C) 2015 KMEE (http://www.kmee.com.br)
# @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Address from Brazilian Localization ZIP by Correios',
    'summary': 'Address from Brazilian Localization ZIP by Correios',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'KMEE, '
              'Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '12.0.1.0.0',
    'depends': [
        'l10n_br_zip',
    ],
    'installable': True,
    'external_dependencies': {
        'python': ['zeep'],
    }
}
