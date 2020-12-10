# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Pix',
    'summary': """
        PIX - The Instant Payment System (SPI) infrastructure for instant payments settlement between different payment service providers in Brazil.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil',
    'development_status': 'Alpha',
    "maintainers": ['mileo'],
    'depends': [
        'account'
    ],
    'data': [
        'security/l10n_br_pix_cob.xml',
        'views/l10n_br_pix_cob.xml',
        'security/l10n_br_pix_key.xml',
        'security/l10n_br_pix_config.xml',

        'views/l10n_br_pix_menu.xml',
        'views/l10n_br_pix_key.xml',
        'views/l10n_br_pix_config.xml',

        'views/account_journal.xml',
    ],
    'demo': [
        'demo/l10n_br_pix_config.xml',
        'demo/l10n_br_pix_key.xml',
        # 'demo/l10n_br_pix_cob.xml',
        # 'demo/account_journal.xml',
    ],
}
