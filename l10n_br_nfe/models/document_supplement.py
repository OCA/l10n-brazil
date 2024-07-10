# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class NFeSupplement(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.supplement"
    _inherit = ["l10n_br_fiscal.document.supplement", "nfe.40.infnfesupl"]
    _description = "NFe Supplement Document"
    _stacked = "nfe.40.infnfesupl"
    _binding_module = "nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00"
    _field_prefix = "nfe40_"
    _schema_name = "nfe"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_nfe"
    _spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
    _spec_tab_name = "NFe"

    nfe40_qrCode = fields.Char(related="qrcode")

    nfe40_urlChave = fields.Char(related="url_key")
