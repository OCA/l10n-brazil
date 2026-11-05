# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from erpbrasil.base import misc
from lxml import etree

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    fiscal_deductions_value = fields.Monetary(
        string="Fiscal Deductions",
        default=0.0,
        compute="_compute_fiscal_deductions_value",
        store=True,
        readonly=False,
        precompute=True,
    )
    other_retentions_value = fields.Monetary(
        string="Other Retentions",
        default=0.0,
    )

    @api.depends("product_id", "product_id.fiscal_deductions_value")
    def _compute_fiscal_deductions_value(self):
        for line in self:
            if line.product_id and line.product_id.fiscal_deductions_value:
                line.fiscal_deductions_value = line.product_id.fiscal_deductions_value

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        # ``other_retentions_value`` has no placeholder of its own: it is meant
        # to be shown right after ``issqn_wh_value``, a field that only exists
        # in the line form through the fiscal fields injection (fiscal_taxes
        # page, see l10n_br_fiscal.document.line.mixin.inject_fiscal_fields,
        # already applied by super()._get_view here). We add it on the modern
        # ``_get_view`` flow.
        #
        # This used to live in a ``fields_view_get`` override, which the 16.0
        # web client never calls (get_views -> get_view -> _get_view): the
        # field had silently vanished from the NFS-e line form, and a bare
        # ``except Exception`` hid a missing anchor as a no-op. We now fail
        # loudly (diagnosable log) instead of swallowing the regression.
        if view_type == "form":
            anchors = arch.xpath("//field[@name='issqn_wh_value']")
            if anchors:
                anchors[0].addnext(
                    etree.fromstring('<field name="other_retentions_value"/>')
                )
            else:
                _logger.warning(
                    "l10n_br_nfse: cannot place 'other_retentions_value' on the "
                    "%s form view: the anchor field 'issqn_wh_value' is missing "
                    "from the injected fiscal line arch (fiscal_taxes page). The "
                    "field will not be shown on the NFS-e line form. Keep "
                    "'issqn_wh_value' in the injected line form.",
                    self._name,
                )
        return arch, view

    def _prepare_line_service(self, rate=1.0):
        """Return the service values of the line, in the company currency.

        :param rate: multiplier from the invoice currency to the company
            currency (1.0 when both are the same). Monetary values are
            multiplied before rounding, so the rounding is done once, in the
            currency the NFS-e is issued in. The ISS amounts are recomputed
            from the converted base, instead of converting the ISS computed
            in the invoice currency, so that base x rate always matches the
            amount the city hall validates.
        """

        def conv(value):
            return round((value or 0.0) * rate, 2)

        vals = {
            "valor_servicos": conv(self.price_gross),
            "valor_deducoes": conv(self.fiscal_deductions_value),
            "valor_pis": conv(self.pis_value) or conv(self.pis_wh_value),
            "valor_pis_retido": conv(self.pis_wh_value),
            "valor_cofins": conv(self.cofins_value) or conv(self.cofins_wh_value),
            "valor_cofins_retido": conv(self.cofins_wh_value),
            "valor_inss": conv(self.inss_value) or conv(self.inss_wh_value),
            "valor_inss_retido": conv(self.inss_wh_value),
            "valor_ir": conv(self.irpj_value) or conv(self.irpj_wh_value),
            "valor_ir_retido": conv(self.irpj_wh_value),
            "valor_csll": conv(self.csll_value) or conv(self.csll_wh_value),
            "valor_csll_retido": conv(self.csll_wh_value),
            "iss_retido": "1" if self.issqn_wh_percent else "2",
            "valor_iss": conv(self.issqn_value),
            "valor_iss_retido": conv(self.issqn_wh_value),
            "outras_retencoes": conv(self.other_retentions_value),
            "base_calculo": conv(self.issqn_base) or conv(self.issqn_wh_base),
            "aliquota": (self.issqn_percent / 100) or (self.issqn_wh_percent / 100),
            "valor_liquido_nfse": conv(self.amount_taxed),
            "item_lista_servico": self.service_type_id.code
            and self.service_type_id.code.replace(".", ""),
            "codigo_tributacao_nacional": self.national_taxation_code_id.code or None,
            "codigo_tributacao_municipio": self.city_taxation_code_id.code or None,
            "municipio_prestacao_servico": self.issqn_fg_city_id.ibge_code or "",
            "discriminacao": str(self.name[:2000] or ""),
            "codigo_cnae": misc.punctuation_rm(self.cnae_id.code) or None,
            "codigo_nbs": self.nbs_id.code or "",
            "codigo_nbs_unmasked": self.nbs_id.code_unmasked or "",
            "codigo_indicador_operacao": self.operation_indicator_id.code or "",
            "ibs_cbs_classificacao_tributaria": self.tax_classification_id.code
            or "000000",
            "ibs_cbs_situacao_tributaria": self.ibs_cst_code or "000",
            "ibs_cbs_base_calculo": conv(self.issqn_base),
            "valor_desconto_incondicionado": conv(self.discount_value),
            "ibs_uf_aliquota": round(self.ibs_percent, 2) if self.ibs_percent else None,
            "ibs_mun_aliquota": 0.0,
            "cbs_aliquota": round(self.cbs_percent, 2) if self.cbs_percent else None,
            "ibs_uf_valor": conv(self.ibs_value) if self.ibs_value else None,
            "ibs_mun_valor": 0.0,
            "cbs_valor": conv(self.cbs_value) if self.cbs_value else None,
            "situacao_tributaria_pis": self.pis_cst_code or "",
            "situacao_tributaria_cofins": self.cofins_cst_code or "",
            "base_calculo_pis": conv(self.pis_base),
            "base_calculo_cofins": conv(self.cofins_base),
            "aliquota_pis": round(self.pis_percent, 2) if self.pis_percent else 0.0,
            "aliquota_cofins": (
                round(self.cofins_percent, 2) if self.cofins_percent else 0.0
            ),
            "tipo_retencao_pis_cofins": (
                "1" if (self.pis_wh_value or self.cofins_wh_value) else "2"
            ),
        }
        if rate != 1.0:
            base = vals["base_calculo"]
            if self.issqn_value:
                vals["valor_iss"] = round(base * self.issqn_percent / 100, 2)
            if self.issqn_wh_value:
                vals["valor_iss_retido"] = round(base * self.issqn_wh_percent / 100, 2)
        return vals
