# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import api, fields, models


class DocumentLine(models.Model):
    _inherit = 'l10n_br_fiscal.document.line'

    fiscal_deductions_value = fields.Monetary(
        string='Fiscal Deductions',
        default=0.00,
    )
    other_retentions_value = fields.Monetary(
        string='Other Retentions',
        default=0.00,
    )
    city_taxation_code = fields.Char(
        string='City Taxation Code',
    )

    @api.onchange("product_id")
    def _onchange_product_id_fiscal(self):
        super(DocumentLine, self)._onchange_product_id_fiscal()
        if self.product_id and self.product_id.fiscal_deductions_value:
            self.fiscal_deductions_value = \
                self.product_id.fiscal_deductions_value
        if self.product_id and self.product_id.city_taxation_code:
            self.city_taxation_code = self.product_id.city_taxation_code

    def _compute_taxes(self, taxes, cst=None):
        discount_value = self.discount_value
        self.discount_value += self.fiscal_deductions_value
        res = super(DocumentLine, self)._compute_taxes(taxes, cst)
        self.discount_value = discount_value
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type="form",
                        toolbar=False, submenu=False):
        model_view = super(DocumentLine, self).fields_view_get(
            view_id, view_type, toolbar, submenu)

        if view_type == 'form':
            try:
                doc = etree.fromstring(model_view.get('arch'))
                field = doc.xpath("//field[@name='issqn_wh_value']")[0]
                parent = field.getparent()
                parent.insert(parent.index(field)+1, etree.XML(
                    '<field name="other_retentions_value"/>'
                ))

                model_view["arch"] = etree.tostring(doc, encoding='unicode')
            except Exception:
                return model_view
        return model_view
