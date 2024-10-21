# Copyright (C) 2012  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class TaxEstimate(models.Model):
    _name = "l10n_br_fiscal.tax.estimate"
    _description = "Fiscal Tax Estimate"
    _order = "create_date desc"

    ncm_id = fields.Many2one(comodel_name="l10n_br_fiscal.ncm", string="NCM")

    nbs_id = fields.Many2one(comodel_name="l10n_br_fiscal.nbs", string="NBS")

    state_id = fields.Many2one(
        comodel_name="res.country.state", string="State", required=True
    )

    federal_taxes_national = fields.Float(
        string="Impostos Federais Nacional",
        digits="Fiscal Tax Percent",
    )

    federal_taxes_import = fields.Float(
        string="Impostos Federais Importado",
        digits="Fiscal Tax Percent",
    )

    state_taxes = fields.Float(
        string="Impostos Estaduais Nacional",
        digits="Fiscal Tax Percent",
    )

    municipal_taxes = fields.Float(
        string="Impostos Municipais Nacional",
        digits="Fiscal Tax Percent",
    )

    create_date = fields.Datetime(readonly=True)

    key = fields.Char(size=32)

    origin = fields.Char(string="Source", size=32)

    active = fields.Boolean(string="Ativo", default=True)

    def _deactivate_old_estimates(self):
        for estimate in self:
            domain = [
                ("id", "!=", estimate.id),
                ("state_id", "=", estimate.state_id.id),
                "|",
                ("ncm_id", "=", estimate.ncm_id.id),
                ("nbs_id", "=", estimate.nbs_id.id),
            ]
            old_estimates = self.search(domain)
            old_estimates.write({"active": False})

    @api.model_create_multi
    def create(self, vals_list):
        estimates = super().create(vals_list)
        estimates._deactivate_old_estimates()
        return estimates
