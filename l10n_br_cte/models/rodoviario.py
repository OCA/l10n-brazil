# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.cte.bindings.v4_0.cte_modal_rodoviario_v4_00 import Rodo

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class Rodoviario(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.rodoviario"
    _inherit = "cte.40.rodo"

    cte40_RNTRC = fields.Char(
        string="RNTRC",
        store=True,
        help="Registro Nacional de Transportadores Rodoviários de Carga",
    )

    cte40_occ = fields.One2many(
        comodel_name="l10n_br_cte.modal.rodoviario.occ",
        string="Ordens de Coleta associados",
    )


class Occ(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.rodoviario.occ"
    _inherit = "cte.40.occ"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_serie = fields.Char(string="Série da OCC")

    cte40_nOcc = fields.Char(string="Número da Ordem de coleta")

    cte40_dEmi = fields.Date(
        string="Data de emissão da ordem de coleta",
        help="Data de emissão da ordem de coleta\nFormato AAAA-MM-DD",
    )

    cte40_emiOcc = fields.Many2one(comodel_name="res.partner", string="emiOcc")

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Rodo.Occ(
            serie=self.cte40_serie,
            nOcc=self.cte40_nOcc,
            dEmi=self.cte40_dEmi,
            emiOcc=self.cte40_emiOcc,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class EmiOcc(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.rodoviario.occ.emiocc"
    _inherit = "cte.40.emiocc"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Ferrovias Envolvidas",
    )

    cte40_cInt = fields.Char(
        string="Código interno da Ferrovia envolvida",
        help="Código interno da Ferrovia envolvida\nUso da transportadora",
    )

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Rodo.Occ.EmiOcc(
            CNPJ=self.partner_id.cte40_CNPJ,
            IE=self.partner_id.cte40_IE,
            xNome=self.partner_id.cte40_xNome,
            cInt=self.cte40_cInt,
            UF=self.partner_id.cte40_UF,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]
