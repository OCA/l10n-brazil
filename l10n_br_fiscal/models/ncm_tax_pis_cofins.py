# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


# pylint: disable=consider-merging-classes-inherited
class NCM(models.Model):
    _inherit = "l10n_br_fiscal.ncm"

    piscofins_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax.pis.cofins",
        relation="fiscal_pis_cofins_ncm_rel",
        column1="ncm_id",
        column2="piscofins_id",
        readonly=True,
        string="PIS/COFINS",
    )
