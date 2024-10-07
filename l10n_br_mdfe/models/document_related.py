# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeRelated(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.related"
    _inherit = [
        "l10n_br_fiscal.document.related",
        "mdfe.30.infmdfetransp",
        "mdfe.30.tmdfe_infnfe",
        "mdfe.30.infcte",
    ]
    _mdfe30_odoo_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
    )
    _mdfe30_stacking_mixin = "mdfe.30.tmdfe_infnfe"

    mdfe30_chNFe = fields.Char(related="document_key")

    mdfe30_chCTe = fields.Char(related="document_key")

    mdfe30_chMDFe = fields.Char(related="document_key")

    mdfe30_peri = fields.One2many(comodel_name="l10n_br_mdfe.transporte.perigoso")

    mdfe30_infUnidTransp = fields.One2many(comodel_name="l10n_br_mdfe.transporte.inf")
