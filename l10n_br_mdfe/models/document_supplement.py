# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeSupplement(spec_models.SpecModel):
    _name = "l10n_br_fiscal.document.supplement"
    _inherit = ["l10n_br_fiscal.document.supplement", "mdfe.30.infmdfesupl"]
    _mdfe30_binding_type = "Tmdfe.InfMdfeSupl"  # avoid ambiguity with NFe and CTe

    mdfe30_qrCodMDFe = fields.Char(related="qrcode")
