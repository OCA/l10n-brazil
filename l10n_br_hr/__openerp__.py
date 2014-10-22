# -*- encoding: utf-8 -*-
##############################################################################
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
##############################################################################

{
    'name' : 'Brazilian Localization HR',
    'description' : """
Brazilian Localization HR with informations refered to the national context of HR""",
    'category' : 'Localization',
    'author' : 'KMEE',
    'maintainer': 'KMEE',
    'website' : 'http://www.kmee.com.br',
    'version' : '0.1',
    'depends' : ['hr','l10n_br_base'],
    'data': [
             'data/l10n_br_hr.cbo.csv',
             'security/ir.model.access.csv',
             'view/l10n_br_hr_cbo_view.xml',
             'view/hr_employee_view.xml',
             'view/hr_job_view.xml',
             ],
    'test': [],
    'installable': True,
    'images': [],
    'auto_install': False,
    'license': 'AGPL-3',
}
