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
    city_taxation_code_id = fields.Many2one(
        string='City Taxation Code',
        comodel_name='l10n_br_fiscal.city.taxation.code'
    )

    @api.onchange("product_id")
    def _onchange_product_id_fiscal(self):
        super(DocumentLine, self)._onchange_product_id_fiscal()
        if self.product_id and self.product_id.fiscal_deductions_value:
            self.fiscal_deductions_value = \
                self.product_id.fiscal_deductions_value
        if self.product_id and self.product_id.city_taxation_code_id:
            company_city_id = self.document_id.company_id.city_id
            city_id = self.product_id.city_taxation_code_id.filtered(
                lambda r: r.city_id == company_city_id)
            if city_id:
                self.city_taxation_code_id = city_id

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

    def prepare_line_servico(self):
        return {
            'valor_servicos': float(self.fiscal_price),
            'valor_deducoes': float(self.fiscal_deductions_value),
            'valor_pis': float(self.pis_value),
            'valor_cofins': float(self.cofins_value),
            'valor_inss': float(self.inss_value),
            'valor_ir': float(self.irpj_value),
            'valor_csll': float(self.csll_value),
            'iss_retido': '1' if self.issqn_wh_value else '2',
            'valor_iss': float(self.issqn_value),
            'valor_iss_retido': float(self.issqn_wh_value),
            'outras_retencoes': float(self.other_retentions_value),
            'base_calculo': float(self.issqn_base),
            'aliquota': float(self.issqn_percent / 100),
            'valor_liquido_nfse': float(self.amount_total),
            'item_lista_servico':
                self.service_type_id.code and
                self.service_type_id.code.replace('.', ''),
            'codigo_tributacao_municipio':
                self.city_taxation_code_id.code,
            'discriminacao': str(self.name[:120] or ''),
        }
