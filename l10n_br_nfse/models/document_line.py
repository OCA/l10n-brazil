# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from erpbrasil.base import misc
from lxml import etree

from odoo import api, fields, models


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    fiscal_deductions_value = fields.Monetary(
        string="Fiscal Deductions",
        default=0.00,
    )
    other_retentions_value = fields.Monetary(
        string="Other Retentions",
        default=0.00,
    )

    @api.onchange("product_id")
    def _onchange_product_id_fiscal(self):
        super(DocumentLine, self)._onchange_product_id_fiscal()
        if self.product_id and self.product_id.fiscal_deductions_value:
            self.fiscal_deductions_value = self.product_id.fiscal_deductions_value

    def _compute_taxes(self, taxes, cst=None):
        discount_value = self.discount_value
        self.discount_value += self.fiscal_deductions_value
        res = super(DocumentLine, self)._compute_taxes(taxes, cst)
        self.discount_value = discount_value
        return res

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        model_view = super(DocumentLine, self).fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        if view_type == "form":
            try:
                doc = etree.fromstring(model_view.get("arch"))
                field = doc.xpath("//field[@name='issqn_wh_value']")[0]
                parent = field.getparent()
                parent.insert(
                    parent.index(field) + 1,
                    etree.XML('<field name="other_retentions_value"/>'),
                )

                model_view["arch"] = etree.tostring(doc, encoding="unicode")
            except Exception:
                return model_view

        arch_tree = self.inject_fiscal_fields(model_view["arch"])
        View = self.env["ir.ui.view"]
        # Override context for postprocessing
        if view_id and model_view.get("base_model", self._name) != self._name:
            View = View.with_context(base_model_name=model_view["base_model"])

        # Apply post processing, groups and modifiers etc...
        xarch, xfields = View.postprocess_and_fields(node=arch_tree, model=self._name)
        model_view["arch"] = xarch
        model_view["fields"] = xfields
        return model_view

    def prepare_line_servico(self):
        return {
            "valor_servicos": round(self.fiscal_price, 2),
            "valor_deducoes": round(self.fiscal_deductions_value, 2),
            "valor_pis": round(self.pis_value, 2) or round(self.pis_wh_value, 2),
            "valor_pis_retido": round(self.pis_wh_value, 2),
            "valor_cofins": round(self.cofins_value, 2)
            or round(self.cofins_wh_value, 2),
            "valor_cofins_retido": round(self.cofins_wh_value, 2),
            "valor_inss": round(self.inss_value, 2) or round(self.inss_wh_value, 2),
            "valor_inss_retido": round(self.inss_wh_value, 2),
            "valor_ir": round(self.irpj_value, 2) or round(self.irpj_wh_value, 2),
            "valor_ir_retido": round(self.irpj_wh_value, 2),
            "valor_csll": round(self.csll_value, 2) or round(self.csll_wh_value, 2),
            "valor_csll_retido": round(self.csll_wh_value, 2),
            "iss_retido": "1" if self.issqn_wh_value else "2",
            "valor_iss": round(self.issqn_value, 2),
            "valor_iss_retido": round(self.issqn_wh_value, 2),
            "outras_retencoes": round(self.other_retentions_value, 2),
            "base_calculo": round(self.issqn_base, 2) or round(self.issqn_wh_base, 2),
            "aliquota": (self.issqn_percent / 100) or (self.issqn_wh_percent / 100),
            "valor_liquido_nfse": round(self.amount_taxed, 2),
            "item_lista_servico": self.service_type_id.code
            and self.service_type_id.code.replace(".", ""),
            "codigo_tributacao_municipio": self.city_taxation_code_id.code or "",
            "municipio_prestacao_servico": self.issqn_fg_city_id.ibge_code or "",
            "discriminacao": str(self.name[:2000] or ""),
            "codigo_cnae": misc.punctuation_rm(self.cnae_id.code) or None,
            "valor_desconto_incondicionado": round(self.discount_value, 2),
        }
