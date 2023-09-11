# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeModalFerroviario(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.ferroviario"
    _inherit = "mdfe.30.ferrov"

    mdfe30_trem = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.ferroviario.trem", required=True
    )

    mdfe30_vag = fields.One2many(comodel_name="l10n_br_mdfe.modal.ferroviario.vagao")


class MDFeModalFerroviarioTrem(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.ferroviario.trem"
    _inherit = "mdfe.30.trem"

    mdfe30_xPref = fields.Char(required=True)

    mdfe30_xOri = fields.Char(required=True)

    mdfe30_xDest = fields.Char(required=True)

    mdfe30_qVag = fields.Char(required=True)


class MDFeModalFerroviarioVagao(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.ferroviario.vagao"
    _inherit = "mdfe.30.vag"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_pesoBC = fields.Float(required=True)

    mdfe30_pesoR = fields.Float(required=True)

    mdfe30_serie = fields.Char(required=True)

    mdfe30_nVag = fields.Char(required=True)

    mdfe30_TU = fields.Char(required=True)

    @api.model
    def export_fields(self):
        return {
            "pesoBC": self.mdfe30_pesoBC,
            "pesoR": self.mdfe30_pesoR,
            "tpVag": self.mdfe30_tpVag,
            "serie": self.mdfe30_serie,
            "nVag": self.mdfe30_nVag,
            "nSeq": self.mdfe30_nSeq,
            "TU": self.mdfe30_TU,
        }
