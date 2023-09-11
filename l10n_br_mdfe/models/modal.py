# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.modal import (
    MDFE_MODAL_DEFAULT,
    MDFE_MODAL_VERSION_DEFAULT,
    MDFE_MODALS,
)


class MDFeModal(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal"
    _inherit = "mdfe.30.infmodal"
    _mdfe_search_keys = ["mdfe30_versaoModal"]

    mdfe30_versaoModal = fields.Char(
        string="Modal Version", default=MDFE_MODAL_VERSION_DEFAULT
    )

    name = fields.Char(string="Modal Name")

    modal_type = fields.Selection(
        selection=MDFE_MODALS, string="Modal Type", default=MDFE_MODAL_DEFAULT
    )
