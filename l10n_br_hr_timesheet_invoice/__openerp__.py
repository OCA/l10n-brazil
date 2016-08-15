# -*- coding: utf-8 -*-
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Invoice on Timesheets',
    'version': '1.0',
    'category': 'Sales Management',
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'depends': ['l10n_br_account',
                'hr_timesheet_invoice',
                ],
    'data': [
        'hr_timesheet_invoice_data.xml',
        'hr_timesheet_invoice_view.xml',
    ],
    'installable': False,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
