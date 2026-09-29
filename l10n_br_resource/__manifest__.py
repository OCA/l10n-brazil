# Copyright 2016 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Resource",
    "summary": "Brazilian calendar and tools to compute dates used in "
    "financial and payroll modules",
    "version": "20.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_base", "resource"],
    "maintainers": ["mileo"],
    "external_dependencies": {"python": ["workalendar"]},
    "data": [
        "security/ir.access.csv",
        "views/resource_calendar_view.xml",
        "views/resource_calendar_leaves_view.xml",
        "views/resource_calendar_menu.xml",
        "wizards/workalendar_holiday_import_views.xml",
    ],
}
