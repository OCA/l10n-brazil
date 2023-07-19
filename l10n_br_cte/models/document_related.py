# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

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

    # infCarga
    cte40_prodPred = fields.Char(string="prodPred")

    cte40_vCarga = fields.Monetary(
        currency_field="currency_id", compute="_compute_vCarga", store=True
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id", readonly=True
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )

    # InfNFe
    cte40_chave = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_chave",
    )

    cte40_tpDoc = fields.Char(
        compute="_compute_cte_data",
        inverse="_inverse_cte40_tpDoc",
    )

    cte40_infDoc = fields.Selection(related="cte40_choice254")

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

    cte40_choice254 = fields.Selection(
        selection=[
            ("cte40_infNF", "infNF"),
            ("cte40_infNFe", "infNFe"),
            ("cte40_infOutros", "Outros"),
        ],
        compute="_compute_cte_data",
        inverse="_inverse_cte40_choice254",
    )

    def _compute_vCarga(self):
        for rec in self:
            if rec.document_related_id:
                rec.cte40_vCarga += rec.document_related_id.amount_price_gross

    @api.depends("document_type_id")
    def _compute_cte_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.document_type_id:
                if rec.document_type_id.code in ("55",):
                    rec.cte40_choice254 = "cte40_infNFe"
                    rec.cte40_chave = rec.document_key
                elif rec.document_type_id.code in ("00", "10", "59", "65", "99"):
                    rec.cte40_choice254 = "cte40_infOutros"
                    rec.cte40_tpDoc = rec.document_type_id.code

    def _inverse_cte40_chave(self):
        for rec in self:
            if rec.cte40_chave:
                rec.document_key = rec.cte40_chave

    def _inverse_cte40_tpDoc(self):
        for rec in self:
            if rec.cte40_tpDoc:
                rec.document_type_id = rec.cte40_tpDoc

    def _inverse_cte40_choice254(self):
        for rec in self:
            if rec.cte40_choice254 == "cte40_infNFe":
                rec.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
