# Copyright (C) 2023 KMEE - Felipe Zago
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mdfe_version = fields.Selection(
        string="MDF-e Version",
        related="company_id.mdfe_version",
        readonly=False,
    )

    mdfe_environment = fields.Selection(
        string="MDF-e Environment",
        related="company_id.mdfe_environment",
        readonly=False,
    )

    mdfe_transmission = fields.Selection(
        string="MDF-e Transmission",
        related="company_id.mdfe_transmission",
        readonly=False,
    )

    mdfe_version_name = fields.Char(
        string="MDF-e Proc Version",
        config_parameter="l10n_br_mdfe.version.name",
    )
