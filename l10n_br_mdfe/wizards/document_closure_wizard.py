# Copyright 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models


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

    related_city_ids = fields.Many2many(
        comodel_name="res.city",
        compute="_compute_related_cities",
        string="Cities from Related Documents",
    )

    closure_city_id = fields.Many2one(
        string="City from Related Documents",
        comodel_name="res.city",
        domain="[('id', 'in', related_city_ids)]",
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

    @api.depends(
        "document_id",
        "document_id.mdfe_document_ids",
        "document_id.mdfe_document_ids.partner_id.city_id",
    )
    def _compute_related_cities(self):
        for wizard in self:
            cities = wizard.document_id.mdfe_document_ids.partner_id.mapped("city_id")
            wizard.related_city_ids = [Command.set(cities.ids)]

    @api.onchange("closure_city_id")
    def _onchange_closure_city_id(self):
        city = self.closure_city_id
        if city:
            self.state_id = city.state_id
            self.city_id = city

    @api.onchange("city_id")
    def _onchange_city_id(self):
        if self.city_id and self.city_id not in self.related_city_ids:
            return {
                "warning": {
                    "title": _("Confirmação"),
                    "message": _(
                        "Deseja selecionar uma cidade diferente da listada nos "
                        "documentos relacionados?"
                    ),
                }
            }

    def doit(self):
        for wizard in self:
            if wizard.document_id:
                wizard.document_id.closure_state_id = wizard.state_id
                wizard.document_id.closure_city_id = wizard.city_id
                wizard.document_id._document_closure()
        self._close()
