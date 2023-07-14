# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeRelated(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document.related"
    _inherit = [
        "l10n_br_fiscal.document.related",
        "cte.40.tcte_infnfe",
        "cte.40.tcte_infnf",
        "cte.40.tcte_infq",
    ]
    _stacked = "cte.40.tcte_infnfe"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _spec_tab_name = "CTe"

    # infQ
    cte40_cUnid = fields.Selection(related="cUnid")

    cte40_tpMed = fields.Char()

    cte40_qCarga = fields.Float()

    # View - infQ
    cUnid = fields.Selection(
        selection=[
            ("00", "M3"),
            ("01", "KG"),
            ("02", "TON"),
            ("03", "UNIDADE"),
            ("04", "LITROS"),
            ("05", "MMBTU"),
        ]
    )

    # infCarga One2many pro document line ?
    cte40_prodPred = fields.Char(string="prodPred")

    cte40_vCarga = fields.Monetary(related="price_gross")  # TODO compute

    cte40_infDoc = fields.Selection(related="infDoc")

    # infNF - infNFE
    cte40_mod = fields.Char(related="document_type_id.code", string="cte40_mod")

    cte40_serie = fields.Char(related="document_serie")

    cte40_nDoc = fields.Char(related="document_number")

    cte40_dEmi = fields.Datetime(related="document_date")

    cte40_vBC = fields.Monetary(related="icms_base")

    cte40_vICMS = fields.Monetary(related="amount_icms_value")

    cte40_vBCST = fields.Monetary(related="amount_icmsst_base")

    cte40_vST = fields.Monetary(related="amount_icmsst_value")

    cte40_vProd = fields.Monetary(related="amount_total")

    cte40_vNF = fields.Monetary(related="amount_financial_total")

    cte40_nCFOP = fields.Char(related="cfop_id.code")

    infDoc = fields.Selection(
        selection=[
            ("cte40_infNF", "NF"),
            ("cte40_infNFe", "NFe"),
            ("cte40_infOutros", "Outros"),
        ]
    )

    def _compute_vCarga(self):
        # TODO
        pass
