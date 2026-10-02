# Copyright 2023 KMEE INFORMATICA LTDA
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeRelated(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.related"
    _inherit = [
        "l10n_br_fiscal.document.related",
        "cte.40.tcte_infdoc",
        "cte.40.tcte_infctecomp",
    ]

    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    )
    _cte40_stacking_mixin = "cte.40.tcte_infdoc"

    # InfNFe
    cte40_chave = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_chave",
    )

    cte40_tpDoc = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_tpDoc",
    )

    # infOutros

    cte40_descOutros = fields.Char(string="Descrição do documento")

    cte40_nDoc = fields.Char(string="Número", default="123123")

    cte40_dEmi = fields.Date(
        string="Data de Emissão",
        help="Data de Emissão\nFormato AAAA-MM-DD",
    )

    cte40_vDocFisc = fields.Monetary(
        string="Valor do documento",
        default=1000.0,
        currency_field="brl_currency_id",
    )

    cte40_dPrev = fields.Date(
        string="Data prevista de entrega",
        help="Data prevista de entrega\nFormato AAAA-MM-DD",
    )

    cte40_infDoc = fields.Selection(
        related="cte40_choice_infNF_infNFE_infOutros", string="infDoc"
    )

    # infCteNorm
    cte40_chCTe = fields.Char(compute="_compute_chCte", string="chCte")

    ##########################
    # CT-e tag: infCTeComp
    # Compute Methods
    ##########################

    def _compute_chCTe(self):
        records = ""
        for rec in self:
            if rec.cte40_Id:
                records += rec.document_key
        self.cte40_chCTe = records

    cte40_choice_infNF_infNFE_infOutros = fields.Selection(
        selection=[
            ("cte40_infNF", "infNF"),  # TODO
            ("cte40_infNFe", "infNFe"),
            ("cte40_infOutros", "Outros"),
        ],
        compute="_compute_cte_data",
        inverse="_inverse_cte40_choice_infNF_infNFE_infOutros",
        string="CHOICE",
    )

    @api.depends("document_type_id")
    def _compute_cte_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.document_type_id:
                if rec.document_type_id.code in ("55",):
                    rec.cte40_choice_infNF_infNFE_infOutros = "cte40_infNFe"
                    rec.cte40_chave = rec.document_key
                elif rec.document_type_id.code in ("00", "10", "59", "65", "99"):
                    rec.cte40_choice_infNF_infNFE_infOutros = "cte40_infOutros"
                    rec.cte40_tpDoc = rec.document_type_id.code

    def _inverse_cte40_chave(self):
        for rec in self:
            if rec.cte40_chave:
                rec.document_key = rec.cte40_chave

    def _inverse_cte40_tpDoc(self):
        for rec in self:
            if rec.cte40_tpDoc:
                rec.document_type_id = rec.cte40_tpDoc

    def _inverse_cte40_choice_infNF_infNFE_infOutros(self):
        for rec in self:
            if rec.cte40_choice_infNF_infNFE_infOutros == "cte40_infNFe":
                rec.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
            if rec.cte40_choice_infNF_infNFE_infOutros == "infOutros":
                rec.document_type_id = self.env.ref("l10n_br_fiscal.document_01")
