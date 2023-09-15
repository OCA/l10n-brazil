# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeTranporte(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte"
    _inherit = "mdfe.30.infmdfetransp"

    mdfe30_chMDFe = fields.Char(required=True)

    mdfe30_infUnidTransp = fields.One2many(comodel_name="l10n_br_mdfe.transporte.inf")

    mdfe30_peri = fields.One2many(comodel_name="l10n_br_mdfe.transporte.perigoso")


class MDFeTranporteInf(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte.inf"
    _inherit = "mdfe.30.tunidadetransp"

    mdfe30_tpUnidTransp = fields.Selection(required=True)

    mdfe30_idUnidTransp = fields.Char(required=True)

    mdfe30_lacUnidTransp = fields.One2many(comodel_name="l10n_br_mdfe.transporte.lacre")

    mdfe30_infUnidCarga = fields.One2many(
        comodel_name="l10n_br_mdfe.transporte.carga.inf"
    )


class MDFeTranporteCargaInf(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte.carga.inf"
    _inherit = "mdfe.30.tunidcarga"

    mdfe30_tpUnidCarga = fields.Selection(required=True)

    mdfe30_idUnidCarga = fields.Char(required=True)

    mdfe30_lacUnidCarga = fields.One2many(comodel_name="l10n_br_mdfe.transporte.lacre")


class MDFeTranportePerigoso(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte.perigoso"
    _inherit = [
        "mdfe.30.infmdfetransp_peri",
        "mdfe.30.infnfe_peri",
        "mdfe.30.infcte_peri",
    ]

    mdfe30_nONU = fields.Char(required=True)

    mdfe30_qTotProd = fields.Char(required=True)


class MDFeLacre(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte.lacre"
    _inherit = ["mdfe.30.lacunidtransp", "mdfe.30.lacunidcarga", "mdfe.30.lacrodo"]

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_nLacre = fields.Char(required=True)

    @api.model
    def export_fields(self, binding):
        if len(self) > 1:
            return self.export_fields_multi()

        return binding(nLacre=self.mdfe30_nLacre)

    @api.model
    def export_fields_multi(self, binding):
        return [record.export_fields(binding) for record in self]
