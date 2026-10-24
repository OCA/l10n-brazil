# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from ..constants import (
    MIT_MONETARY_VARIATION,
    MIT_PIS_COFINS_REGIME,
    MIT_PJ_QUALIFICATION,
    MIT_PROFIT_TAXATION,
)


class ResCompany(models.Model):
    """The initial data of the MIT barely changes from one month to the next.

    Keeping it on the company means a monthly assessment starts filled in, and
    the accountant only touches what actually changed.
    """

    _inherit = "res.company"

    dctfweb_pj_qualification = fields.Selection(
        selection=MIT_PJ_QUALIFICATION,
        string="MIT legal entity qualification",
    )
    dctfweb_profit_taxation = fields.Selection(
        selection=MIT_PROFIT_TAXATION,
        string="MIT profit taxation",
    )
    dctfweb_monetary_variation = fields.Selection(
        selection=MIT_MONETARY_VARIATION,
        string="MIT monetary variation criterion",
    )
    dctfweb_pis_cofins_regime = fields.Selection(
        selection=MIT_PIS_COFINS_REGIME,
        string="MIT PIS/COFINS regime",
    )
    dctfweb_responsible_cpf = fields.Char(
        size=11,
        string="MIT responsible CPF",
    )
    dctfweb_responsible_phone_area = fields.Char(
        size=2,
        string="MIT responsible phone area code",
    )
    dctfweb_responsible_phone = fields.Char(
        size=9,
        string="MIT responsible phone",
    )
    dctfweb_responsible_email = fields.Char(
        size=60,
        string="MIT responsible e-mail",
    )
    dctfweb_crc_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="MIT CRC state",
        domain="[('country_id.code', '=', 'BR')]",
    )
    dctfweb_crc_number = fields.Char(
        size=11,
        string="MIT CRC number",
    )
