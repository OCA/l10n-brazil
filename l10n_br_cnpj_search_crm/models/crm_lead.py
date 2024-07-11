# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Lead(models.Model):
    """CRM Lead Case"""

    _name = "crm.lead"
    _inherit = [_name, "l10n_br_base.party.mixin", "format.address.mixin"]

    cnpj = fields.Char(string="CNPJ", related="partner_id.cnpj_cpf")

    company_type = fields.Selection(
        string="Company Type",
        selection=[("person", "Individual"), ("company", "Company")],
        default="company",
    )
