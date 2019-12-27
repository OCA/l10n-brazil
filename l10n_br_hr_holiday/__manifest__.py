# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Hr Holiday',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'hr_holidays',
        'l10n_br_resource',
    ],
    'data': [
        'data/hr_leave_type_data.xml',
        'security/hr_leave_type.xml',
        'security/hr_leave_rule.xml',
        'security/ir.model.access.csv',
        'views/hr_leave.xml',
        'views/hr_leave_type.xml',
        'views/calendar_event_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
