# coding: utf-8
###############################################################################
#
#    Brazillian Human Resources Payroll module for OpenERP
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
###############################################################################

{
    'name': 'Brazilian Localization HR Payroll',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.0.0.1',
    'depends': [
        'l10n_br_hr_holiday',
        'l10n_br_resource',
        'l10n_br_hr_contract',
        'hr_payroll',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_br_hr_child_benefit_view.xml',
        'views/l10n_br_hr_income_tax_view.xml',
        'views/l10n_br_hr_income_tax_deductable_amount_family_view.xml',
        'views/l10n_br_hr_minimum_wage_view.xml',
        'views/l10n_br_hr_rat_fap_view.xml',
        'views/l10n_br_hr_social_security_tax_view.xml',
        'views/hr_payslip.xml',
    ],
    'installable': True,
    'auto_install': False,
}
