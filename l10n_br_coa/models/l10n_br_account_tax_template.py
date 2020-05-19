# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nBrAccountTaxTemplate(models.Model):
    _name = 'l10n_br_account.tax.template'
    _inherit = 'account.tax.template'

    chart_template_id = fields.Many2one(required=False)

    def create_account_tax_templates(self, chart_template_id):
        self.ensure_one()
        chart = self.env['account.chart.template'].browse(chart_template_id)
        module = chart.get_external_id()[chart_template_id].split('.')[0]
        xmlid = '.'.join(
            [module, self.get_external_id()[self.id].split('.')[1]])
        tax_template_data = self.copy_data()[0]
        tax_template_data.update({'chart_template_id': chart_template_id})
        data = dict(xml_id=xmlid, values=tax_template_data, noupdate=True)
        self.env['account.tax.template']._load_records([data])
