# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Invoice on Timesheets',
    'category': 'Sales Management',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.0.0.0',
    'depends': [
        'l10n_br_account',
        'account_analytic_analysis',
    ],
    'data': [
    ],
    'test': [
        'test/test_hr_timesheet_invoice.yml',
        'test/test_hr_timesheet_invoice_no_prod_tax.yml',
        'test/hr_timesheet_invoice_report.yml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
