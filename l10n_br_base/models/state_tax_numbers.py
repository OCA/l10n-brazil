# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StateTaxNumbers(models.Model):
    _name = "state.tax.numbers"
    _description = "State Tax Numbers"

    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")

    inscr_est = fields.Char(string="State Tax Number", size=16, required=True)

    state_id = fields.Many2one(
        comodel_name="res.country.state", string="State", required=True
    )

    _sql_constraints = [
        (
            "l10n_br_base_state_tax_numbers_id_uniq",
            "unique (state_id, partner_id)",
            "The Partner already has a State Tax Number for that State!",
        )
    ]
