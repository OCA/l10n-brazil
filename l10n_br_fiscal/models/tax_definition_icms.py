# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TaxDefinitionICMS(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    icms_regulation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.regulation",
        string="ICMS Regulation")

    state_from_id = fields.Many2one(
        comodel_name='res.country.state',
        string='From State',
        domain=[('country_id.code', '=', 'BR')])

    state_to_id = fields.Many2one(
        comodel_name='res.country.state',
        string='To State',
        domain=[('country_id.code', '=', 'BR')])

    @api.multi
    @api.constrains("icms_regulation_id", "state_from_id")
    def _check_icms(self):
        for record in self:
            if record.icms_regulation_id:
                domain = [
                    ("id", "!=", record.id),
                    ('icms_regulation_id', '=', record.company_id.id),
                    ('state_from_id', '=', record.state_from_id.id),
                    ('tax_group_id', '=', record.tax_group_id.id)]

                if record.env["l10n_br_fiscal.tax.definition"].search(domain):
                    raise ValidationError(_(
                        "Tax Definition already exists "
                        "for this ICMS and Tax Group !"))
