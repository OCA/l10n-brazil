# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class NFeSupplement(spec_models.SpecModel):
    _name = "l10n_br_fiscal.document.supplement"
    _inherit = ["l10n_br_fiscal.document.supplement", "nfe.40.infnfesupl"]
    _nfe40_binding_type = "Tnfe.InfNfeSupl"  # avoid ambiguity with CTe and MDFe modules

    nfe40_qrCode = fields.Char(related="qrcode")
    nfe40_urlChave = fields.Char(related="url_key")
