# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.mdfe import (
    MDFE_EMIT_TYPE_DEFAULT,
    MDFE_EMIT_TYPES,
    MDFE_ENVIRONMENT_DEFAULT,
    MDFE_ENVIRONMENTS,
    MDFE_TRANSMISSION_DEFAULT,
    MDFE_TRANSMISSIONS,
    MDFE_TRANSP_TYPE,
    MDFE_TRANSP_TYPE_DEFAULT,
    MDFE_VERSION_DEFAULT,
    MDFE_VERSIONS,
)


class ResCompany(spec_models.SpecModel):

    _name = "res.company"
    _inherit = [
        "res.company",
        "mdfe.30.emit",
    ]
    _mdfe_search_keys = ["mdfe30_CNPJ", "mdfe30_xNome", "mdfe_xFant"]

    mdfe_version = fields.Selection(
        selection=MDFE_VERSIONS,
        string="MDFe Version",
        default=MDFE_VERSION_DEFAULT,
    )

    mdfe_environment = fields.Selection(
        selection=MDFE_ENVIRONMENTS,
        string="MDFe Environment",
        default=MDFE_ENVIRONMENT_DEFAULT,
    )

    mdfe_emit_type = fields.Selection(
        selection=MDFE_EMIT_TYPES,
        string="MDFe Emit Type",
        default=MDFE_EMIT_TYPE_DEFAULT,
    )

    mdfe_transp_type = fields.Selection(
        selection=MDFE_TRANSP_TYPE,
        string="MDFe Transp Type",
        default=MDFE_TRANSP_TYPE_DEFAULT,
    )

    mdfe_transmission = fields.Selection(
        selection=MDFE_TRANSMISSIONS,
        string="MDFe Transmission",
        copy=False,
        default=MDFE_TRANSMISSION_DEFAULT,
    )

    # TODO
