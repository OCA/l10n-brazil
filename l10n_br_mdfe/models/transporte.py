# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeTranporte(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte"
    _inherit = "mdfe.30.infmdfetransp"
    _description = "Transporte MDFe"

    mdfe30_chMDFe = fields.Char(required=True)

    mdfe30_infUnidTransp = fields.One2many(comodel_name="l10n_br_mdfe.transporte.inf")

    mdfe30_peri = fields.One2many(comodel_name="l10n_br_mdfe.transporte.perigoso")


class MDFeTranporteInf(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte.inf"
    _inherit = "mdfe.30.tunidadetransp"
    _description = "Informações de Transporte MDFe"

    mdfe30_tpUnidTransp = fields.Selection(required=True)

    mdfe30_idUnidTransp = fields.Char(required=True)

    mdfe30_lacUnidTransp = fields.One2many(comodel_name="l10n_br_mdfe.transporte.lacre")

    mdfe30_infUnidCarga = fields.One2many(
        comodel_name="l10n_br_mdfe.transporte.carga.inf"
    )


class MDFeTranporteCargaInf(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte.carga.inf"
    _inherit = "mdfe.30.tunidcarga"
    _description = "Informações de Carga MDFe"

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
    _description = "Transporte Perigoso MDFe"

    mdfe30_nONU = fields.Char(required=True)

    mdfe30_qTotProd = fields.Char(required=True)


class MDFeLacre(spec_models.SpecModel):
    _name = "l10n_br_mdfe.transporte.lacre"
    _inherit = ["mdfe.30.lacunidtransp", "mdfe.30.lacunidcarga"]
    _description = "Lacre MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_nLacre = fields.Char(required=True, size=20)
