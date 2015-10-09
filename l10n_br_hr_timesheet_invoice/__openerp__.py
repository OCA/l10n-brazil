# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Brazilian Invoice on Timesheets',
    'version': '8.0',
    'category': 'Sales Management',
    'description': """
Generate your Invoices from Expenses, Timesheet Entries.
========================================================

Module to generate invoices based on costs (human resources, expenses, ...).

With Brazilian Taxes

You can define price lists in analytic account, make some theoretical revenue
reports.""",
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'depends': [
        'l10n_br_account',
        'hr_timesheet_invoice',
    ],
    'data': [
        'hr_timesheet_invoice_data.xml',
        'hr_timesheet_invoice_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
