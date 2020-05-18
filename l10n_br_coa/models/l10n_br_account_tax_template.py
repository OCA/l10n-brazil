# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nBrAccountTaxTemplate(models.Model):
    _name = 'l10n_br_account.tax.template'
    _inherit = 'account.tax.template'

    chart_template_id = fields.Many2one(required=False)

    def create_account_tax_templates(self, chart_template_id):
        self.ensure_one()
        account_tax_template_data = {'chart_template_id': chart_template_id}
        account_tax_template_data.update({
            field: self[field]
            for field in self._fields if self[field] is not False})
        self.env['account.tax.template'].create(account_tax_template_data)
