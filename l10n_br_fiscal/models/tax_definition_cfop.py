# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TaxDefinitionCFOP(models.Model):
    _inherit = 'l10n_br_fiscal.tax.definition'

    cfop_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cfop',
        string='CFOP')

    @api.multi
    @api.constrains('cfop_id')
    def _check_cfop_id(self):
        for record in self:
            if record.cfop_id:
                domain = [
                    ('id', '!=', record.id),
                    ('cfop_id', '=', record.cfop_id.id),
                    ('tax_group_id', '=', record.tax_group_id.id),
                    ('tax_id', '=', record.tax_id.id)]

                if record.env['l10n_br_fiscal.tax.definition'].search_count(
                        domain):
                    raise ValidationError(_(
                        "Tax Definition already exists "
                        "for this CFOP and Tax Group !"))

    @api.onchange('cfop_id')
    def _onchange_cfop_id(self):
        if self.cfop_id:
            self.type_in_out = self.cfop_id.type_in_out
