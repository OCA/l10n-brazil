# Copyright (C) 2019 - Renato Lima Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def post_init_hook(cr, registry):
    """Import XML data to change core data"""
    from odoo.tools import convert_file
    files = [
        'data/fiscal.cnae.csv',
        'data/fiscal.cfop.csv',
        'data/fiscal.cst.csv',
        'data/fiscal.tax.csv',
        'data/fiscal.tax.ipi.guideline.csv',
        'data/fiscal.ncm.csv',
        'data/fiscal.cest.csv',
        'data/fiscal.nbs.csv',
        'data/fiscal.service.type.csv',
        'data/simplified_tax_data.xml',
    ]

    for file in files:
        convert_file(cr, 'fiscal', file, None, mode='init',
                    noupdate=True, kind='init', report=None)
