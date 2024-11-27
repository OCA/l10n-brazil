# Copyright 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DocumentClosurenWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.closure.wizard"
    _description = "Fiscal Document Closure Wizard"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
    )

    country_id = fields.Many2one(
        comodel_name="res.country",
        related="company_id.country_id",
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id', '=', country_id)]",
    )

    city_id = fields.Many2one(
        string="City",
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
    )

    def doit(self):
        for wizard in self:
            if wizard.document_id:
                wizard.document_id.closure_state_id = wizard.state_id
                wizard.document_id.closure_city_id = wizard.city_id
                wizard.document_id._document_closure()
        self._close()
